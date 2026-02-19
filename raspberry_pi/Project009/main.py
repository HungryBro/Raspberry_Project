"""
main.py - ไฟล์หลัก
<<<<<<< HEAD
Smart AI Fan: Camera + Servo + Motor + Face Detection + Hand Gesture

รองรับ 2 โหมด (เปลี่ยนที่ config.py → CONTROL_MODE):
  - "adc"     : Potentiometer ควบคุม Motor + Servo ส่ายอัตโนมัติ
  - "gesture" : ท่ามือควบคุม Motor + Servo Jog
=======
รวม Camera + Servo + ADC + Motor + Face Detection
⚡ ระบบจะเริ่มทำงานเมื่อกด Switch (ADC voltage > 1.0V)
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77

วิธีใช้งาน:
    cd Project009
    python3 main.py
"""

<<<<<<< HEAD
import threading
import servo_module
import camera_module
import motor_module
import shared_state
from config import CONTROL_MODE
=======
import time
import threading
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from config import ADC_CHANNEL
import servo_module
import adc_module
import camera_module
import shared_state


def wait_for_switch():
    """รอจนกว่าจะกด Switch (ADC voltage > 1.0V)"""
    print("\n⏳ รอกด Switch เพื่อเริ่มระบบ...")
    print("   (ADC จะอ่านค่าแรงดัน ถ้า > 1.0V = Switch ON)\n")
    
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        ads.gain = 1
        chan = AnalogIn(ads, ADC_CHANNEL)
        
        while not shared_state.stop_event.is_set():
            voltage = chan.voltage
            print(f"\r   Voltage: {voltage:.2f}V - รอกด Switch...", end="", flush=True)
            
            if voltage >= 1.0:
                print(f"\n\n✅ Switch ON! (Voltage: {voltage:.2f}V)")
                print("🚀 เริ่มระบบทั้งหมด...\n")
                i2c.deinit()
                return True
            
            time.sleep(0.3)
        
        i2c.deinit()
        return False
        
    except Exception as e:
        print(f"\n❌ ADC Error: {e}")
        print("   ไม่สามารถอ่านค่า ADC ได้ - เริ่มระบบโดยไม่รอ Switch")
        return True
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77


def main():
    print("=" * 60)
<<<<<<< HEAD
    print("  Smart AI Fan: Safety & Gesture Control")
    print("=" * 60)

    if CONTROL_MODE == "gesture":
        print("  📌 โหมด: GESTURE (ท่ามือ)")
        print("  1. กล้อง + Face Detection + Hand Gesture (MediaPipe)")
        print("  2. ✋ นิ้วชี้/กลาง/นาง → ควบคุมความเร็ว Motor")
        print("     - กำปั้น     = 0%")
        print("     - 1 นิ้ว     = 30%")
        print("     - 2 นิ้ว     = 60%")
        print("     - 3 นิ้ว     = 100%")
        print("  3. 👍 หัวแม่มือ → Servo +5°")
        print("  4. 🤙 นิ้วก้อย   → Servo -5°")
    else:
        print("  📌 โหมด: ADC (Potentiometer)")
        print("  1. กล้อง + Face Detection (MediaPipe)")
        print("  2. Servo หมุน 0° -> 90° -> 180°")
        print("  3. ADC ควบคุม Motor:")
        print("     - < 1.0V     = 0%")
        print("     - 1.0-1.6V   = 30%")
        print("     - 1.6-2.0V   = 60%")
        print("     - > 2.0V     = 100%")

    print("  ⚠️  เจอหน้าคน -> Motor หยุดทันที!")
    print("=" * 60)
    print("  กด 'q' บนหน้าต่างกล้องเพื่อออก")
    print("=" * 60)

    # === สร้าง Threads ตามโหมด ===
    threads = []

    if CONTROL_MODE == "gesture":
        # Mode Gesture: Motor thread + Servo Gesture thread
        motor_thread = threading.Thread(target=motor_module.motor_worker, daemon=True)
        servo_thread = threading.Thread(target=servo_module.servo_gesture_worker, daemon=True)
        threads.extend([motor_thread, servo_thread])
    else:
        # Mode ADC: ADC+Motor thread + Servo Auto-Sweep thread
        import adc_module
        adc_motor_thread = threading.Thread(target=adc_module.adc_motor_worker, daemon=True)
        servo_thread = threading.Thread(target=servo_module.servo_worker, daemon=True)
        threads.extend([adc_motor_thread, servo_thread])

    try:
        # เริ่ม threads
        for t in threads:
            t.start()

        # รันกล้องใน main thread (OpenCV ต้องการ main thread)
        camera_module.camera_worker()

=======
    print("  Smart Fan: Camera + Servo + ADC + Motor + Face Detection")
    print("=" * 60)
    print("  1. กล้อง + Face Detection (MediaPipe)")
    print("  2. Servo หมุนตาม SERVO_ANGLES")
    print("  3. ADC ควบคุม Motor:")
    print("     - < 1.0V     = 0%")
    print("     - 1.0-1.6V   = 30%")
    print("     - 1.6-2.0V   = 60%")
    print("     - > 2.0V     = 100%")
    print("  4. ⚠️ เจอหน้าคน -> Motor หยุดทันที!")
    print("=" * 60)
    print("  กด 'q' บนหน้าต่างกล้องเพื่อออก")
    print("=" * 60)
    
    # รอกด Switch ก่อนเริ่มระบบ
    if not wait_for_switch():
        print("[Main] ยกเลิกการเริ่มระบบ")
        return
    
    # สร้าง Threads
    adc_motor_thread = threading.Thread(target=adc_module.adc_motor_worker, daemon=True)
    servo_thread = threading.Thread(target=servo_module.servo_worker, daemon=True)
    
    try:
        # เริ่ม threads
        adc_motor_thread.start()
        servo_thread.start()
        
        # รันกล้องใน main thread (OpenCV ต้องการ main thread)
        camera_module.camera_worker()
        
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
    except KeyboardInterrupt:
        print("\n[Main] กด Ctrl+C - กำลังหยุดโปรแกรม...")
    finally:
        shared_state.stop_event.set()
<<<<<<< HEAD
        for t in threads:
            t.join(timeout=2)
=======
        adc_motor_thread.join(timeout=2)
        servo_thread.join(timeout=2)
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
        print("[Main] ปิดโปรแกรมเรียบร้อย")


if __name__ == "__main__":
    main()
