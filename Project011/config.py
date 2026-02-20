"""
config.py - ค่าคงที่ทั้งหมดของระบบ Project011 (Roboflow Cloud Version)
Smart Fan ควบคุมด้วย Sign Language (Roboflow Inference) + Face Safety

ใช้ AI 2 ตัว:
  - Roboflow Cloud API → ตรวจจับท่ามือ ASL → ควบคุม Motor + Servo
  - MediaPipe Face     → ตรวจจับหน้า       → หยุด Motor ฉุกเฉิน

แก้ไขค่า PIN หรือค่าต่างๆ ได้ที่ไฟล์นี้ไฟล์เดียว
"""

from gpiozero.pins.lgpio import LGPIOFactory  # ใช้สำหรับ Raspberry Pi 5

import warnings
warnings.filterwarnings("ignore")

# --- Pin Factory สำหรับ Pi 5 ---
factory = LGPIOFactory()

# --- Servo ---
SERVO_PIN = 19
SERVO_MIN_PULSE = 0.0005
SERVO_MAX_PULSE = 0.0025*3/4
SERVO_MIN_ANGLE = -90
SERVO_MAX_ANGLE = 90
SERVO_SETTLE_TIME = 0.1
SERVO_STEP = 5

# --- Motor Driver ---
MOTOR_PWM_PIN = 12
MOTOR_AIN1_PIN = 17
MOTOR_AIN2_PIN = 27

# --- Camera (Pi Camera Module 3) ---
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# --- Face Detection (MediaPipe) ---
FACE_MODEL = 1
FACE_CONFIDENCE = 0.5

# --- Roboflow Cloud API ---
ROBOFLOW_API_KEY = "YOUR_API_KEY"  # ใส่ API Key ของคุณที่นี่
ROBOFLOW_MODEL_ID = "extrdb/2"
SIGN_CONFIDENCE = 0.50
GESTURE_INTERVAL = 0.3

# === Frame Skipping (Optimization) ===
SKIP_FACE = 5       # ตรวจหน้าทุกๆ 5 เฟรม
SKIP_CLOUD = 5      # ส่งภาพไป Cloud ทุกๆ 5 เฟรม (ประหยัด Req + ลด Latency)

# === Mapping: Sign Language → Motor Speed ===
SIGN_SPEED_MAP = {
    "s": 0.0,   # กำปั้น → Motor 0%
    "o": 0.0,   # วงกลม → Motor 0%
    "d": 0.3,   # ชี้ 1 นิ้ว → Motor 30%
    "x": 0.3,   # งอนิ้วชี้ → Motor 30%
    "v": 0.6,   # ชู 2 นิ้ว → Motor 60%
    "w": 1.0,   # ชู 3 นิ้ว → Motor 100%
}

# === Mapping: Sign Language → Servo ===
# t (กำมือสอดนิ้วโป้ง) / y (ชูโป้ง+ก้อย) -> Servo Control
SERVO_RIGHT_SIGNS = ["t"]   # หมุนขวา
SERVO_LEFT_SIGNS = ["y"]    # หมุนซ้าย
