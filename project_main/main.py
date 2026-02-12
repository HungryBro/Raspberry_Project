"""
main.py - ไฟล์หลัก
Smart Fan: Anti-Direct-Blow System
กล้อง + Servo Scan + ADC Motor + Face Detection (หลบคนอัตโนมัติ)

วิธีใช้งาน:
    cd project_main
    python3 main.py
"""

import threading
import servo_module
import adc_module
import camera_module
import shared_state


def main():
    print("=" * 60)
    print("  Smart Fan: Anti-Direct-Blow System")
    print("=" * 60)
    print("  1. กล้อง Pi Camera Module 3 (rpicam-vid)")
    print("  2. Face Detection (MediaPipe)")
    print("  3. Servo Scan 57° → 123° (6 Sectors)")
    print("  4. ADC ควบคุม Motor:")
    print("     - < 1.0V     = 0%")
    print("     - 1.0-1.6V   = 30%")
    print("     - 1.6-2.0V   = 60%")
    print("     - > 2.0V     = 100%")
    print("  5. ⚠️ No-Go Zone: พัดลมหยุดเมื่อหันไปทิศคน!")
    print("=" * 60)
    print("  กด 'q' บนหน้าต่างกล้องเพื่อออก")
    print("=" * 60)
    
    # สร้าง Threads
    adc_motor_thread = threading.Thread(target=adc_module.adc_motor_worker, daemon=True)
    servo_thread = threading.Thread(target=servo_module.servo_worker, daemon=True)
    
    try:
        # เริ่ม threads
        adc_motor_thread.start()
        servo_thread.start()
        
        # รันกล้องใน main thread (OpenCV ต้องการ main thread)
        camera_module.camera_worker()
        
    except KeyboardInterrupt:
        print("\n[Main] กด Ctrl+C - กำลังหยุดโปรแกรม...")
    finally:
        shared_state.stop_event.set()
        adc_motor_thread.join(timeout=2)
        servo_thread.join(timeout=2)
        print("[Main] ปิดโปรแกรมเรียบร้อย")


if __name__ == "__main__":
    main()
