"""Hardware control helpers for Raspberry Pi + Arduino."""
from __future__ import annotations

import platform
import time
from typing import Optional

try:
    import serial  # type: ignore
except Exception:  # pragma: no cover
    serial = None


def is_raspberry_pi() -> bool:
    """Return True when running on Raspberry Pi hardware."""
    return "raspberrypi" in platform.uname().node.lower()


class HardwareController:
    """
    Điều khiển Arduino qua USB Serial.
    
    Arduino sẽ điều khiển:
    - Relay (D7): Băng chuyền motor DC 12V
    - Servo (D9): Gạt sản phẩm lỗi
    
    Giao tiếp: USB Serial (/dev/ttyACM0)
    Baud rate: 115200
    """

    def __init__(self, serial_port: str = "/dev/ttyACM0", baud_rate: int = 115200) -> None:
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.available = is_raspberry_pi()
        self.serial_conn: Optional["serial.Serial"] = None
        
        # Thử kết nối Arduino
        if serial is not None:
            self.serial_conn = self._open_serial()
            if self.serial_conn:
                print(f"✅ Connected to Arduino at {serial_port}")
                time.sleep(2)  # Đợi Arduino reset sau khi mở serial
                self._read_response()  # Đọc startup message
            else:
                print(f"⚠️ Cannot connect to Arduino at {serial_port}")
                print("   Hardware functions will be simulated.")
        else:
            print("⚠️ pyserial not installed. Hardware functions disabled.")

    def _open_serial(self) -> Optional["serial.Serial"]:
        """Mở kết nối serial với Arduino."""
        if serial is None:
            return None
        try:
            conn = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            return conn
        except Exception as e:
            print(f"Serial connection failed: {e}")
            return None

    def _send_command(self, command: str) -> bool:
        """Gửi lệnh tới Arduino và đọc response."""
        if self.serial_conn is None:
            print(f"[SIMULATED] Arduino command: {command}")
            return False
        
        try:
            self.serial_conn.write(f"{command}\n".encode())
            print(f"→ Sent to Arduino: {command}")
            
            # Đọc response
            response = self._read_response()
            if response:
                print(f"← Arduino response: {response}")
            return True
            
        except Exception as e:
            print(f"Failed to send command '{command}': {e}")
            return False

    def _read_response(self, timeout: float = 0.5) -> str:
        """Đọc response từ Arduino."""
        if self.serial_conn is None:
            return ""
        
        start_time = time.time()
        response_lines = []
        
        while time.time() - start_time < timeout:
            if self.serial_conn.in_waiting > 0:
                try:
                    line = self.serial_conn.readline().decode().strip()
                    if line:
                        response_lines.append(line)
                except Exception:
                    pass
        
        return "\n".join(response_lines)

    def start_conveyor(self) -> None:
        """Bật băng chuyền (relay ON)."""
        print("🟢 Starting conveyor...")
        self._send_command("RELAY_ON")

    def stop_conveyor(self) -> None:
        """Tắt băng chuyền (relay OFF)."""
        print("🔴 Stopping conveyor...")
        self._send_command("RELAY_OFF")

    def servo_left(self) -> None:
        """Di chuyển servo sang trái (gạt sản phẩm)."""
        print("⬅️ Moving servo LEFT...")
        self._send_command("SERVO_LEFT")

    def servo_center(self) -> None:
        """Trả servo về giữa."""
        print("⏺️ Moving servo CENTER...")
        self._send_command("SERVO_CENTER")

    def servo_right(self) -> None:
        """Di chuyển servo sang phải."""
        print("➡️ Moving servo RIGHT...")
        self._send_command("SERVO_RIGHT")

    def eject_bad_product(self) -> None:
        """
        Sequence tự động gạt sản phẩm lỗi:
        1. Dừng băng chuyền
        2. Gạt sản phẩm (servo left)
        3. Trả servo về giữa
        4. Khởi động băng chuyền
        """
        print("🚫 Ejecting bad product...")
        
        if self.serial_conn:
            # Arduino sẽ tự động thực hiện sequence
            self._send_command("EJECT")
        else:
            # Simulation mode
            print("[SIMULATED] Eject sequence:")
            print("  1. Stop conveyor")
            time.sleep(0.3)
            print("  2. Servo eject")
            time.sleep(0.8)
            print("  3. Servo return")
            time.sleep(0.5)
            print("  4. Start conveyor")

    def push_bad_product(self) -> None:
        """Alias cho eject_bad_product (để tương thích với code cũ)."""
        self.eject_bad_product()

    def get_status(self) -> None:
        """Lấy trạng thái hiện tại từ Arduino."""
        print("📊 Requesting Arduino status...")
        self._send_command("STATUS")

    def ping(self) -> bool:
        """Test kết nối với Arduino."""
        print("🏓 Pinging Arduino...")
        if self._send_command("PING"):
            return True
        return False

    def hardware_test(self) -> None:
        """Test đầy đủ các chức năng hardware."""
        print("\n" + "="*50)
        print("🔧 Hardware Test Sequence")
        print("="*50)
        
        # Test 1: Ping
        print("\n[1/5] Testing connection...")
        self.ping()
        time.sleep(1)
        
        # Test 2: Relay ON
        print("\n[2/5] Testing conveyor START...")
        self.start_conveyor()
        time.sleep(2)
        
        # Test 3: Relay OFF
        print("\n[3/5] Testing conveyor STOP...")
        self.stop_conveyor()
        time.sleep(1)
        
        # Test 4: Servo movements
        print("\n[4/5] Testing servo movements...")
        self.servo_left()
        time.sleep(1)
        self.servo_center()
        time.sleep(1)
        self.servo_right()
        time.sleep(1)
        self.servo_center()
        time.sleep(1)
        
        # Test 5: Full eject sequence
        print("\n[5/5] Testing full eject sequence...")
        self.eject_bad_product()
        time.sleep(2)
        
        # Get status
        print("\n[FINAL] Getting system status...")
        self.get_status()
        
        print("\n" + "="*50)
        print("✅ Hardware test complete")
        print("="*50 + "\n")

    def cleanup(self) -> None:
        """Dọn dẹp khi thoát chương trình."""
        print("🧹 Cleaning up hardware...")
        
        # Dừng băng chuyền
        self.stop_conveyor()
        time.sleep(0.5)
        
        # Trả servo về giữa
        self.servo_center()
        time.sleep(0.5)
        
        # Đóng serial connection
        if self.serial_conn:
            self.serial_conn.close()
            print("✅ Serial connection closed")
        
        print("✅ Hardware cleanup complete")

