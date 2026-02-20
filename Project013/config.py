"""
config.py - ค่าคงที่ทั้งหมดของระบบ Project013 (Modified: No Cross-Check)
Smart Fan ควบคุมด้วย YOLO + MediaPipe (Dual AI)

ใช้ AI 2 ตัวแยกหน้าที่ชัดเจน:
  - YOLO (local model) → ตรวจจับท่ามือ ASL   → ควบคุม Motor (เต็มตัว)
  - MediaPipe Hands   → ตรวจจับนิ้ว          → ควบคุม Servo (หัวแม่มือ/ก้อย)
  - MediaPipe Face    → ตรวจจับหน้า          → หยุด Motor ฉุกเฉิน

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

# --- MediaPipe Hands ---
HAND_MAX_NUM = 1                    # จำนวนมือสูงสุดที่ตรวจจับ
HAND_CONFIDENCE = 0.7               # ค่าความมั่นใจ MediaPipe Hands
HAND_TRACKING = 0.5                 # ค่า tracking confidence

# --- Local YOLO Model (train เองจาก extrdb v2 dataset) ---
YOLO_MODEL_PATH = "models/best.pt"
YOLO_CONFIDENCE = 0.70
YOLO_IMG_SIZE = 640
GESTURE_INTERVAL = 0.3

# === Frame Skipping (Optimization) ===
# ลดภาระ CPU เพื่อเพิ่ม FPS
SKIP_FACE = 5       # ตรวจหน้าทุกๆ 5 เฟรม
SKIP_YOLO = 5       # ตรวจ YOLO ทุกๆ 5 เฟรม
SKIP_HANDS = 3      # ตรวจนิ้วทุกๆ 3 เฟรม

# === Mapping: Sign Language → Motor Speed (YOLO Only) ===
SIGN_SPEED_MAP = {
    "s": 0.0,   # กำปั้น → Motor 0%
    "o": 0.0,   # วงกลม → Motor 0%
    "d": 0.3,   # ชี้ 1 นิ้ว → Motor 30%
    "x": 0.3,   # งอนิ้วชี้ → Motor 30%
    "v": 0.6,   # ชู 2 นิ้ว → Motor 60%
    "w": 1.0,   # ชู 3 นิ้ว → Motor 100%
}

# === Mapping: MediaPipe Finger → Servo ===
# หัวแม่มือชูอย่างเดียว (นิ้วอื่นงอ) → Servo +5° (หมุนขวา)
# ก้อยชูอย่างเดียว (นิ้วอื่นงอ)       → Servo -5° (หมุนซ้าย)
