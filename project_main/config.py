"""
config.py - ค่าคงที่ทั้งหมดของระบบ
แก้ไขค่า PIN หรือค่าต่างๆ ได้ที่ไฟล์นี้ไฟล์เดียว
"""

from gpiozero.pins.lgpio import LGPIOFactory

import warnings
warnings.filterwarnings("ignore")

# --- Pin Factory สำหรับ Pi 5 ---
factory = LGPIOFactory()

# --- Servo ---
SERVO_PIN = 18
SERVO_MIN_PULSE = 0.0005
SERVO_MAX_PULSE = 0.0025
SERVO_MIN_ANGLE = -90
SERVO_MAX_ANGLE = 90
SERVO_ANGLES = [90, 0, -90]       # ลำดับมุมที่จะหมุน
SERVO_DELAY = 1.5                  # หน่วง (วินาที) ก่อนเปลี่ยนมุม
SERVO_SETTLE_TIME = 0.3            # หน่วง (วินาที) หลังตั้งมุมใหม่

# --- ADC (ADS1115) ---
ADC_CHANNEL = 0
ADC_INTERVAL = 0.3                 # อ่านค่าทุกๆ (วินาที)

# --- Motor Driver ---
MOTOR_PWM_PIN = 12
MOTOR_AIN1_PIN = 17
MOTOR_AIN2_PIN = 27

# --- Camera ---
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# --- Face Detection ---
FACE_MODEL = 0                     # 0 = short range (2m), 1 = full range (5m)
FACE_CONFIDENCE = 0.5
