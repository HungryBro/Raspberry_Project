"""
servo_module.py - ควบคุม Servo MG996R
อ่านมุมเป้าหมายจาก shared_state (Jog ด้วยท่ามือ)
"""

import time
from gpiozero import AngularServo
from config import (factory, SERVO_PIN, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE,
                    SERVO_MIN_PULSE, SERVO_MAX_PULSE, SERVO_SETTLE_TIME)
import shared_state


def servo_worker():
    """Thread: อ่านมุมเป้าหมายจาก shared_state แล้วหมุน Servo ตาม
    กล้องจะอัปเดต target_servo_angle เมื่อตรวจจับหัวแม่มือ/นิ้วก้อย
    """

    servo = None

    try:
        # สร้าง Servo โดยกำหนด initial_value=0 (0° ตรงกลาง)
        # เพื่อป้องกันกระตุกตอนเริ่ม
        servo = AngularServo(SERVO_PIN,
                             min_angle=SERVO_MIN_ANGLE,
                             max_angle=SERVO_MAX_ANGLE,
                             min_pulse_width=SERVO_MIN_PULSE,
                             max_pulse_width=SERVO_MAX_PULSE,
                             initial_angle=0,
                             pin_factory=factory)

        print("[Servo] เริ่มทำงาน - เริ่มต้นที่ 0° (Jog ด้วยท่ามือ)")

        # ตั้งค่าเริ่มต้น
        shared_state.set_servo_angle(0)
        shared_state.set_target_servo_angle(0)
        time.sleep(1.0)  # รอให้ Servo เสถียรที่ 0° ก่อนเริ่ม

        # หลังจากเสถียรแล้ว detach เพื่อหยุดส่ง PWM (ไม่กระตุก)
        servo.detach()
        print("[Servo] พร้อมรับคำสั่งจากท่ามือ")

        last_angle = 0

        while not shared_state.stop_event.is_set():
            # อ่านมุมเป้าหมายจาก shared_state
            status = shared_state.get_status()
            target = status["target_servo_angle"]

            # Clamp มุมให้อยู่ในช่วง
            target = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, target))

            # หมุนเฉพาะเมื่อมุมเปลี่ยน
            if target != last_angle:
                servo.angle = target
                shared_state.set_servo_angle(target)
                time.sleep(SERVO_SETTLE_TIME)
                # detach หลังหมุนเสร็จ เพื่อหยุดส่ง PWM (ลดกระตุก)
                servo.detach()
                last_angle = target
                print(f"[Servo] Angle: {target}°")

            time.sleep(0.05)  # ตรวจสอบทุก 50ms

    except Exception as e:
        print(f"[Servo] เกิดข้อผิดพลาด: {e}")
    finally:
        if servo is not None:
            try:
                servo.angle = 0
                time.sleep(SERVO_SETTLE_TIME)
                servo.detach()
            except:
                pass
        print("[Servo] ปิดการทำงาน")
