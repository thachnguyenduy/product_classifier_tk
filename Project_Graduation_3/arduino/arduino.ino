/*
 * ============================================
 * COCA-COLA BOTTLE SORTING SYSTEM
 * Arduino Uno Controller
 * ============================================
 * 
 * Graduation Project
 * 
 * Hardware Connections:
 * - IR Sensor: Digital Pin 2 (INPUT_PULLUP)
 * - Servo Motor: Digital Pin 9 (OUTPUT)
 * - Relay Module: Digital Pin 4 (OUTPUT)
 * 
 * Power:
 * - Arduino: USB power from Raspberry Pi
 * - Servo + Relay: External 5V 5A supply
 * 
 * ============================================
 * PROTOCOL
 * ============================================
 * 
 * Raspberry Pi → Arduino (Serial):
 * - 'O' = OK product (servo allows bottle to pass)
 * - 'N' = NG product (servo blocks bottle)
 * - 'S' = Start conveyor (relay ON)
 * - 'P' = Pause/Stop conveyor (relay OFF)
 * 
 * Arduino → Raspberry Pi (Serial):
 * - 'T' = IR sensor triggered (bottle detected)
 * 
 * ============================================
 * LOGIC FLOW
 * ============================================
 * 
 * 1. Raspberry Pi continuously tracks bottles
 * 2. When bottle crosses virtual line:
 *    - Pi finalizes classification
 *    - Pi sends 'O' or 'N' to Arduino
 *    - Arduino stores this classification
 * 3. When bottle reaches IR sensor:
 *    - Arduino detects bottle
 *    - Arduino sends 'T' to Pi
 *    - Arduino actuates servo based on LAST classification
 *      - 'O' → Servo stays at idle (allow pass)
 *      - 'N' → Servo moves to block position
 * 
 * ============================================
 * RELAY LOGIC (LOW TRIGGER)
 * ============================================
 * 
 * - digitalWrite(RELAY_PIN, LOW) = Relay ON = Conveyor RUNNING
 * - digitalWrite(RELAY_PIN, HIGH) = Relay OFF = Conveyor STOPPED
 * 
 * ============================================
 */

#include <Servo.h>

// ============================================
// PIN DEFINITIONS
// ============================================
const int IR_SENSOR_PIN = 2;    // IR sensor input
const int SERVO_PIN = 9;         // Servo motor output
const int RELAY_PIN = 4;         // Relay output (conveyor control)

// ============================================
// SERVO SETTINGS
// ============================================
const int SERVO_IDLE = 0;        // Idle position - allow bottle to pass (degrees)
const int SERVO_BLOCK = 100;     // Block position - stop NG bottle (degrees)
const int SERVO_DURATION = 200;  // How long to hold block position (ms)

// ============================================
// RELAY SETTINGS (LOW TRIGGER MODULE)
// ============================================
const int RELAY_ON = LOW;        // LOW = Relay ON = Conveyor running
const int RELAY_OFF = HIGH;      // HIGH = Relay OFF = Conveyor stopped

// ============================================
// DEBOUNCE SETTINGS
// ============================================
const unsigned long DEBOUNCE_DELAY = 300;  // ms - prevent multiple triggers

// ============================================
// GLOBAL VARIABLES
// ============================================
Servo bottleServo;

// IR sensor state
bool lastSensorState = HIGH;           // HIGH = no object (pull-up resistor)
unsigned long lastTriggerTime = 0;     // Last IR trigger timestamp

// Classification state
char lastClassification = 'O';         // Last received classification ('O' or 'N')
bool conveyorRunning = false;          // Conveyor state

// ============================================
// SETUP
// ============================================
void setup() {
  // Initialize Serial (9600 baud)
  Serial.begin(9600);
  
  // Initialize IR Sensor (INPUT with internal pull-up)
  pinMode(IR_SENSOR_PIN, INPUT_PULLUP);
  
  // Initialize Relay (OUTPUT, start with OFF)
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, RELAY_OFF);  // Conveyor OFF initially
  conveyorRunning = false;
  
  // Initialize Servo
  bottleServo.attach(SERVO_PIN);
  bottleServo.write(SERVO_IDLE);       // Start at idle position
  
  // Startup message
  Serial.println("============================================");
  Serial.println("COCA-COLA SORTING SYSTEM - Arduino Ready");
  Serial.println("============================================");
  Serial.println("Servo: IDLE position");
  Serial.println("Relay: OFF (Conveyor stopped)");
  Serial.println("Waiting for START command from Raspberry Pi...");
  Serial.println("============================================");
  
  delay(1000);
}

// ============================================
// MAIN LOOP
// ============================================
void loop() {
  // 1. Check Serial for commands from Raspberry Pi
  checkSerialCommands();
  
  // 2. Check IR Sensor (only if conveyor is running)
  if (conveyorRunning) {
    checkIRSensor();
  }
  
  delay(10);  // Small delay for stability
}

// ============================================
// CHECK IR SENSOR
// ============================================
void checkIRSensor() {
  bool currentState = digitalRead(IR_SENSOR_PIN);
  unsigned long currentTime = millis();
  
  // Edge detection: HIGH → LOW (object detected)
  // IR sensor outputs LOW when object is detected
  if (currentState == LOW && lastSensorState == HIGH) {
    // Debounce check
    if (currentTime - lastTriggerTime > DEBOUNCE_DELAY) {
      // Bottle detected!
      Serial.println();
      Serial.println("--------------------------------------------");
      Serial.println("IR SENSOR TRIGGERED - Bottle detected!");
      Serial.print("Time: ");
      Serial.println(currentTime);
      
      // Send trigger to Raspberry Pi
      Serial.print('T');
      Serial.flush();
      
      // Actuate servo based on LAST classification
      if (lastClassification == 'N') {
        // NG bottle - BLOCK IT
        Serial.println("Classification: NG");
        Serial.println("Action: BLOCKING bottle");
        blockBottle();
      } else {
        // OK bottle - LET IT PASS
        Serial.println("Classification: OK");
        Serial.println("Action: Allowing bottle to pass");
        // Servo already at IDLE, do nothing
      }
      
      Serial.println("--------------------------------------------");
      Serial.println();
      
      lastTriggerTime = currentTime;
    }
  }
  
  lastSensorState = currentState;
}

// ============================================
// CHECK SERIAL COMMANDS
// ============================================
void checkSerialCommands() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    switch (command) {
      case 'O':
        // OK classification received
        lastClassification = 'O';
        Serial.println();
        Serial.println("[Command] Classification received: OK");
        Serial.println();
        break;
      
      case 'N':
        // NG classification received
        lastClassification = 'N';
        Serial.println();
        Serial.println("[Command] Classification received: NG");
        Serial.println();
        break;
      
      case 'S':
        // Start conveyor
        startConveyor();
        break;
      
      case 'P':
        // Pause/Stop conveyor
        stopConveyor();
        break;
      
      default:
        // Unknown command
        Serial.print("[Warning] Unknown command: ");
        Serial.println(command);
        break;
    }
  }
}

// ============================================
// START CONVEYOR
// ============================================
void startConveyor() {
  digitalWrite(RELAY_PIN, RELAY_ON);  // LOW = ON for low-trigger relay
  conveyorRunning = true;
  
  Serial.println();
  Serial.println("============================================");
  Serial.println("CONVEYOR STARTED");
  Serial.println("============================================");
  Serial.println("Monitoring IR sensor for bottles...");
  Serial.println();
}

// ============================================
// STOP CONVEYOR
// ============================================
void stopConveyor() {
  digitalWrite(RELAY_PIN, RELAY_OFF);  // HIGH = OFF for low-trigger relay
  conveyorRunning = false;
  
  Serial.println();
  Serial.println("============================================");
  Serial.println("CONVEYOR STOPPED");
  Serial.println("============================================");
  Serial.println();
}

// ============================================
// BLOCK BOTTLE (NG)
// ============================================
void blockBottle() {
  // Move servo to block position
  bottleServo.write(SERVO_BLOCK);
  Serial.print("Servo moved to: ");
  Serial.println(SERVO_BLOCK);
  
  // Hold for duration
  delay(SERVO_DURATION);
  
  // Return to idle position
  bottleServo.write(SERVO_IDLE);
  Serial.print("Servo returned to: ");
  Serial.println(SERVO_IDLE);
}

// ============================================
// END OF CODE
// ============================================

