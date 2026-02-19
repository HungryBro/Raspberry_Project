"""
shared_state.py - ตัวแปรร่วมระหว่าง Thread ทั้งหมด
"""

import threading

# --- Events ---
stop_event = threading.Event()       # สำหรับหยุดโปรแกรมทั้งหมด
face_detected = threading.Event()    # แจ้งเมื่อเจอหน้าคน

# --- Locks ---
data_lock = threading.Lock()         # ป้องกัน race condition ข้อมูลทั่วไป
motor_lock = threading.Lock()        # ป้องกัน race condition ตัว Motor

# --- Shared Data ---
current_voltage = 0.0
current_motor_speed = 0
current_servo_angle = 0


def get_status():
    """อ่านค่าสถานะทั้งหมดแบบ thread-safe"""
    with data_lock:
        return {
            "voltage": current_voltage,
            "motor_speed": current_motor_speed,
            "servo_angle": current_servo_angle,
            "face": face_detected.is_set()
        }


def set_voltage(value):
    """อัปเดตค่าแรงดัน"""
    global current_voltage
    with data_lock:
        current_voltage = value


def set_motor_speed(value):
    """อัปเดตค่าความเร็ว Motor"""
    global current_motor_speed
    with data_lock:
        current_motor_speed = value


def set_servo_angle(value):
    """อัปเดตค่ามุม Servo"""
    global current_servo_angle
    with data_lock:
        current_servo_angle = value
