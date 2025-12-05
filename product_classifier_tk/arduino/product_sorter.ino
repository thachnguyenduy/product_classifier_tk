/*
 * ================================================================================
 * Coca-Cola Bottle Defect Detection System - Arduino Uno Controller
 * ================================================================================
 * 
 * Hardware:
 *   - IR Sensor (D2): Active LOW - Detects bottle presence
 *   - Relay 5V (D7): LOW Trigger - Controls 12V DC conveyor motor
 *   - Servo Motor (D9): Ejects defective bottles
 * 
 * Communication:
 *   - USB Serial @ 115200 baud
 *   - Sends "DETECTED" when IR sensor detects bottle
 *   - Receives "START_CONVEYOR", "STOP_CONVEYOR", "REJECT" commands from Pi
 * 
 * Pin Connections:
 *   - IR Sensor: VCC→5V, GND→GND, OUT→D2 (Active LOW)
 *   - Relay Module: VCC→5V, GND→GND, IN→D7 (LOW=ON, HIGH=OFF)
 *   - Servo: Signal→D9, VCC→5V (external supply), GND→GND common
 * 
 * ================================================================================
 */

#include <Servo.h>

// ======================== PIN CONFIGURATION ========================
#define IR_SENSOR_PIN   2    // IR sensor input (Active LOW)
#define RELAY_PIN       7    // Relay control (LOW trigger)
#define SERVO_PIN       9    // Servo motor signal

// ======================= SERVO POSITIONS ===========================
#define SERVO_REST      90   // Rest position (centered)
#define SERVO_EJECT     0    // Ejection position (push bottle off)
#define SERVO_RETURN    90   // Return to rest

// ===================== TIMING PARAMETERS ===========================
#define DEBOUNCE_TIME   50   // IR sensor debounce (ms)
#define SERVO_EJECT_TIME 500 // Time to hold eject position (ms)
#define SERVO_RETURN_TIME 300 // Time to return to rest (ms)

// =========================== GLOBALS ===============================
Servo ejectorServo;
String commandBuffer = "";

// IR Sensor state
int lastIRState = HIGH;          // Previous IR sensor state
unsigned long lastDebounceTime = 0;
bool bottleDetected = false;

// Conveyor state
bool conveyorRunning = false;

// ========================== FUNCTIONS ==============================

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  
  // Configure pins
  pinMode(IR_SENSOR_PIN, INPUT_PULLUP);  // IR sensor with pull-up
  pinMode(RELAY_PIN, OUTPUT);
  
  // Initialize relay (HIGH = OFF for LOW-trigger relay)
  digitalWrite(RELAY_PIN, HIGH);  // Conveyor OFF initially
  
  // Initialize servo
  ejectorServo.attach(SERVO_PIN);
  ejectorServo.write(SERVO_REST);
  
  // Startup message
  Serial.println("========================================");
  Serial.println("Arduino Bottle Defect System Ready");
  Serial.println("Commands: START_CONVEYOR, STOP_CONVEYOR, REJECT, PING, STATUS");
  Serial.println("========================================");
}

void loop() {
  // Check for bottle detection (IR sensor)
  checkBottleSensor();
  
  // Process incoming serial commands from Raspberry Pi
  processSerialCommands();
}

/**
 * Check IR sensor for bottle detection with debouncing
 * Sends "DETECTED" signal to Pi when bottle passes sensor
 */
void checkBottleSensor() {
  int currentReading = digitalRead(IR_SENSOR_PIN);
  
  // IR sensor is Active LOW: LOW = bottle detected
  if (currentReading == LOW && lastIRState == HIGH) {
    // State changed from HIGH to LOW (bottle detected)
    unsigned long currentTime = millis();
    
    if (currentTime - lastDebounceTime > DEBOUNCE_TIME) {
      // Valid detection (debounced)
      lastDebounceTime = currentTime;
      
      // Send detection signal to Pi
      Serial.println("DETECTED");
      
      bottleDetected = true;
    }
  }
  
  lastIRState = currentReading;
}

/**
 * Process incoming serial commands from Raspberry Pi
 */
void processSerialCommands() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    
    if (c == '\n') {
      // Command complete
      commandBuffer.trim();
      executeCommand(commandBuffer);
      commandBuffer = "";
    } else {
      commandBuffer += c;
    }
  }
}

/**
 * Execute received command
 */
void executeCommand(String cmd) {
  cmd.toUpperCase();
  
  if (cmd == "START_CONVEYOR") {
    startConveyor();
    
  } else if (cmd == "STOP_CONVEYOR") {
    stopConveyor();
    
  } else if (cmd == "REJECT") {
    rejectBottle();
    
  } else if (cmd == "PING") {
    Serial.println("PONG");
    
  } else if (cmd == "STATUS") {
    printStatus();
    
  } else if (cmd.length() > 0) {
    Serial.print("ERROR: Unknown command: ");
    Serial.println(cmd);
  }
}

/**
 * Start conveyor belt (Relay LOW = ON for LOW-trigger relay)
 */
void startConveyor() {
  digitalWrite(RELAY_PIN, LOW);  // LOW triggers relay ON
  conveyorRunning = true;
  Serial.println("OK: Conveyor started");
}

/**
 * Stop conveyor belt (Relay HIGH = OFF)
 */
void stopConveyor() {
  digitalWrite(RELAY_PIN, HIGH);  // HIGH = relay OFF
  conveyorRunning = false;
  Serial.println("OK: Conveyor stopped");
}

/**
 * Reject defective bottle using servo
 * NOTE: Conveyor continues running (continuous flow)
 */
void rejectBottle() {
  Serial.println("REJECT: Ejecting bottle...");
  
  // Push servo to eject position
  ejectorServo.write(SERVO_EJECT);
  delay(SERVO_EJECT_TIME);
  
  // Return servo to rest position
  ejectorServo.write(SERVO_RETURN);
  delay(SERVO_RETURN_TIME);
  
  Serial.println("OK: Bottle ejected");
}

/**
 * Print system status
 */
void printStatus() {
  Serial.println("====== System Status ======");
  Serial.print("Conveyor: ");
  Serial.println(conveyorRunning ? "RUNNING" : "STOPPED");
  Serial.print("Relay State: ");
  Serial.println(digitalRead(RELAY_PIN) == LOW ? "ON (LOW)" : "OFF (HIGH)");
  Serial.print("IR Sensor: ");
  Serial.println(digitalRead(IR_SENSOR_PIN) == LOW ? "BLOCKED" : "CLEAR");
  Serial.print("Servo Position: ");
  Serial.println(ejectorServo.read());
  Serial.println("===========================");
}

