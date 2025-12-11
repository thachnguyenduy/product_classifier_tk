/*
 * ============================================
 * COCA-COLA SORTING SYSTEM - ARDUINO CODE
 * FIFO Queue Mode with IR Trigger
 * ============================================
 * 
 * Hardware:
 * - IR Sensor (Digital Pin 2) - Detects bottle at end
 * - Servo (Digital Pin 9) - Kicks NG bottles
 * 
 * Protocol:
 * - Send 'T' to Pi when IR sensor detects bottle
 * - Receive 'K' from Pi to kick
 * - Receive 'O' from Pi for OK (optional, for logging)
 * 
 * ============================================
 */

#include <Servo.h>

// ============================================
// PIN DEFINITIONS
// ============================================
const int IR_SENSOR_PIN = 2;
const int SERVO_PIN = 9;

// ============================================
// SERVO SETTINGS
// ============================================
const int SERVO_IDLE = 0;     // Idle position (degrees)
const int SERVO_KICK = 100;   // Kick position (degrees)
const int KICK_DURATION = 150; // Kick duration (ms)

// ============================================
// DEBOUNCE SETTINGS
// ============================================
const unsigned long DEBOUNCE_DELAY = 300; // ms

// ============================================
// GLOBALS
// ============================================
Servo rejectServo;

bool lastSensorState = HIGH;  // HIGH = no object (assuming pull-up)
unsigned long lastTriggerTime = 0;

// ============================================
// SETUP
// ============================================
void setup() {
  // Initialize Serial
  Serial.begin(9600);
  
  // Initialize IR Sensor (INPUT with pull-up)
  pinMode(IR_SENSOR_PIN, INPUT_PULLUP);
  
  // Initialize Servo
  rejectServo.attach(SERVO_PIN);
  rejectServo.write(SERVO_IDLE);
  
  // Startup message
  Serial.println("Arduino Ready!");
  Serial.println("Waiting for bottles...");
  
  delay(1000);
}

// ============================================
// MAIN LOOP
// ============================================
void loop() {
  // 1. Check IR Sensor
  checkIRSensor();
  
  // 2. Check Serial for commands
  checkSerial();
  
  delay(10); // Small delay for stability
}

// ============================================
// CHECK IR SENSOR
// ============================================
void checkIRSensor() {
  bool currentState = digitalRead(IR_SENSOR_PIN);
  unsigned long currentTime = millis();
  
  // Edge detection: HIGH -> LOW (object detected)
  if (currentState == LOW && lastSensorState == HIGH) {
    // Debounce check
    if (currentTime - lastTriggerTime > DEBOUNCE_DELAY) {
      // Send trigger to Pi
      Serial.print('T');
      Serial.flush();
      
      if (true) { // Verbose logging (set to false for production)
        Serial.println();
        Serial.print("Bottle detected at: ");
        Serial.println(currentTime);
      }
      
      lastTriggerTime = currentTime;
    }
  }
  
  lastSensorState = currentState;
}

// ============================================
// CHECK SERIAL FOR COMMANDS
// ============================================
void checkSerial() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    if (command == 'K') {
      // Kick command
      executeKick();
      
      if (true) { // Verbose logging
        Serial.println("Command received: KICK");
      }
    }
    else if (command == 'O') {
      // OK command (optional, just for logging)
      if (true) { // Verbose logging
        Serial.println("Command received: OK");
      }
    }
  }
}

// ============================================
// EXECUTE KICK
// ============================================
void executeKick() {
  // Move servo to kick position
  rejectServo.write(SERVO_KICK);
  
  // Hold for kick duration
  delay(KICK_DURATION);
  
  // Return to idle
  rejectServo.write(SERVO_IDLE);
  
  if (true) { // Verbose logging
    Serial.println("Servo kicked!");
  }
}

