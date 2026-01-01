/*
 * QUICK TEST for Dual Sensor + MG996R Setup
 * Use this to test sensors and servo independently before running full system
 * 
 * Upload this sketch to test:
 * 1. Both sensors working
 * 2. Servo angles (IDLE and KICK)
 * 3. Kick duration
 * 
 * Open Serial Monitor at 9600 baud
 * Send commands:
 *   'T' = Test servo (kick motion)
 *   'S' = Show sensor states (continuous)
 *   'R' = Reset and show statistics
 */

#include <Servo.h>

// Pin Definitions
const int SENSOR_1_PIN = 2;
const int SENSOR_2_PIN = 3;
const int SERVO_PIN = 9;

// Servo Configuration (adjust these values)
const int SERVO_IDLE = 0;
const int SERVO_KICK = 90;
const int SERVO_KICK_DURATION = 2000;

Servo testServo;
bool showSensors = false;

void setup() {
  Serial.begin(9600);
  
  pinMode(SENSOR_1_PIN, INPUT);
  pinMode(SENSOR_2_PIN, INPUT);
  
  testServo.attach(SERVO_PIN);
  testServo.write(SERVO_IDLE);
  
  Serial.println("==========================================");
  Serial.println("  DUAL SENSOR + MG996R TEST MODE");
  Serial.println("==========================================");
  Serial.println();
  Serial.println("Commands:");
  Serial.println("  T = Test servo kick");
  Serial.println("  S = Show sensor states (toggle)");
  Serial.println("  R = Reset statistics");
  Serial.println();
  Serial.print("Servo IDLE angle:  ");
  Serial.println(SERVO_IDLE);
  Serial.print("Servo KICK angle:  ");
  Serial.println(SERVO_KICK);
  Serial.print("Kick duration:     ");
  Serial.print(SERVO_KICK_DURATION);
  Serial.println(" ms");
  Serial.println();
  Serial.println("Ready for testing...");
  Serial.println();
}

void loop() {
  // Check for commands
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    if (cmd == 'T' || cmd == 't') {
      testServoKick();
    }
    else if (cmd == 'S' || cmd == 's') {
      showSensors = !showSensors;
      Serial.print("Sensor monitoring: ");
      Serial.println(showSensors ? "ON" : "OFF");
    }
    else if (cmd == 'R' || cmd == 'r') {
      Serial.println("Statistics reset");
    }
  }
  
  // Show sensor states if enabled
  if (showSensors) {
    bool s1 = digitalRead(SENSOR_1_PIN);
    bool s2 = digitalRead(SENSOR_2_PIN);
    
    Serial.print("Sensor 1: ");
    Serial.print(s1 ? "HIGH" : "LOW ");
    Serial.print("  |  Sensor 2: ");
    Serial.println(s2 ? "HIGH" : "LOW ");
    
    delay(200);
  }
}

void testServoKick() {
  Serial.println(">>> Testing servo kick motion...");
  
  Serial.print("  1. Moving to IDLE (");
  Serial.print(SERVO_IDLE);
  Serial.println("°)");
  testServo.write(SERVO_IDLE);
  delay(1000);
  
  Serial.print("  2. Moving to KICK (");
  Serial.print(SERVO_KICK);
  Serial.println("°)");
  testServo.write(SERVO_KICK);
  
  Serial.print("  3. Holding for ");
  Serial.print(SERVO_KICK_DURATION);
  Serial.println(" ms");
  delay(SERVO_KICK_DURATION);
  
  Serial.println("  4. Returning to IDLE");
  testServo.write(SERVO_IDLE);
  delay(500);
  
  Serial.println(">>> Test complete!");
  Serial.println();
  Serial.println("Check:");
  Serial.println("  - Did rack extend fully?");
  Serial.println("  - Was it blocked long enough?");
  Serial.println("  - Did it return smoothly?");
  Serial.println();
}

