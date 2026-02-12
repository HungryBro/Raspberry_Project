"""
config.py - ค่าคงที่ทั้งหมดของระบบ
แก้ไขค่า PIN หรือค่าต่างๆ ได้ที่ไฟล์นี้ไฟล์เดียว
"""

from gpiozero.pins.lgpio import LGPIOFactory  # ใช้สำหรับ Raspberry Pi 5

import warnings
warnings.filterwarnings("ignore")  # ปิดการแจ้งเตือน Warning

# --- Pin Factory สำหรับ Pi 5 ---
factory = LGPIOFactory()

# --- Servo ---
SERVO_PIN = 19                     # ขา GPIO ที่ต่อกับ Servo (Pin 33)
SERVO_MIN_PULSE = 0.0005           # Pulse Width ต่ำสุด 0.5ms
SERVO_MAX_PULSE = 0.0025           # Pulse Width สูงสุด 2.5ms
SERVO_MIN_ANGLE = -90              # มุมต่ำสุดที่ Servo หมุนได้ (องศา)
SERVO_MAX_ANGLE = 90               # มุมสูงสุดที่ Servo หมุนได้ (องศา)

# --- Servo Scan Range (ช่วงที่กล้องมองเห็น) ---
SERVO_SCAN_MIN = 57                # มุมเริ่ม scan (องศา) = 90 - 33
SERVO_SCAN_MAX = 123               # มุมสุด scan (องศา) = 90 + 33
SERVO_STEP_DELAY = 0.02            # Delay ต่อ step (วินาที) ยิ่งมากยิ่งช้า
SERVO_SETTLE_TIME = 0.3            # เวลารอให้ Servo เสถียรหลังตั้งมุม (วินาที)

# --- Camera FOV & Sector ---
FOV_H_DEG = 66                     # มุมมองกล้องแนวนอน (องศา)
NUM_SECTORS = 6                    # จำนวน Sector ที่แบ่ง
SECTOR_DEG = FOV_H_DEG // NUM_SECTORS  # ขนาดแต่ละ Sector (11 องศา)

# --- ADC (ADS1115) ---
ADC_CHANNEL = 0                    # ช่อง Analog ที่ใช้อ่านค่า (A0)
ADC_INTERVAL = 0.3                 # อ่านค่าแรงดันทุกๆ 0.3 วินาที

# --- Motor Driver ---
MOTOR_PWM_PIN = 12                 # ขา GPIO ควบคุมความเร็ว Motor ด้วย PWM (Pin 32)
MOTOR_AIN1_PIN = 17                # ขา GPIO ควบคุมทิศทาง Motor ขา 1 (Pin 11)
MOTOR_AIN2_PIN = 27                # ขา GPIO ควบคุมทิศทาง Motor ขา 2 (Pin 13)

# --- Camera (Pi Camera Module 3) ---
CAMERA_WIDTH = 640                 # ความกว้างภาพ (พิกเซล)
CAMERA_HEIGHT = 480                # ความสูงภาพ (พิกเซล)

# --- Face Detection (MediaPipe) ---
FACE_MODEL = 1                     # โมเดลตรวจจับใบหน้า (0 = ใกล้ 2m, 1 = ไกล 5m)
FACE_CONFIDENCE = 0.5              # ค่าความมั่นใจขั้นต่ำ (0.0-1.0)
