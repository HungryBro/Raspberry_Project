"""
main.py - ไฟล์หลัก
Smart AI Fan: Camera + Servo + Motor + Face Detection + Sign Language (Roboflow)

วิธีใช้งาน:
    cd Project011
    python3 main.py
"""

import threading
import servo_module
import camera_module
import motor_module
import shared_state


def main():
    print("=" * 60)
    print("  Smart AI Fan: Sign Language Control")
    print("  (Roboflow extrdb/2 - ASL Hand Signs)")
    print("=" * 60)
    print("  1. กล้อง + Face Detection (MediaPipe)")
    print("  2. Sign Language Detection (Roboflow AI)")
    print("     - ✊ S (กำปั้น)       = Motor 0%")
    print("     - 👌 O (วงกลม)        = Motor 0%")
    print("     - ☝️  D (ชี้ 1 นิ้ว)   = Motor 30%")
    print("     - 🤞 X (งอนิ้วชี้)    = Motor 30%")
    print("     - ✌️  V (ชู 2 นิ้ว)    = Motor 60%")
    print("     - 🤟 W (ชู 3 นิ้ว)    = Motor 100%")
    print("     - 👍 T (กำ+หัวแม่มือ) = Servo +5°")
    print("     - 🤙 Y (ชากา)         = Servo -5°")
    print("  ⚠️  เจอหน้าคน -> Motor หยุดทันที!")
    print("=" * 60)
    print("  กด 'q' บนหน้าต่างกล้องเพื่อออก")
    print("=" * 60)

    # สร้าง Threads
    motor_thread = threading.Thread(target=motor_module.motor_worker, daemon=True)
    servo_thread = threading.Thread(target=servo_module.servo_worker, daemon=True)

    try:
        # เริ่ม threads
        motor_thread.start()
        servo_thread.start()

        # รันกล้องใน main thread (OpenCV ต้องการ main thread)
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
