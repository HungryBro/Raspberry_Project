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
SERVO_MAX_PULSE = 0.0025           # Pulse Width สูงสุด 2.5ms (กำหนดมุมสูงสุด)
SERVO_MIN_ANGLE = -90              # มุมต่ำสุดที่ Servo หมุนได้ (องศา)
SERVO_MAX_ANGLE = 90               # มุมสูงสุดที่ Servo หมุนได้ (องศา)
SERVO_ANGLES = [0,90,180]     # ลำดับมุมที่ Servo จะหมุนไป วนลูป
SERVO_DELAY = 0.5                  # เวลาหน่วง (วินาที) ก่อนเปลี่ยนมุมถัดไป
SERVO_SETTLE_TIME = 0.1            # เวลาหน่วง (วินาที) รอให้ Servo เสถียรหลังตั้งมุมใหม่

# --- ADC (ADS1115) ---
ADC_CHANNEL = 0                    # ช่อง Analog ที่ใช้อ่านค่า (A0)
ADC_INTERVAL = 0.3                 # อ่านค่าแรงดันทุกๆ 0.3 วินาที

# --- Motor Driver ---
MOTOR_PWM_PIN = 12                 # ขา GPIO ควบคุมความเร็ว Motor ด้วย PWM (Pin 32)
MOTOR_AIN1_PIN = 17                # ขา GPIO ควบคุมทิศทาง Motor ขา 1 (Pin 11)
MOTOR_AIN2_PIN = 27                # ขา GPIO ควบคุมทิศทาง Motor ขา 2 (Pin 13)

# --- Camera ---
CAMERA_INDEX = 0                   # หมายเลขกล้อง USB (0 = กล้องตัวแรก)
CAMERA_WIDTH = 640                 # ความกว้างภาพ (พิกเซล)
CAMERA_HEIGHT = 480                # ความสูงภาพ (พิกเซล)

# --- Face Detection ---
FACE_MODEL = 0.25                     # โมเดลตรวจจับใบหน้า (0 = ระยะใกล้ 2m, 1 = ระยะไกล 5m)
FACE_CONFIDENCE = 0.5              # ค่าความมั่นใจขั้นต่ำ (0.0-1.0) ยิ่งสูงยิ่งแม่นแต่ตรวจจับยากขึ้น

