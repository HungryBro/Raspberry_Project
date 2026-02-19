"""
motor_module.py - ควบคุม Motor Driver (TB6612 / L298N)
ควบคุมความเร็วด้วย Sign Language Detection ผ่าน shared_state
"""

import time
from gpiozero import PWMOutputDevice, DigitalOutputDevice
from config import factory, MOTOR_PWM_PIN, MOTOR_AIN1_PIN, MOTOR_AIN2_PIN
import shared_state

# --- Motor Objects ---
pwm_a = None
ain1 = None
ain2 = None


def init():
    """สร้าง Motor objects"""
    global pwm_a, ain1, ain2

    with shared_state.motor_lock:
        pwm_a = PWMOutputDevice(MOTOR_PWM_PIN, pin_factory=factory)
        ain1 = DigitalOutputDevice(MOTOR_AIN1_PIN, pin_factory=factory)
        ain2 = DigitalOutputDevice(MOTOR_AIN2_PIN, pin_factory=factory)

    print("[Motor] พร้อมทำงาน")


def control(speed):
    """ควบคุม Motor
    speed: 0.0 - 1.0 (0 = หยุด, 1 = เต็มกำลัง)
    """
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
    """เบรค Motor"""
    control(0)


def motor_worker():
    """Thread: อ่าน target_speed จาก shared_state แล้วสั่ง Motor
    - เจอหน้าคน → Motor = 0% (หยุดฉุกเฉิน)
    - ไม่เจอหน้า → Motor ตาม target_speed จากท่ามือภาษามือ
    """
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
