/*
 * Product Sorter - Arduino Uno Controller
 * 
 * Nhận lệnh từ Raspberry Pi qua USB Serial
 * Điều khiển:
 *   - Relay (D7): Bật/tắt băng chuyền (motor DC 12V)
 *   - Servo (D9): Gạt sản phẩm lỗi
 * 
 * Kết nối:
 *   - Relay: VCC→5V, GND→GND, IN→D7
 *   - Servo: Signal→D9, VCC→5V (nguồn tổ ong), GND→GND chung
 *   - USB Serial: Tự động kết nối với Raspberry Pi
 */

#include <Servo.h>

// Pin definitions
#define RELAY_PIN 7
#define SERVO_PIN 9

// Servo positions
#define SERVO_CENTER 90
#define SERVO_LEFT 0
#define SERVO_RIGHT 180

// Servo object
Servo sorter;

// Command buffer
String command = "";

void setup() {
  // Initialize serial communication (115200 baud for faster response)
  Serial.begin(115200);
  
  // Initialize relay pin
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);  // Băng chuyền dừng ban đầu
  
  // Initialize servo
  sorter.attach(SERVO_PIN);
  sorter.write(SERVO_CENTER);  // Vị trí trung tâm
  
  // Startup message
  Serial.println("Arduino Product Sorter Ready");
  Serial.println("Commands: RELAY_ON, RELAY_OFF, SERVO_LEFT, SERVO_CENTER, SERVO_RIGHT, EJECT");
}

void loop() {
  // Đọc lệnh từ Serial
  if (Serial.available() > 0) {
    char c = Serial.read();
    
    if (c == '\n') {
      // Kết thúc lệnh, xử lý
      command.trim();
      processCommand(command);
      command = "";  // Reset buffer
    } else {
      command += c;
    }
  }
}

void processCommand(String cmd) {
  cmd.toUpperCase();  // Chuyển về chữ hoa
  
  if (cmd == "RELAY_ON") {
    digitalWrite(RELAY_PIN, HIGH);
    Serial.println("OK: Conveyor started");
    
  } else if (cmd == "RELAY_OFF") {
    digitalWrite(RELAY_PIN, LOW);
    Serial.println("OK: Conveyor stopped");
    
  } else if (cmd == "SERVO_LEFT") {
    sorter.write(SERVO_LEFT);
    Serial.println("OK: Servo moved to LEFT");
    
  } else if (cmd == "SERVO_CENTER") {
    sorter.write(SERVO_CENTER);
    Serial.println("OK: Servo moved to CENTER");
    
  } else if (cmd == "SERVO_RIGHT") {
    sorter.write(SERVO_RIGHT);
    Serial.println("OK: Servo moved to RIGHT");
    
  } else if (cmd == "EJECT") {
    // Sequence tự động: Dừng → Gạt → Trả về → Chạy
    ejectBadProduct();
    
  } else if (cmd == "PING") {
    Serial.println("PONG");
    
  } else if (cmd == "STATUS") {
    printStatus();
    
  } else {
    Serial.print("ERROR: Unknown command: ");
    Serial.println(cmd);
  }
}

void ejectBadProduct() {
  Serial.println("Starting eject sequence...");
  
  // 1. Dừng băng chuyền
  digitalWrite(RELAY_PIN, LOW);
  Serial.println("  Step 1: Conveyor stopped");
  delay(300);
  
  // 2. Gạt sản phẩm
  sorter.write(SERVO_LEFT);
  Serial.println("  Step 2: Servo ejecting product");
  delay(800);  // Đợi servo gạt xong
  
  // 3. Trả servo về trung tâm
  sorter.write(SERVO_CENTER);
  Serial.println("  Step 3: Servo returned to center");
  delay(500);
  
  // 4. Khởi động lại băng chuyền
  digitalWrite(RELAY_PIN, HIGH);
  Serial.println("  Step 4: Conveyor restarted");
  
  Serial.println("Eject sequence complete");
}

void printStatus() {
  Serial.println("=== System Status ===");
  Serial.print("Relay (Conveyor): ");
  Serial.println(digitalRead(RELAY_PIN) == HIGH ? "ON" : "OFF");
  Serial.print("Servo Position: ");
  Serial.println(sorter.read());
  Serial.println("====================");
}

