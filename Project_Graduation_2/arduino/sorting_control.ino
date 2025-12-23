/*
 * Coca-Cola Sorting System - Arduino Controller (DUAL SENSOR MODE)
 * Hardware: Arduino Uno
 * Components: 
 *   - IR Sensor 1 (Pin 2): Detects bottle at start → triggers AI
 *   - IR Sensor 2 (Pin 3): Detects bottle near servo → triggers kick if NG
 *   - Relay Module (Pin 4): Conveyor control
 *   - Servo Motor MG996R (Pin 9): Linear actuator for rejection
 * 
 * WORKFLOW (Dual Sensor - No TRAVEL_TIME needed):
 * 1. Conveyor ALWAYS runs (Relay = LOW)
 * 2. Sensor 1 detects bottle → Send 'D' to Pi → Add to queue as "pending"
 * 3. Pi responds with 'O' (OK) or 'N' (NG) → Mark bottle in queue
 * 4. Sensor 2 detects bottle → Check queue:
 *    - If NG pending → Kick immediately
 *    - If OK → Let pass
 * 
 * ADVANTAGE: No need to calibrate TRAVEL_TIME, works with any conveyor speed
 */

#include <Servo.h>

// ============================================================================
// CONFIGURATION (Adjust these values for your physical setup)
// ============================================================================

// Pin Definitions
const int SENSOR_1_PIN = 2;     // IR Sensor 1 (Start position - triggers AI)
const int SENSOR_2_PIN = 3;     // IR Sensor 2 (Near servo - triggers kick)
const int RELAY_PIN = 4;        // Relay Control (LOW = Run, HIGH = Stop)
const int SERVO_PIN = 9;        // Servo Motor MG996R for rejection

// Servo Configuration (MG996R optimized)
const int SERVO_IDLE = 0;         // Idle position (rack retracted, no blocking)
const int SERVO_KICK = 90;        // Kick position (rack extended, blocking conveyor)
                                  // MG996R: 0-180°, adjust based on rack travel distance
const int SERVO_KICK_DURATION = 2000;  // How long servo stays extended (ms)
                                       // Keeps rack blocking for 2 seconds so bottle falls by inertia

// Circular Buffer Configuration
const int BUFFER_SIZE = 20;       // Max bottles that can be tracked simultaneously
                                  // Allows multiple bottles in processing zone

// Sensor Debouncing
const int DEBOUNCE_DELAY = 300;   // Minimum time between detections (ms)
                                  // Prevents double-counting same bottle

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

Servo rejectServo;

// Queue for pending rejections (true = NG pending, false = OK or empty)
bool pendingRejections[BUFFER_SIZE];
bool hasDecision[BUFFER_SIZE];  // Track if Pi has sent decision for this bottle
unsigned long bottleTimestamp[BUFFER_SIZE];  // When bottle was detected at Sensor 1
int queueHead = 0;  // Index to read from (oldest bottle at Sensor 2)
int queueTail = 0;  // Index to write to (newest bottle at Sensor 1)
int queueCount = 0; // Number of items in queue
int decisionIndex = 0; // Index of next bottle waiting for Pi's decision

// Decision timeout
const unsigned long DECISION_TIMEOUT = 1000;  // Max 1 second to wait for Pi's decision

// Sensor 1 State (Start position)
bool lastSensor1State = HIGH;
unsigned long lastSensor1Time = 0;

// Sensor 2 State (Near servo)
bool lastSensor2State = HIGH;
unsigned long lastSensor2Time = 0;

// Statistics
unsigned long totalDetections = 0;
unsigned long totalRejections = 0;
unsigned long totalPassed = 0;

// ============================================================================
// SETUP
// ============================================================================

void setup() {
  // Initialize Serial Communication
  Serial.begin(9600);
  
  // Configure Pins
  pinMode(SENSOR_1_PIN, INPUT);
  pinMode(SENSOR_2_PIN, INPUT);
  pinMode(RELAY_PIN, OUTPUT);
  
  // Initialize Servo MG996R
  rejectServo.attach(SERVO_PIN);
  rejectServo.write(SERVO_IDLE);
  
  // Conveyor ALWAYS runs in continuous mode
  digitalWrite(RELAY_PIN, LOW);
  
  // Initialize queue (all false = no pending rejections)
  for (int i = 0; i < BUFFER_SIZE; i++) {
    pendingRejections[i] = false;
    hasDecision[i] = false;
    bottleTimestamp[i] = 0;
  }
  decisionIndex = 0;
  
  // Startup Message
  Serial.println("========================================");
  Serial.println("Coca-Cola Sorting System - DUAL SENSOR MODE");
  Serial.println("========================================");
  Serial.println("Servo: MG996R Linear Actuator");
  Serial.println("Sensor 1 (Pin 2): Start position - triggers AI");
  Serial.println("Sensor 2 (Pin 3): Near servo - triggers kick");
  Serial.print("Servo Kick Angle: ");
  Serial.println(SERVO_KICK);
  Serial.print("Kick Duration: ");
  Serial.print(SERVO_KICK_DURATION);
  Serial.println(" ms");
  Serial.print("Buffer Size: ");
  Serial.println(BUFFER_SIZE);
  Serial.println("Conveyor Running (Continuous)...");
  Serial.println("Ready for operation.");
  Serial.println();
}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {
  // 1. Check Sensor 1 (Start position) for bottle detection
  checkSensor1();
  
  // 2. Check Sensor 2 (Near servo) for kick trigger
  checkSensor2();
  
  // 3. Check Serial for Pi's decision ('O' or 'N')
  checkSerial();
  
  // Small delay to prevent CPU overload
  delay(10);
}

// ============================================================================
// SENSOR 1 DETECTION (Start Position - Triggers AI)
// ============================================================================

void checkSensor1() {
  bool currentState = digitalRead(SENSOR_1_PIN);
  unsigned long currentTime = millis();
  
  // Detect falling edge (HIGH -> LOW) with debouncing
  if (lastSensor1State == HIGH && currentState == LOW) {
    if (currentTime - lastSensor1Time > DEBOUNCE_DELAY) {
      handleBottleDetection(currentTime);
      lastSensor1Time = currentTime;
    }
  }
  
  lastSensor1State = currentState;
}

void handleBottleDetection(unsigned long detectionTime) {
  totalDetections++;
  
  // Add new entry to queue (initially OK, will be updated when Pi responds)
  if (queueCount < BUFFER_SIZE) {
    int currentIndex = queueTail;
    pendingRejections[currentIndex] = false;  // Default: OK (no rejection)
    hasDecision[currentIndex] = false;  // No decision yet
    bottleTimestamp[currentIndex] = detectionTime;  // Record timestamp
    
    queueTail = (queueTail + 1) % BUFFER_SIZE;
    queueCount++;
    
    Serial.print("[Sensor 1] Bottle at index ");
    Serial.print(currentIndex);
    Serial.print(" detected → AI triggered | Queue: ");
    Serial.println(queueCount);
  } else {
    Serial.println("[ERROR] Queue full! Cannot track bottle.");
  }
  
  // Send detection signal to Raspberry Pi
  Serial.print('D');
  Serial.print(',');
  Serial.println(detectionTime);
  
  // Debug output
  if (totalDetections % 10 == 0) {
    printStatistics();
  }
}

// ============================================================================
// SENSOR 2 DETECTION (Near Servo - Triggers Kick)
// ============================================================================

void checkSensor2() {
  bool currentState = digitalRead(SENSOR_2_PIN);
  unsigned long currentTime = millis();
  
  // Detect falling edge (HIGH -> LOW) with debouncing
  if (lastSensor2State == HIGH && currentState == LOW) {
    if (currentTime - lastSensor2Time > DEBOUNCE_DELAY) {
      handleServoSensorDetection();
      lastSensor2Time = currentTime;
    }
  }
  
  lastSensor2State = currentState;
}

void handleServoSensorDetection() {
  // Check if there's a bottle in queue
  if (queueCount > 0) {
    Serial.print("[Sensor 2] Bottle at index ");
    Serial.print(queueHead);
    Serial.print(" detected → ");
    
    // CRITICAL: Wait for Pi's decision if not received yet
    if (!hasDecision[queueHead]) {
      Serial.println("Waiting for Pi decision...");
      
      unsigned long waitStart = millis();
      bool gotDecision = false;
      
      // Wait up to DECISION_TIMEOUT for Pi's response
      while (millis() - waitStart < DECISION_TIMEOUT) {
        // Check serial for Pi's decision
        checkSerial();
        
        // Check if decision arrived
        if (hasDecision[queueHead]) {
          gotDecision = true;
          Serial.print("  Decision received! → ");
          break;
        }
        
        delay(10);  // Small delay to prevent CPU overload
      }
      
      // If timeout, assume OK (let pass)
      if (!gotDecision) {
        Serial.print("  [TIMEOUT] No decision from Pi → DEFAULT: ");
        pendingRejections[queueHead] = false;  // Assume OK
        hasDecision[queueHead] = true;  // Mark as decided
      }
    }
    
    // Now process the bottle based on decision
    if (pendingRejections[queueHead]) {
      // NG bottle → Kick it!
      Serial.println("NG → KICKING!");
      executeKick();
    } else {
      // OK bottle → Let it pass
      totalPassed++;
      Serial.println("OK → PASSING");
    }
    
    // Remove from queue
    pendingRejections[queueHead] = false;
    hasDecision[queueHead] = false;
    bottleTimestamp[queueHead] = 0;
    queueHead = (queueHead + 1) % BUFFER_SIZE;
    queueCount--;
  } else {
    // Queue empty but sensor 2 triggered (shouldn't happen normally)
    Serial.println("[WARNING] Sensor 2 triggered but queue empty");
  }
}

// ============================================================================
// SERIAL COMMUNICATION (Receive Pi's Decision)
// ============================================================================

void checkSerial() {
  if (Serial.available() > 0) {
    char decision = Serial.read();
    
    if (decision == 'O') {
      // OK product - bottle at decisionIndex stays false (OK)
      if (decisionIndex != queueTail) {
        pendingRejections[decisionIndex] = false;  // Mark as OK
        hasDecision[decisionIndex] = true;  // Decision received!
        
        Serial.print("[Pi Decision] OK → Bottle at index ");
        Serial.print(decisionIndex);
        Serial.println(" will pass");
        
        // Move to next bottle waiting for decision
        decisionIndex = (decisionIndex + 1) % BUFFER_SIZE;
      } else {
        Serial.println("[WARNING] Received OK but no bottle waiting for decision");
      }
    } 
    else if (decision == 'N') {
      // NG product - mark bottle at decisionIndex as pending rejection
      markAsRejection();
    }
  }
}

void markAsRejection() {
  // Mark the bottle at decisionIndex (next in line waiting for decision)
  if (decisionIndex != queueTail) {
    pendingRejections[decisionIndex] = true;  // Mark as NG
    hasDecision[decisionIndex] = true;  // Decision received!
    totalRejections++;
    
    Serial.print("[Pi Decision] NG → Bottle at index ");
    Serial.print(decisionIndex);
    Serial.print(" marked for rejection | Queue: ");
    Serial.println(queueCount);
    
    // Move to next bottle waiting for decision
    decisionIndex = (decisionIndex + 1) % BUFFER_SIZE;
  } else {
    Serial.println("[WARNING] Received NG but no bottle waiting for decision");
  }
}

// ============================================================================
// KICK EXECUTION
// ============================================================================

void executeKick() {
  // MG996R Linear Actuator: Extend rack to block bottle
  rejectServo.write(SERVO_KICK);
  delay(SERVO_KICK_DURATION);
  rejectServo.write(SERVO_IDLE);
  
  // Note: Using delay() here is acceptable because:
  // 1. Conveyor keeps running (relay stays LOW)
  // 2. Rack blocks bottle for SERVO_KICK_DURATION, bottle falls by inertia
  // 3. Other bottles wait in queue and will be processed when servo returns
  
  Serial.print("[Servo] Kick executed | Queue remaining: ");
  Serial.println(queueCount);
}

// ============================================================================
// STATISTICS & DEBUGGING
// ============================================================================

void printStatistics() {
  Serial.println("========== STATISTICS ==========");
  Serial.print("Total Detections (Sensor 1): ");
  Serial.println(totalDetections);
  Serial.print("Total Passed (OK):           ");
  Serial.println(totalPassed);
  Serial.print("Total Rejected (NG):         ");
  Serial.println(totalRejections);
  
  if (totalDetections > 0) {
    float passRate = 100.0 * totalPassed / totalDetections;
    float rejectRate = 100.0 * totalRejections / totalDetections;
    Serial.print("Pass Rate:                   ");
    Serial.print(passRate, 1);
    Serial.println("%");
    Serial.print("Reject Rate:                 ");
    Serial.print(rejectRate, 1);
    Serial.println("%");
  }
  
  Serial.print("Current Queue Size:          ");
  Serial.println(queueCount);
  Serial.println("================================");
}

// ============================================================================
// CALIBRATION HELPER (Call via Serial command 'C')
// ============================================================================

// Optional: Add calibration mode
// Send 'C' from Pi to enter calibration mode
// Arduino will print sensor state continuously for physical measurement
