"""
config.py - ค่าคงที่ทั้งหมดของระบบ Project011
Smart Fan ควบคุมด้วย Sign Language (Roboflow extrdb/2 model)

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

# --- Face Detection (MediaPipe) ---
FACE_MODEL = 1                     # โมเดลตรวจจับใบหน้า (0 = ระยะใกล้ 2m, 1 = ระยะไกล 5m)
FACE_CONFIDENCE = 0.5              # ค่าความมั่นใจขั้นต่ำ (0.0-1.0)

# --- Roboflow Sign Language Detection ---
ROBOFLOW_API_KEY = "ekTKDcHd22SkTXRleX5r"   # Roboflow API Key
ROBOFLOW_MODEL_ID = "extrdb/2"               # Model ID (ASL hand sign, 27 classes)
SIGN_CONFIDENCE = 0.70                       # ค่าความมั่นใจขั้นต่ำ
GESTURE_INTERVAL = 0.3                       # หน่วงเวลา Servo Jog ป้องกันกระตุก (วินาที)

# === Mapping: Sign Language → Action ===
# ท่ามือภาษามือ ASL → การควบคุมพัดลม/Servo
#
#   ท่า S (กำปั้น)      → Motor 0%     (หยุด)
#   ท่า O (วงกลม)       → Motor 0%     (หยุด)
#   ท่า D (ชี้ 1 นิ้ว)  → Motor 30%
#   ท่า X (งอนิ้วชี้)   → Motor 30%
#   ท่า V (ชู 2 นิ้ว)   → Motor 60%
#   ท่า W (ชู 3 นิ้ว)   → Motor 100%
#   ท่า T (กำ+หัวแม่มือ)→ Servo +5°
#   ท่า Y (ชากา)        → Servo -5°

SIGN_SPEED_MAP = {
    "s": 0.0,   # กำปั้น → Motor 0%
    "o": 0.0,   # วงกลม → Motor 0%
    "d": 0.3,   # ชี้ 1 นิ้ว → Motor 30%
    "x": 0.3,   # งอนิ้วชี้ → Motor 30%
    "v": 0.6,   # ชู 2 นิ้ว → Motor 60%
    "w": 1.0,   # ชู 3 นิ้ว → Motor 100%
}

# ท่าสำหรับ Servo Jog
SERVO_RIGHT_SIGNS = ["t"]    # Servo +5° (หมุนขวา)
SERVO_LEFT_SIGNS = ["y"]     # Servo -5° (หมุนซ้าย)
