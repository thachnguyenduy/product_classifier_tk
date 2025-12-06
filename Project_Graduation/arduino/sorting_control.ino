/*
 * Coca-Cola Sorting System - Arduino Controller
 * Hardware: Arduino Uno
 * Components: IR Sensor (Pin 2), Relay Module (Pin 4), Servo Motor (Pin 9)
 * 
 * Communication Protocol:
 * - Receives 'D' command: Detected bottle (sent by Arduino to Pi)
 * - Sends 'O': OK product (Pi to Arduino)
 * - Sends 'N': NG product (Pi to Arduino)
 */

#include <Servo.h>

// Pin Definitions
const int SENSOR_PIN = 2;     // IR Sensor Input
const int RELAY_PIN = 4;      // Relay Control (LOW = Run, HIGH = Stop)
const int SERVO_PIN = 9;      // Servo Motor for rejection

// Servo Object
Servo rejectServo;

// Servo Positions
const int SERVO_IDLE = 0;     // Idle position
const int SERVO_KICK = 90;    // Kicking position

// Timing Constants
const int STABILIZE_DELAY = 500;  // Delay after stopping conveyor
const int SERVO_KICK_DELAY = 800;  // Time servo stays in kick position
const int MOVE_TO_SERVO_DELAY = 1500;  // Time to move bottle to servo position

void setup() {
  // Initialize Serial Communication
  Serial.begin(9600);
  
  // Configure Pins
  pinMode(SENSOR_PIN, INPUT);
  pinMode(RELAY_PIN, OUTPUT);
  
  // Initialize Servo
  rejectServo.attach(SERVO_PIN);
  rejectServo.write(SERVO_IDLE);
  
  // Start with conveyor running (Relay LOW trigger)
  digitalWrite(RELAY_PIN, LOW);
  
  Serial.println("Coca-Cola Sorting System Ready");
  Serial.println("Conveyor Running...");
}

void loop() {
  // Default state: Conveyor running
  digitalWrite(RELAY_PIN, LOW);
  
  // Check if IR sensor detects a bottle (LOW = detected)
  if (digitalRead(SENSOR_PIN) == LOW) {
    handleBottleDetection();
  }
  
  delay(50);  // Small delay to prevent bouncing
}

void handleBottleDetection() {
  // 1. Stop the conveyor
  stopConveyor();
  Serial.println("Bottle detected! Conveyor stopped.");
  
  // 2. Wait for stabilization
  delay(STABILIZE_DELAY);
  
  // 3. Send detection signal to Raspberry Pi
  Serial.println('D');  // Send 'D' to trigger camera capture
  Serial.println("Waiting for AI decision...");
  
  // 4. Wait for Pi's decision ('O' for OK, 'N' for NG)
  char decision = waitForDecision();
  
  // 5. Act based on decision
  if (decision == 'N') {
    handleNGProduct();
  } else if (decision == 'O') {
    handleOKProduct();
  } else {
    // Timeout or invalid response - default to OK (safety)
    Serial.println("No valid response. Defaulting to OK.");
    handleOKProduct();
  }
}

void stopConveyor() {
  digitalWrite(RELAY_PIN, HIGH);  // LOW trigger relay: HIGH = Stop
}

void startConveyor() {
  digitalWrite(RELAY_PIN, LOW);   // LOW trigger relay: LOW = Run
}

char waitForDecision() {
  unsigned long startTime = millis();
  const unsigned long TIMEOUT = 10000;  // 10 second timeout
  
  while (millis() - startTime < TIMEOUT) {
    if (Serial.available() > 0) {
      char received = Serial.read();
      if (received == 'O' || received == 'N') {
        return received;
      }
    }
    delay(10);
  }
  
  return 'T';  // Timeout
}

void handleOKProduct() {
  Serial.println("Decision: OK - Product passed");
  
  // Simply restart the conveyor
  startConveyor();
  Serial.println("Conveyor running...");
  
  delay(1000);  // Brief delay before next detection
}

void handleNGProduct() {
  Serial.println("Decision: NG - Product rejected");
  
  // Step 1: Move bottle to servo position
  Serial.println("Moving bottle to rejection position...");
  startConveyor();
  delay(MOVE_TO_SERVO_DELAY);
  
  // Step 2: Stop at servo position
  stopConveyor();
  delay(200);
  
  // Step 3: Activate servo to kick bottle off
  Serial.println("Activating rejection servo...");
  rejectServo.write(SERVO_KICK);
  delay(SERVO_KICK_DELAY);
  
  // Step 4: Return servo to idle
  rejectServo.write(SERVO_IDLE);
  delay(300);
  
  // Step 5: Restart conveyor
  startConveyor();
  Serial.println("Conveyor running...");
  
  delay(1000);  // Brief delay before next detection
}

