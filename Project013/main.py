"""
main.py - ไฟล์หลัก
Smart AI Fan: Dual AI Detection (YOLO + MediaPipe)

ใช้ AI 3 ตัวพร้อมกัน:
  1. YOLO (local model)  → ตรวจจับท่ามือ ASL (primary)
  2. MediaPipe Hands     → นับนิ้ว 21 landmarks (secondary)
  3. MediaPipe Face      → ตรวจจับหน้า (safety)

วิธีใช้งาน:
    cd Project013
    python3 main.py
"""

import threading
import servo_module
import camera_module
import motor_module
import shared_state


def main():
    print("=" * 60)
    print("  Smart AI Fan: Dual AI Detection")
    print("  YOLO (Sign Language) + MediaPipe (Finger Count)")
    print("=" * 60)
    print("  AI #1: YOLO Local Model (primary)")
    print("    S,O = Motor 0% | D,X = Motor 30%")
    print("    V   = Motor 60%| W   = Motor 100%")
    print("    T   = Servo +5 | Y   = Servo -5")
    print("  AI #2: MediaPipe Hands (backup)")
    print("    0f = 0% | 1f = 30% | 2f = 60% | 3f = 100%")
    print("    4f = Servo +5 | 5f = Servo -5")
    print("  AI #3: MediaPipe Face (safety)")
    print("    เจอหน้าคน -> Motor หยุดทันที!")
    print("=" * 60)
    print("  Cross-Check Mode:")
    print("    DUAL CONFIRM = ทั้ง 2 AI เห็นตรงกัน (มั่นใจสูง)")
    print("    YOLO         = YOLO อย่างเดียว")
    print("    MP BACKUP    = MediaPipe อย่างเดียว")
    print("=" * 60)
    print("  กด 'q' บนหน้าต่างกล้องเพื่อออก")
    print("=" * 60)

    motor_thread = threading.Thread(target=motor_module.motor_worker, daemon=True)
    servo_thread = threading.Thread(target=servo_module.servo_worker, daemon=True)

    try:
        motor_thread.start()
        servo_thread.start()
        camera_module.camera_worker()

    except KeyboardInterrupt:
        print("\n[Main] กด Ctrl+C - กำลังหยุดโปรแกรม...")
    finally:
        shared_state.stop_event.set()
        motor_thread.join(timeout=2)
        servo_thread.join(timeout=2)
        print("[Main] ปิดโปรแกรมเรียบร้อย")


if __name__ == "__main__":
    main()
