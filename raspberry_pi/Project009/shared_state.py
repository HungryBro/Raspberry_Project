"""
shared_state.py - ตัวแปรร่วมระหว่าง Thread ทั้งหมด
<<<<<<< HEAD
รองรับทั้ง Mode ADC และ Mode Gesture
=======
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
"""

import threading

# --- Events ---
stop_event = threading.Event()       # สำหรับหยุดโปรแกรมทั้งหมด
face_detected = threading.Event()    # แจ้งเมื่อเจอหน้าคน

# --- Locks ---
data_lock = threading.Lock()         # ป้องกัน race condition ข้อมูลทั่วไป
motor_lock = threading.Lock()        # ป้องกัน race condition ตัว Motor

<<<<<<< HEAD
# --- Shared Data (เดิม - Mode ADC) ---
=======
# --- Shared Data ---
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
current_voltage = 0.0
current_motor_speed = 0
current_servo_angle = 0

<<<<<<< HEAD
# --- Shared Data (ใหม่ - Mode Gesture) ---
target_speed = 0.0                   # ความเร็ว Motor เป้าหมาย (0.0 - 1.0)
target_servo_angle = 0               # มุม Servo เป้าหมาย (องศา)
finger_count = 0                     # จำนวนนิ้วที่ตรวจจับได้


# =====================================================
#  Getter / Setter แบบ thread-safe
# =====================================================
=======
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77

def get_status():
    """อ่านค่าสถานะทั้งหมดแบบ thread-safe"""
    with data_lock:
        return {
            "voltage": current_voltage,
            "motor_speed": current_motor_speed,
            "servo_angle": current_servo_angle,
<<<<<<< HEAD
            "face": face_detected.is_set(),
            "target_speed": target_speed,
            "target_servo_angle": target_servo_angle,
            "finger_count": finger_count,
=======
            "face": face_detected.is_set()
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
        }


def set_voltage(value):
<<<<<<< HEAD
    """อัปเดตค่าแรงดัน (Mode ADC)"""
=======
    """อัปเดตค่าแรงดัน"""
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
    global current_voltage
    with data_lock:
        current_voltage = value


def set_motor_speed(value):
<<<<<<< HEAD
    """อัปเดตค่าความเร็ว Motor (แสดงผลเป็น %)"""
=======
    """อัปเดตค่าความเร็ว Motor"""
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
    global current_motor_speed
    with data_lock:
        current_motor_speed = value


def set_servo_angle(value):
<<<<<<< HEAD
    """อัปเดตค่ามุม Servo ปัจจุบัน"""
    global current_servo_angle
    with data_lock:
        current_servo_angle = value


def set_target_speed(value):
    """อัปเดตความเร็ว Motor เป้าหมาย (Mode Gesture)"""
    global target_speed
    with data_lock:
        target_speed = value


def set_target_servo_angle(value):
    """อัปเดตมุม Servo เป้าหมาย (Mode Gesture)"""
    global target_servo_angle
    with data_lock:
        target_servo_angle = value


def set_finger_count(value):
    """อัปเดตจำนวนนิ้วที่ตรวจจับได้"""
    global finger_count
    with data_lock:
        finger_count = value
=======
    """อัปเดตค่ามุม Servo"""
    global current_servo_angle
    with data_lock:
        current_servo_angle = value
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
