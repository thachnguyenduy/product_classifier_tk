/*
 * TEST RELAY MODULE
 * Dùng để kiểm tra relay hoạt động đúng không
 * 
 * Upload code này, mở Serial Monitor (9600 baud)
 * Gửi:
 *   '1' = Set relay HIGH
 *   '0' = Set relay LOW
 * 
 * Quan sát băng chuyền chạy hay dừng
 */

const int RELAY_PIN = 4;

void setup() {
  Serial.begin(9600);
  pinMode(RELAY_PIN, OUTPUT);
  
  // Bắt đầu với HIGH
  digitalWrite(RELAY_PIN, HIGH);
  
  Serial.println("=== RELAY TEST MODE ===");
  Serial.println("Commands:");
  Serial.println("  '1' = Set relay HIGH");
  Serial.println("  '0' = Set relay LOW");
  Serial.println();
  Serial.println("Current: HIGH");
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    if (cmd == '1') {
      digitalWrite(RELAY_PIN, HIGH);
      Serial.println(">>> Relay = HIGH");
      Serial.println("Băng chuyền CHẠY hay DỪNG?");
    }
    else if (cmd == '0') {
      digitalWrite(RELAY_PIN, LOW);
      Serial.println(">>> Relay = LOW");
      Serial.println("Băng chuyền CHẠY hay DỪNG?");
    }
  }
}

