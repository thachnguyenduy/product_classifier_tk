/*
 * Coca-Cola Sorting System - Arduino Controller (CONTINUOUS CONVEYOR)
 * Hardware: Arduino Uno
 * Components: IR Sensor (Pin 2), Relay Module (Pin 4), Servo Motor (Pin 9)
 * 
 * WORKFLOW (Continuous - No Stopping):
 * 1. Conveyor ALWAYS runs (Relay = LOW)
 * 2. IR Sensor detects bottle -> Send 'D' to Pi -> Record timestamp
 * 3. Pi responds with 'O' (OK) or 'N' (NG)
 * 4. If 'N': Calculate kick_time = timestamp + TRAVEL_TIME, add to circular buffer
 * 5. Loop continuously checks buffer, kicks bottle when millis() >= kick_time
 * 
 * CRITICAL: TRAVEL_TIME = Time from sensor to servo position (~4500ms default)
 * Multiple bottles can be in the processing zone simultaneously
 */

#include <Servo.h>

// ============================================================================
// CONFIGURATION (Adjust these values for your physical setup)
// ============================================================================

// Pin Definitions
const int SENSOR_PIN = 2;     // IR Sensor Input
const int RELAY_PIN = 4;      // Relay Control (LOW = Run, HIGH = Stop - but we keep it LOW always)
const int SERVO_PIN = 9;      // Servo Motor for rejection

// Timing Configuration
unsigned long TRAVEL_TIME = 4500;  // Time (ms) from sensor to servo position
                                    // CRITICAL: Measure this physically!
                                    // Too short = kick early (miss bottle)
                                    // Too long = kick late (wrong bottle)

// Servo Configuration
const int SERVO_IDLE = 0;         // Idle position (retracted)
const int SERVO_KICK = 100;       // Kick position (extended)
const int SERVO_KICK_DURATION = 2000;  // How long servo stays extended/blocking (ms) - 2000ms = 2s

// Circular Buffer Configuration
const int BUFFER_SIZE = 20;       // Max bottles that can be tracked simultaneously
                                  // With 4.5s travel time and ~2 bottles/sec = need ~10 slots
                                  // 20 provides safety margin

// Sensor Debouncing
const int DEBOUNCE_DELAY = 300;   // Minimum time between detections (ms)

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================

Servo rejectServo;

// Circular Buffer for Kick Times
unsigned long kickQueue[BUFFER_SIZE];
int queueHead = 0;  // Index to read from (oldest)
int queueTail = 0;  // Index to write to (newest)
int queueCount = 0; // Number of items in queue

// Sensor State
bool lastSensorState = HIGH;
unsigned long lastDetectionTime = 0;

// Statistics
unsigned long totalDetections = 0;
unsigned long totalRejections = 0;

// ============================================================================
// SETUP
// ============================================================================

void setup() {
  // Initialize Serial Communication
  Serial.begin(9600);
  
  // Configure Pins
  pinMode(SENSOR_PIN, INPUT);
  pinMode(RELAY_PIN, OUTPUT);
  
  // Initialize Servo
  rejectServo.attach(SERVO_PIN);
  rejectServo.write(SERVO_IDLE);
  
  // CRITICAL: Conveyor ALWAYS runs in continuous mode
  digitalWrite(RELAY_PIN, LOW);
  
  // Initialize circular buffer (all zeros)
  for (int i = 0; i < BUFFER_SIZE; i++) {
    kickQueue[i] = 0;
  }
  
  // Startup Message
  Serial.println("========================================");
  Serial.println("Coca-Cola Sorting System - CONTINUOUS MODE");
  Serial.println("========================================");
  Serial.print("Travel Time: ");
  Serial.print(TRAVEL_TIME);
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
  // 1. Check IR Sensor for bottle detection
  checkSensor();
  
  // 2. Check Serial for Pi's decision ('O' or 'N')
  checkSerial();
  
  // 3. Process kick queue (trigger servo if time has come)
  processKickQueue();
  
  // Small delay to prevent CPU overload
  delay(10);
}

// ============================================================================
// SENSOR DETECTION
// ============================================================================

void checkSensor() {
  bool currentSensorState = digitalRead(SENSOR_PIN);
  unsigned long currentTime = millis();
  
  // Detect falling edge (HIGH -> LOW) with debouncing
  if (lastSensorState == HIGH && currentSensorState == LOW) {
    // Check debounce
    if (currentTime - lastDetectionTime > DEBOUNCE_DELAY) {
      handleBottleDetection(currentTime);
      lastDetectionTime = currentTime;
    }
  }
  
  lastSensorState = currentSensorState;
}

void handleBottleDetection(unsigned long detectionTime) {
  totalDetections++;
  
  // Send detection signal to Raspberry Pi
  // Format: 'D' followed by timestamp for Pi's reference
  Serial.print('D');
  Serial.print(',');
  Serial.println(detectionTime);
  
  // Debug output
  if (totalDetections % 10 == 0) {
    printStatistics();
  }
}

// ============================================================================
// SERIAL COMMUNICATION (Receive Pi's Decision)
// ============================================================================

void checkSerial() {
  if (Serial.available() > 0) {
    char decision = Serial.read();
    
    if (decision == 'O') {
      // OK product - do nothing, let it pass
      // Serial.println("[Arduino] OK - Pass");
    } 
    else if (decision == 'N') {
      // NG product - schedule kick
      scheduleKick();
    }
  }
}

void scheduleKick() {
  // Calculate when to kick (current time + travel time)
  unsigned long kickTime = millis() + TRAVEL_TIME;
  
  // Add to circular buffer
  if (queueCount < BUFFER_SIZE) {
    kickQueue[queueTail] = kickTime;
    queueTail = (queueTail + 1) % BUFFER_SIZE;
    queueCount++;
    totalRejections++;
    
    // Debug output
    Serial.print("[Arduino] NG - Kick scheduled at ");
    Serial.print(kickTime);
    Serial.print(" (in ");
    Serial.print(TRAVEL_TIME);
    Serial.print(" ms) | Queue: ");
    Serial.println(queueCount);
  } else {
    // Buffer overflow - this should never happen with proper sizing
    Serial.println("[ERROR] Kick queue full! Bottle will not be rejected.");
  }
}

// ============================================================================
// KICK QUEUE PROCESSING
// ============================================================================

void processKickQueue() {
  // Check if there are items in the queue
  if (queueCount > 0) {
    unsigned long currentTime = millis();
    unsigned long nextKickTime = kickQueue[queueHead];
    
    // Check if it's time to kick
    // Use >= to handle millis() overflow (happens every ~50 days)
    if (currentTime >= nextKickTime) {
      executeKick();
      
      // Remove from queue
      queueHead = (queueHead + 1) % BUFFER_SIZE;
      queueCount--;
      
      Serial.print("[Arduino] Kick executed | Queue remaining: ");
      Serial.println(queueCount);
    }
  }
}

void executeKick() {
  // Fast kick motion
  rejectServo.write(SERVO_KICK);
  delay(SERVO_KICK_DURATION);
  rejectServo.write(SERVO_IDLE);
  
  // Note: Using delay() here is acceptable because:
  // 1. Kick duration is very short (150ms)
  // 2. Pi's AI processing takes much longer (~500ms)
  // 3. Bottles are spaced apart (>1 second typically)
}

// ============================================================================
// STATISTICS & DEBUGGING
// ============================================================================

void printStatistics() {
  Serial.println("--- Statistics ---");
  Serial.print("Total Detections: ");
  Serial.println(totalDetections);
  Serial.print("Total Rejections: ");
  Serial.println(totalRejections);
  Serial.print("Pass Rate: ");
  if (totalDetections > 0) {
    float passRate = 100.0 * (totalDetections - totalRejections) / totalDetections;
    Serial.print(passRate);
    Serial.println("%");
  } else {
    Serial.println("N/A");
  }
  Serial.print("Current Queue Size: ");
  Serial.println(queueCount);
  Serial.println("------------------");
}

// ============================================================================
// CALIBRATION HELPER (Call via Serial command 'C')
// ============================================================================

// Optional: Add calibration mode
// Send 'C' from Pi to enter calibration mode
// Arduino will print sensor state continuously for physical measurement
