"""
servo_module.py - ควบคุม Servo MG996R
หมุน 90° → 0° → -90° วนลูป
"""

import time
from gpiozero import AngularServo
from config import (factory, SERVO_PIN, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE,
                    SERVO_MIN_PULSE, SERVO_MAX_PULSE, SERVO_ANGLES,
                    SERVO_DELAY, SERVO_SETTLE_TIME)
import shared_state


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
            
            # ถ้ามุมเปลี่ยน ให้หมุนไปที่ตำแหน่งนั้นเลย
            if angle != last_angle:
                servo.angle = angle
                shared_state.set_servo_angle(angle)
                time.sleep(SERVO_SETTLE_TIME)
                last_angle = angle
            
            print(f"[Servo] Angle: {angle}°")
            
            # รอก่อนเปลี่ยนมุมถัดไป
            for _ in range(int(SERVO_DELAY / 0.1)):
                if shared_state.stop_event.is_set():
                    break
                time.sleep(0.1)
            
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
        print("[Servo] ปิดการทำงาน")
