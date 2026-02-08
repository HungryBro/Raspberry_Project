import cv2
import threading
from gpiozero import AngularServo
from time import sleep

# --- ส่วนตั้งค่า Servo ---
SERVO_PIN = 18

# ปรับ Pulse ให้กว้างหน่อยสำหรับ MG996R
MIN_PULSE = 0.0005
MAX_PULSE = 0.0025

stop_event = threading.Event()

def servo_worker():
    try:
        # --- แก้ไขตรงนี้: กำหนดมุมเป็น 0 ถึง 180 ---
        servo = AngularServo(SERVO_PIN, 
                             min_angle=0, 
                             max_angle=180,
                             min_pulse_width=MIN_PULSE, 
                             max_pulse_width=MAX_PULSE)

        print("[Servo] เริ่มทำงาน (0 <-> 180)...")

        while not stop_event.is_set():
            # หมุนไปที่ 0 องศา
            # print("Angle: 0")
            servo.angle = 0
            sleep(2)
            if stop_event.is_set(): break 

            # หมุนไปที่ 180 องศา
            # print("Angle: 180")
            servo.angle = 180
            sleep(2)
            if stop_event.is_set(): break

    except Exception as e:
        print(f"เกิดข้อผิดพลาดที่ Servo: {e}")

def main():
    # 1. เริ่ม Thread Servo
    t = threading.Thread(target=servo_worker)
    t.start()

    # 2. เปิดกล้อง
    cap = cv2.VideoCapture(0)
    
    # ลดขนาดภาพลงหน่อยเพื่อให้ลื่นขึ้น (Optional)
    cap.set(3, 640) # Width
    cap.set(4, 480) # Height

    if not cap.isOpened():
        print("ไม่สามารถเปิดกล้องได้")
        stop_event.set()
        return

    print("กด 'q' เพื่อออก")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            cv2.imshow('USB Camera', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        pass
    finally:
        print("ปิดโปรแกรม...")
        stop_event.set()
        t.join()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()