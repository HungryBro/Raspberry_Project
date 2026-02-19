"""
servo_module.py - ควบคุม Servo MG996R
<<<<<<< HEAD
รองรับ 2 โหมด:
  - Mode ADC:     ส่ายอัตโนมัติ 0° → 90° → 180° วนลูป
  - Mode Gesture:  อ่านมุมเป้าหมายจาก shared_state (Jog ด้วยท่ามือ)
=======
หมุน 90° → 0° → -90° วนลูป
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
"""

import time
from gpiozero import AngularServo
from config import (factory, SERVO_PIN, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE,
                    SERVO_MIN_PULSE, SERVO_MAX_PULSE, SERVO_ANGLES,
                    SERVO_DELAY, SERVO_SETTLE_TIME)
import shared_state


<<<<<<< HEAD
def _create_servo():
    """สร้าง AngularServo object"""
    servo = AngularServo(SERVO_PIN,
                         min_angle=SERVO_MIN_ANGLE,
                         max_angle=SERVO_MAX_ANGLE,
                         min_pulse_width=SERVO_MIN_PULSE,
                         max_pulse_width=SERVO_MAX_PULSE,
                         pin_factory=factory)
    return servo


def _cleanup_servo(servo):
    """ปิด Servo อย่างปลอดภัย"""
    try:
        servo.angle = 0
        time.sleep(SERVO_SETTLE_TIME)
        servo.detach()
    except:
        pass


def servo_worker():
    """Thread (Mode ADC): ส่ายอัตโนมัติ 0° → 90° → 180° วนลูป"""

    try:
        servo = _create_servo()

        print("[Servo] เริ่มทำงาน (Mode ADC: ส่ายอัตโนมัติ)")

        # ตั้งค่าเริ่มต้นที่ 0° และรอให้เสถียร
        servo.angle = 0
        time.sleep(0.5)

        index = 0
        last_angle = 0

        while not shared_state.stop_event.is_set():
            angle = SERVO_ANGLES[index]

            # Clamp มุมให้อยู่ในช่วงที่กำหนด
            angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, angle))

=======
def servo_worker():
    """Thread: ควบคุม Servo หมุน 90° → 0° → -90° วนลูป"""
    
    try:
        servo = AngularServo(SERVO_PIN,
                             min_angle=SERVO_MIN_ANGLE,
                             max_angle=SERVO_MAX_ANGLE,
                             min_pulse_width=SERVO_MIN_PULSE,
                             max_pulse_width=SERVO_MAX_PULSE,
                             pin_factory=factory)
        
        print("[Servo] เริ่มทำงาน (90° -> 0° -> -90°)")
        
        # ตั้งค่าเริ่มต้นที่ 0° และรอให้เสถียร
        servo.angle = 0
        time.sleep(0.5)
        
        index = 0
        last_angle = 0
        
        while not shared_state.stop_event.is_set():
            angle = SERVO_ANGLES[index]
            
            # Clamp มุมให้อยู่ในช่วงที่กำหนด
            angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, angle))
            
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
            # ถ้ามุมเปลี่ยน ให้หมุนไปที่ตำแหน่งนั้นเลย
            if angle != last_angle:
                servo.angle = angle
                shared_state.set_servo_angle(angle)
                time.sleep(SERVO_SETTLE_TIME)
                last_angle = angle
<<<<<<< HEAD

            print(f"[Servo] Angle: {angle}°")

=======
            
            print(f"[Servo] Angle: {angle}°")
            
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
            # รอก่อนเปลี่ยนมุมถัดไป
            for _ in range(int(SERVO_DELAY / 0.1)):
                if shared_state.stop_event.is_set():
                    break
                time.sleep(0.1)
<<<<<<< HEAD

            if shared_state.stop_event.is_set():
                break

            index = (index + 1) % len(SERVO_ANGLES)

    except Exception as e:
        print(f"[Servo] เกิดข้อผิดพลาด: {e}")
    finally:
        _cleanup_servo(servo)
        print("[Servo] ปิดการทำงาน")


def servo_gesture_worker():
    """Thread (Mode Gesture): อ่านมุมเป้าหมายจาก shared_state แล้วหมุนตาม
    กล้องจะอัปเดต target_servo_angle เมื่อตรวจจับหัวแม่มือ/นิ้วก้อย
    """

    try:
        servo = _create_servo()

        print("[Servo] เริ่มทำงาน (Mode Gesture: Jog ด้วยท่ามือ)")

        # ตั้งค่าเริ่มต้นที่ 0°
        servo.angle = 0
        shared_state.set_servo_angle(0)
        shared_state.set_target_servo_angle(0)
        time.sleep(0.5)

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
                last_angle = target
                print(f"[Servo] Angle: {target}°")

            time.sleep(0.05)  # ตรวจสอบทุก 50ms

    except Exception as e:
        print(f"[Servo] เกิดข้อผิดพลาด: {e}")
    finally:
        _cleanup_servo(servo)
=======
            
            if shared_state.stop_event.is_set():
                break
            
            index = (index + 1) % len(SERVO_ANGLES)
                
    except Exception as e:
        print(f"[Servo] เกิดข้อผิดพลาด: {e}")
    finally:
        try:
            servo.angle = 0
            time.sleep(SERVO_SETTLE_TIME)
            servo.detach()
        except:
            pass
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
        print("[Servo] ปิดการทำงาน")
