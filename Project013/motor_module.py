"""
motor_module.py - ควบคุม Motor Driver
"""

import time
from gpiozero import PWMOutputDevice, DigitalOutputDevice
from config import factory, MOTOR_PWM_PIN, MOTOR_AIN1_PIN, MOTOR_AIN2_PIN
import shared_state

pwm_a = None
ain1 = None
ain2 = None


def init():
    global pwm_a, ain1, ain2
    with shared_state.motor_lock:
        pwm_a = PWMOutputDevice(MOTOR_PWM_PIN, pin_factory=factory)
        ain1 = DigitalOutputDevice(MOTOR_AIN1_PIN, pin_factory=factory)
        ain2 = DigitalOutputDevice(MOTOR_AIN2_PIN, pin_factory=factory)
    print("[Motor] พร้อมทำงาน")


def control(speed):
    global pwm_a, ain1, ain2
    with shared_state.motor_lock:
        if pwm_a is None:
            return
        if speed > 0:
            ain1.on()
            ain2.off()
            pwm_a.value = speed
        else:
            ain1.on()
            ain2.on()
            pwm_a.value = 0


def brake():
    control(0)


def motor_worker():
    try:
        init()
        print("[Motor] เริ่มทำงาน")
        while not shared_state.stop_event.is_set():
            try:
                if shared_state.face_detected.is_set():
                    brake()
                    shared_state.set_motor_speed(0)
                else:
                    status = shared_state.get_status()
                    speed = status["target_speed"]
                    control(speed)
                    shared_state.set_motor_speed(int(speed * 100))
            except Exception as e:
                print(f"[Motor] Error: {e}")
            time.sleep(0.1)
    except Exception as e:
        print(f"[Motor] เกิดข้อผิดพลาด: {e}")
    finally:
        brake()
        print("[Motor] ปิดการทำงาน")
