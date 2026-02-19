"""
servo_module.py - ควบคุม Servo MG996R
"""

import time
from gpiozero import AngularServo
from config import (factory, SERVO_PIN, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE,
                    SERVO_MIN_PULSE, SERVO_MAX_PULSE, SERVO_SETTLE_TIME)
import shared_state


def servo_worker():
    servo = None
    try:
        servo = AngularServo(SERVO_PIN,
                             min_angle=SERVO_MIN_ANGLE,
                             max_angle=SERVO_MAX_ANGLE,
                             min_pulse_width=SERVO_MIN_PULSE,
                             max_pulse_width=SERVO_MAX_PULSE,
                             initial_angle=0,
                             pin_factory=factory)

        print("[Servo] เริ่มทำงาน - 0° (Jog: YOLO T/Y หรือ MediaPipe 4f/5f)")
        shared_state.set_servo_angle(0)
        shared_state.set_target_servo_angle(0)
        time.sleep(1.0)

        last_angle = 0

        while not shared_state.stop_event.is_set():
            status = shared_state.get_status()
            target = status["target_servo_angle"]
            target = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, target))

            if target != last_angle:
                print(f"[Servo] {last_angle}° → {target}°")
                servo.angle = target
                shared_state.set_servo_angle(target)
                time.sleep(SERVO_SETTLE_TIME)
                last_angle = target

            time.sleep(0.05)

    except Exception as e:
        print(f"[Servo] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if servo is not None:
            try:
                servo.angle = 0
                time.sleep(SERVO_SETTLE_TIME)
                servo.detach()
            except:
                pass
        print("[Servo] ปิดการทำงาน")
