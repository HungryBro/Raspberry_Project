"""
shared_state.py - ตัวแปรร่วมระหว่าง Thread ทั้งหมด
ใช้สำหรับระบบควบคุมด้วย Sign Language Detection
"""

import threading

# --- Events ---
stop_event = threading.Event()       # สำหรับหยุดโปรแกรมทั้งหมด
face_detected = threading.Event()    # แจ้งเมื่อเจอหน้าคน

# --- Locks ---
data_lock = threading.Lock()         # ป้องกัน race condition ข้อมูลทั่วไป
motor_lock = threading.Lock()        # ป้องกัน race condition ตัว Motor

# --- Shared Data ---
current_motor_speed = 0              # ความเร็ว Motor ปัจจุบัน (0-100 %)
current_servo_angle = 0              # มุม Servo ปัจจุบัน (องศา)
target_speed = 0.0                   # ความเร็ว Motor เป้าหมาย (0.0 - 1.0)
target_servo_angle = 0               # มุม Servo เป้าหมาย (องศา)
finger_count = 0                     # จำนวนนิ้วที่ตรวจจับได้


# =====================================================
#  Getter / Setter แบบ thread-safe
# =====================================================

def get_status():
    """อ่านค่าสถานะทั้งหมดแบบ thread-safe"""
    with data_lock:
        return {
            "motor_speed": current_motor_speed,
            "servo_angle": current_servo_angle,
            "face": face_detected.is_set(),
            "target_speed": target_speed,
            "target_servo_angle": target_servo_angle,
            "finger_count": finger_count,
        }


def set_motor_speed(value):
    """อัปเดตค่าความเร็ว Motor (แสดงผลเป็น %)"""
    global current_motor_speed
    with data_lock:
        current_motor_speed = value


def set_servo_angle(value):
    """อัปเดตค่ามุม Servo ปัจจุบัน"""
    global current_servo_angle
    with data_lock:
        current_servo_angle = value


def set_target_speed(value):
    """อัปเดตความเร็ว Motor เป้าหมาย"""
    global target_speed
    with data_lock:
        target_speed = value


def set_target_servo_angle(value):
    """อัปเดตมุม Servo เป้าหมาย"""
    global target_servo_angle
    with data_lock:
        target_servo_angle = value


def set_finger_count(value):
    """อัปเดตจำนวนนิ้วที่ตรวจจับได้"""
    global finger_count
    with data_lock:
        finger_count = value
