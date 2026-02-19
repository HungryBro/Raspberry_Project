import cv2
import threading
from gpiozero import AngularServo
from time import sleep

# --- ส่วนตั้งค่า Servo ---
SERVO_PIN = 18
# MG996R มักใช้ช่วง 0.5ms - 2.5ms
MIN_PULSE = 0.0005
MAX_PULSE = 0.0025

# ตัวแปรสำหรับหยุดการทำงานของ Thread เมื่อปิดโปรแกรม
stop_event = threading.Event()

def servo_worker():
    """ฟังก์ชันสำหรับควบคุม Servo ให้ทำงานแยกต่างหาก (Background Thread)"""
    try:
        # สร้าง Object Servo ภายใน Thread
        servo = AngularServo(SERVO_PIN, 
                             min_angle=-90, 
                             max_angle=90,
                             min_pulse_width=MIN_PULSE, 
                             max_pulse_width=MAX_PULSE)

        print("[Servo] เริ่มทำงาน...")

        while not stop_event.is_set():
            # หมุนไป 90
            servo.angle = 90
            sleep(2)
            if stop_event.is_set(): break 

            # หมุนไป 0
            servo.angle = 0
            sleep(2)
            if stop_event.is_set(): break

            # หมุนไป -90
            servo.angle = -90
            sleep(2)

    except Exception as e:
        print(f"เกิดข้อผิดพลาดที่ Servo: {e}")
    finally:
        print("[Servo] หยุดการทำงาน")
        # หมายเหตุ: gpiozero จะ cleanup ให้เองเมื่อ object ถูกทำลาย

# --- ส่วนหลัก (Main) สำหรับเปิดกล้อง ---
def main():
    # 1. เริ่ม Thread ของ Servo
    t = threading.Thread(target=servo_worker)
    t.start()

    # 2. เปิดกล้อง (0 คือกล้องตัวแรก)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("ไม่สามารถเปิดกล้องได้")
        stop_event.set() # สั่งหยุด Servo ด้วยถ้ากล้องเปิดไม่ได้
        return

    print("กด 'q' ที่หน้าต่างกล้องเพื่อออกจากโปรแกรม")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("อ่านเฟรมภาพไม่สำเร็จ")
                break

            # แสดงผลภาพ
            cv2.imshow('USB Camera', frame)

            # กด q เพื่อออก
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    finally:
        # 3. ขั้นตอนการปิดโปรแกรม (Cleanup)
        print("กำลังปิดโปรแกรม...")
        stop_event.set()  # ส่งสัญญาณให้ Thread Servo หยุด
        t.join()          # รอให้ Thread Servo หยุดจริงๆ
        cap.release()     # คืนค่ากล้อง
        cv2.destroyAllWindows() # ปิดหน้าต่าง

if __name__ == "__main__":
    main()