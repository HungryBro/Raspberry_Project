"""
config.py - ค่าคงที่ทั้งหมดของระบบ
แก้ไขค่า PIN หรือค่าต่างๆ ได้ที่ไฟล์นี้ไฟล์เดียว
"""

from gpiozero.pins.lgpio import LGPIOFactory  # ใช้สำหรับ Raspberry Pi 5

import warnings
warnings.filterwarnings("ignore")  # ปิดการแจ้งเตือน Warning

# --- Pin Factory สำหรับ Pi 5 ---
factory = LGPIOFactory()  # สร้าง Pin Factory สำหรับควบคุม GPIO บน Pi 5

# --- Servo ---
SERVO_PIN = 19                     # ขา GPIO ที่ต่อกับสาย Signal ของ Servo (Pin 35)
SERVO_MIN_PULSE = 0.0005           # Pulse Width ต่ำสุด 0.5ms (กำหนดมุมต่ำสุด)
SERVO_MAX_PULSE = 0.0025*3/4       # Pulse Width สูงสุด 2.5ms (กำหนดมุมสูงสุด)
SERVO_MIN_ANGLE = -90              # มุมต่ำสุดที่ Servo หมุนได้ (องศา)
SERVO_MAX_ANGLE = 90               # มุมสูงสุดที่ Servo หมุนได้ (องศา)
SERVO_SETTLE_TIME = 0.1            # เวลาหน่วง (วินาที) รอให้ Servo เสถียร
SERVO_STEP = 5                     # องศาต่อครั้งสำหรับ Jog ด้วยท่ามือ

# --- Motor Driver ---
MOTOR_PWM_PIN = 12                 # ขา GPIO ควบคุมความเร็ว Motor ด้วย PWM (Pin 32)
MOTOR_AIN1_PIN = 17                # ขา GPIO ควบคุมทิศทาง Motor ขา 1 (Pin 11)
MOTOR_AIN2_PIN = 27                # ขา GPIO ควบคุมทิศทาง Motor ขา 2 (Pin 13)

# --- Camera (Pi Camera Module 3) ---
CAMERA_WIDTH = 640                 # ความกว้างภาพ (พิกเซล)
CAMERA_HEIGHT = 480                # ความสูงภาพ (พิกเซล)

# --- Face Detection ---
FACE_MODEL = 1                     # โมเดลตรวจจับใบหน้า (0 = ระยะใกล้ 2m, 1 = ระยะไกล 5m)
FACE_CONFIDENCE = 0.5              # ค่าความมั่นใจขั้นต่ำ (0.0-1.0)

# --- Hand Detection ---
HAND_MODEL_COMPLEXITY = 0          # ความซับซ้อนโมเดลมือ (0 = เบา/เร็ว, 1 = หนัก/แม่น)
HAND_CONFIDENCE = 0.6              # ค่าความมั่นใจขั้นต่ำตรวจจับมือ
HAND_TRACKING_CONFIDENCE = 0.5     # ค่าความมั่นใจติดตามมือ
GESTURE_INTERVAL = 0.3             # หน่วงเวลา Servo Jog ป้องกันกระตุก (วินาที)
