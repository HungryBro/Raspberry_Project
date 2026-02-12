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
face_sectors = set()                 # เซ็ตของ Sector ที่ตรวจเจอคน (0-5)
fan_active = True                    # สถานะพัดลม (True = เปิด, False = หยุด)


def get_status():
    """อ่านค่าสถานะทั้งหมดแบบ thread-safe"""
    with data_lock:
        return {
            "voltage": current_voltage,
            "motor_speed": current_motor_speed,
            "servo_angle": current_servo_angle,
            "face": face_detected.is_set(),
            "face_sectors": face_sectors.copy(),
            "fan_active": fan_active,
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


def set_face_sectors(sectors):
    """อัปเดต Sector ที่ตรวจเจอคน"""
    global face_sectors
    with data_lock:
        face_sectors = set(sectors)


def get_face_sectors():
    """อ่าน Sector ที่ตรวจเจอคน"""
    with data_lock:
        return face_sectors.copy()


def set_fan_active(active):
    """อัปเดตสถานะพัดลม"""
    global fan_active
    with data_lock:
        fan_active = active


def is_fan_active():
    """อ่านสถานะพัดลม"""
    with data_lock:
        return fan_active
