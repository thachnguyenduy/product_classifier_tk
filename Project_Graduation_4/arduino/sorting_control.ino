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
const int SERVO_KICK = 180;        // Kick position (rack extended, blocking conveyor)
                                  // MG996R: 0-180°, adjust based on rack travel distance
const int SERVO_KICK_DURATION = 2000;  // How long servo stays extended (ms)
                                       // Keeps rack blocking for 2 seconds so bottle falls by inertia

// Circular Buffer Configuration
const int BUFFER_SIZE = 20;       // Max bottles that can be tracked simultaneously
                                  // Allows multiple bottles in processing zone

// Sensor Debouncing / Lockout
// NOTE:
// - Sensor 1 can "blink" multiple times for 1 bottle due to reflections/noise.
//   We add a longer lockout + re-arm (must return HIGH stable) to avoid double-trigger.
// - Sensor 2 should stay responsive, so keep a shorter debounce.
const int SENSOR1_LOCKOUT_MS = 800;   // Minimum time between IR1 detections (ms)
const int SENSOR1_REARM_HIGH_MS = 150; // IR1 must stay HIGH this long to re-arm (ms)
const int SENSOR2_DEBOUNCE_MS = 300;  // Minimum time between IR2 detections (ms)

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

Servo rejectServo;

// Queue for pending rejections (true = NG pending, false = OK or empty)
bool pendingRejections[BUFFER_SIZE];
int queueHead = 0;  // Index to read from (oldest bottle at Sensor 2)
int queueTail = 0;  // Index to write to (newest bottle at Sensor 1)
int queueCount = 0; // Number of items in queue
int decisionIndex = 0; // Index of next bottle waiting for Pi's decision

// Sensor 1 State (Start position)
bool lastSensor1State = HIGH;
unsigned long lastSensor1Time = 0;
bool sensor1Armed = true;
unsigned long sensor1HighSince = 0;

// Sensor 2 State (Near servo)
bool lastSensor2State = HIGH;
unsigned long lastSensor2Time = 0;

// Statistics
unsigned long totalDetections = 0;
unsigned long totalRejections = 0;
unsigned long totalPassed = 0;

// System State
bool conveyorRunning = false;  // Conveyor state (controlled by Pi)

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
  
  // Conveyor starts STOPPED (wait for 'S' command from Pi)
  digitalWrite(RELAY_PIN, HIGH);  // HIGH = Stop
  conveyorRunning = false;
  
  // Initialize queue (all false = no pending rejections)
  for (int i = 0; i < BUFFER_SIZE; i++) {
    pendingRejections[i] = false;
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
  Serial.println("Conveyor: STOPPED (waiting for START command)");
  Serial.println("Ready. Send 'S' to start, 'P' to pause.");
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
  // Only check sensor if conveyor is running
  if (!conveyorRunning) {
    return;
  }
  
  bool currentState = digitalRead(SENSOR_1_PIN);
  unsigned long currentTime = millis();
  
  // Re-arm logic: after a detection, IR1 must return to HIGH and stay stable
  // for SENSOR1_REARM_HIGH_MS before we allow the next detection.
  if (currentState == HIGH) {
    if (lastSensor1State != HIGH) {
      sensor1HighSince = currentTime;
    }
    if (!sensor1Armed && (currentTime - sensor1HighSince >= (unsigned long)SENSOR1_REARM_HIGH_MS)) {
      sensor1Armed = true;
    }
  }

  // Detect falling edge (HIGH -> LOW) with lockout + armed gate
  if (sensor1Armed && lastSensor1State == HIGH && currentState == LOW) {
    if (currentTime - lastSensor1Time > (unsigned long)SENSOR1_LOCKOUT_MS) {
      handleBottleDetection(currentTime);
      lastSensor1Time = currentTime;
      sensor1Armed = false; // disarm until sensor returns HIGH stable
    }
  }
  
  lastSensor1State = currentState;
}

void handleBottleDetection(unsigned long detectionTime) {
  totalDetections++;
  
  // Add new entry to queue (initially OK, will be updated when Pi responds)
  if (queueCount < BUFFER_SIZE) {
    pendingRejections[queueTail] = false;  // Default: OK (no rejection)
    queueTail = (queueTail + 1) % BUFFER_SIZE;
    queueCount++;
    
    Serial.print("[Sensor 1] Bottle detected → AI triggered | Queue: ");
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
  // Only check sensor if conveyor is running
  if (!conveyorRunning) {
    return;
  }
  
  bool currentState = digitalRead(SENSOR_2_PIN);
  unsigned long currentTime = millis();
  
  // Detect falling edge (HIGH -> LOW) with debouncing
  if (lastSensor2State == HIGH && currentState == LOW) {
    if (currentTime - lastSensor2Time > (unsigned long)SENSOR2_DEBOUNCE_MS) {
      handleServoSensorDetection();
      lastSensor2Time = currentTime;
    }
  }
  
  lastSensor2State = currentState;
}

void handleServoSensorDetection() {
  // Check if there's a pending rejection at the head of queue
  if (queueCount > 0) {
    Serial.print("[Sensor 2] Bottle at index ");
    Serial.print(queueHead);
    Serial.print(" detected → ");
    
    if (pendingRejections[queueHead]) {
      // There's a NG bottle waiting → Kick it now!
      Serial.println("NG → KICKING!");
      executeKick();
    } else {
      // OK bottle → Let it pass
      totalPassed++;
      Serial.println("OK → PASSING");
    }
    
    // Remove from queue
    pendingRejections[queueHead] = false;
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
    char command = Serial.read();
    
    if (command == 'S') {
      // START command - start conveyor
      startConveyor();
    }
    else if (command == 'P') {
      // PAUSE/STOP command - stop conveyor
      stopConveyor();
    }
    else if (command == 'O') {
      // OK product - bottle at decisionIndex stays false (OK)
      if (decisionIndex != queueTail) {
        Serial.print("[Pi Decision] OK → Bottle at index ");
        Serial.print(decisionIndex);
        Serial.println(" will pass");
        
        // Move to next bottle waiting for decision
        decisionIndex = (decisionIndex + 1) % BUFFER_SIZE;
      } else {
        Serial.println("[WARNING] Received OK but no bottle waiting for decision");
      }
    } 
    else if (command == 'N') {
      // NG product - mark bottle at decisionIndex as pending rejection
      markAsRejection();
    }
  }
}

void markAsRejection() {
  // Mark the bottle at decisionIndex (next in line waiting for decision)
  if (decisionIndex != queueTail) {
    pendingRejections[decisionIndex] = true;
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
// CONVEYOR CONTROL
// ============================================================================

void startConveyor() {
  if (!conveyorRunning) {
    digitalWrite(RELAY_PIN, LOW);  // LOW = Run
    conveyorRunning = true;
    Serial.println("[Conveyor] STARTED - Belt running");
  } else {
    Serial.println("[Conveyor] Already running");
  }
}

void stopConveyor() {
  if (conveyorRunning) {
    digitalWrite(RELAY_PIN, HIGH);  // HIGH = Stop
    conveyorRunning = false;
    Serial.println("[Conveyor] STOPPED - Belt paused");
  } else {
    Serial.println("[Conveyor] Already stopped");
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
