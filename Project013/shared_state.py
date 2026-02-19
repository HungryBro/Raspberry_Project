"""
shared_state.py - ตัวแปรร่วมระหว่าง Thread ทั้งหมด
ใช้สำหรับระบบ Dual AI Detection (YOLO + MediaPipe)
"""

import threading

stop_event = threading.Event()
face_detected = threading.Event()

data_lock = threading.Lock()
motor_lock = threading.Lock()

current_motor_speed = 0
current_servo_angle = 0
target_speed = 0.0
target_servo_angle = 0
finger_count = 0


def get_status():
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
    global current_motor_speed
    with data_lock:
        current_motor_speed = value


def set_servo_angle(value):
    global current_servo_angle
    with data_lock:
        current_servo_angle = value


def set_target_speed(value):
    global target_speed
    with data_lock:
        target_speed = value


def set_target_servo_angle(value):
    global target_servo_angle
    with data_lock:
        target_servo_angle = value


def set_finger_count(value):
    global finger_count
    with data_lock:
        finger_count = value
