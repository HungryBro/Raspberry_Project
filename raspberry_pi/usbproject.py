import cv2
import time
import numpy as np
from gpiozero import AngularServo, PWMOutputDevice, DigitalOutputDevice
from gpiozero.pins.lgpio import LGPIOFactory

# 1. ตั้งค่า Pin Factory (Pi 5)
factory = LGPIOFactory()

# 2. ตั้งค่า Hardware
# Servo GPIO 18
servo = AngularServo(18, min_angle=0, max_angle=180, 
                     min_pulse_width=0.0005, max_pulse_width=0.0025, pin_factory=factory)

# Motor Driver GPIO 12, 17, 27
pwm_a = PWMOutputDevice(12, pin_factory=factory) 
ain1 = DigitalOutputDevice(17, pin_factory=factory)
ain2 = DigitalOutputDevice(27, pin_factory=factory)

# 3. เตรียมระบบจับใบหน้า (Haar Cascade)
# --- [จุดที่แก้] อ่านไฟล์จากโฟลเดอร์ปัจจุบันโดยตรง ---
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# เช็กว่าโหลดไฟล์ได้จริงไหม
if face_cascade.empty():
    print("!!! Error: หาไฟล์ haarcascade_frontalface_default.xml ไม่เจอ !!!")
    print("คำแนะนำ: รันคำสั่ง wget เพื่อโหลดไฟล์ก่อนนะครับ")
    exit()

# 4. ตัวแปรควบคุม
fan_angle = 90
step = 2        
direction = 1   
buffer = 40     

def fan_control(speed, action="RUN"):
    if action == "RUN":
        ain1.on()
        ain2.off()
        pwm_a.value = speed
    else:
        ain1.on()
        ain2.on()
        pwm_a.value = 0

# 5. เริ่มต้นกล้อง USB
print("--- เริ่มต้นระบบ Face Tracking Fan ---")
cap = cv2.VideoCapture(0) # ถ้าภาพไม่มา ลองเปลี่ยนเป็น 1 หรือ 2
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("!!! ไม่เจอกล้อง USB !!!")
    exit()

try:
    while True:
        success, frame = cap.read()
        if not success: continue

        # กลับด้านภาพ
        frame = cv2.flip(frame, 1)

        # แปลงขาวดำเพื่อตรวจจับ
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # ค้นหาใบหน้า
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        person_x_angle = -1 

        # ถ้าเจอหน้า
        if len(faces) > 0:
            # เอาหน้าแรกที่เจอ
            (x, y, w, h) = faces[0]
            center_x = x + (w // 2)
            center_y = y + (h // 2)

            # แปลงตำแหน่ง X เป็นองศา
            img_w = frame.shape[1]
            person_x_angle = int((center_x / img_w) * 180)

            # วาดกรอบ
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
                # Logic พัดลม
        fan_angle += (step * direction)
        if fan_angle >= 180:
            fan_angle = 180
            direction = -1
        elif fan_angle <= 0:
            fan_angle = 0
            direction = 1

        servo.angle = fan_angle

        # หยุดเมื่อเจอหน้า
        if person_x_angle != -1 and abs(fan_angle - person_x_angle) < buffer:
            fan_control(0, action="BRAKE")
            status = "STOP (Face Found)"
            color = (0, 0, 255)
        else:
            fan_control(0.8)
            status = "SCANNING"
            color = (0, 255, 0)

        cv2.putText(frame, f"Fan: {fan_angle} | {status}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        cv2.imshow('Face Tracking Fan', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    print("Closing...")
    fan_control(0, action="BRAKE")
    cap.release()
    cv2.destroyAllWindows()