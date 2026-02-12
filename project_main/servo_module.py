"""
servo_module.py - ควบคุม Servo MG996R
Scan sweep 57° → 123° → 57° วนลูป
ตรวจสอบ No-Go Zone ทุก step เพื่อสั่งหยุดพัดลม
"""

import time
from gpiozero import AngularServo
from config import (factory, SERVO_PIN, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE,
                    SERVO_MIN_PULSE, SERVO_MAX_PULSE,
                    SERVO_SCAN_MIN, SERVO_SCAN_MAX, SERVO_STEP_DELAY,
                    SERVO_SETTLE_TIME, NUM_SECTORS, SECTOR_DEG)
import shared_state


def angle_to_sector(angle):
    """แปลงมุม Servo (57-123) เป็นหมายเลข Sector (0-5)"""
    sector = int((angle - SERVO_SCAN_MIN) / SECTOR_DEG)
    # Clamp ให้อยู่ในช่วง 0 ถึง NUM_SECTORS-1
    return max(0, min(NUM_SECTORS - 1, sector))


def get_no_go_zones(face_sectors):
    """คำนวณ No-Go Zone จาก Sector ที่มีคน
    No-Go = Sector ที่มีคน + Sector ก่อนหน้า (เพื่อให้ลมไม่เฉียด)
    """
    no_go = set()
    for s in face_sectors:
        no_go.add(s)           # Sector ที่คนยืน
        if s - 1 >= 0:
            no_go.add(s - 1)   # Sector ก่อนหน้า (Buffer)
    return no_go


def servo_worker():
    """Thread: ควบคุม Servo scan sweep 57° → 123° → 57° วนลูป"""
    
    try:
        servo = AngularServo(SERVO_PIN,
                             min_angle=SERVO_MIN_ANGLE,
                             max_angle=SERVO_MAX_ANGLE,
                             min_pulse_width=SERVO_MIN_PULSE,
                             max_pulse_width=SERVO_MAX_PULSE,
                             pin_factory=factory)
        
        print(f"[Servo] เริ่มทำงาน (Scan {SERVO_SCAN_MIN}° → {SERVO_SCAN_MAX}°)")
        
        # ตั้งค่าเริ่มต้นที่กลาง (90°) และรอให้เสถียร
        servo.angle = 90
        shared_state.set_servo_angle(90)
        time.sleep(SERVO_SETTLE_TIME)
        
        # ทิศทาง scan: 1 = ไปขวา (เพิ่มมุม), -1 = ไปซ้าย (ลดมุม)
        direction = 1
        current_angle = SERVO_SCAN_MIN
        
        while not shared_state.stop_event.is_set():
            # ตั้งค่ามุม Servo
            servo.angle = current_angle
            shared_state.set_servo_angle(current_angle)
            
            # คำนวณ Sector ปัจจุบัน
            current_sector = angle_to_sector(current_angle)
            
            # ดึง face_sectors จาก shared_state
            face_secs = shared_state.get_face_sectors()
            
            # คำนวณ No-Go Zone
            no_go = get_no_go_zones(face_secs)
            
            # ตรวจสอบว่า Servo อยู่ใน No-Go Zone หรือไม่
            if current_sector in no_go:
                shared_state.set_fan_active(False)
            else:
                shared_state.set_fan_active(True)
            
            # รอ delay ก่อนขยับขั้นถัดไป
            time.sleep(SERVO_STEP_DELAY)
            
            # ขยับมุมถัดไป
            current_angle += direction
            
            # ถ้าถึงขอบ ให้กลับทิศ
            if current_angle >= SERVO_SCAN_MAX:
                current_angle = SERVO_SCAN_MAX
                direction = -1
            elif current_angle <= SERVO_SCAN_MIN:
                current_angle = SERVO_SCAN_MIN
                direction = 1
            
            if shared_state.stop_event.is_set():
                break
                
    except Exception as e:
        print(f"[Servo] เกิดข้อผิดพลาด: {e}")
    finally:
        try:
            servo.angle = 90
            time.sleep(SERVO_SETTLE_TIME)
            servo.detach()
        except:
            pass
        print("[Servo] ปิดการทำงาน")
