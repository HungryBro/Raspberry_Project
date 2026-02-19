"""
test_camera_servo.py - ทดสอบกล้อง (rpicam-vid) พร้อมกับการหมุน Servo
- กล้อง: แสดงภาพจาก Pi Camera Module 3 (rpicam-vid)
- Servo: หมุน 0 -> 90 -> 0 -> -90 ช้าๆ (แยก Thread)
"""

import cv2
import numpy as np
import subprocess
import threading
import time
from gpiozero import AngularServo
import warnings

# ปิด Warning ของ gpiozero
warnings.filterwarnings("ignore")

# --- Config ---
SERVO_PIN = 19
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Global Variable สำหรับแชร์มุม Servo ไปโชว์บนกล้อง
current_servo_angle = 0
stop_event = threading.Event()

# --- Servo Init ---
servo = AngularServo(SERVO_PIN, 
                     min_angle=-90, 
                     max_angle=90,
                     min_pulse_width=0.0005, 
                     max_pulse_width=0.0025/2)

def move_slowly(target, step_delay=0.02):
    """ฟังก์ชันหมุน Servo ช้าๆ"""
    global current_servo_angle
    
    current = int(current_servo_angle)
    step = 1 if target > current else -1
    
    for angle in range(current, target, step):
        if stop_event.is_set(): break
        servo.angle = angle
        current_servo_angle = angle
        time.sleep(step_delay)
        
    servo.angle = target
    current_servo_angle = target

def servo_worker():
    """Thread: ควบคุม Servo หมุนวนลูป"""
    print("[Servo] เริ่มทำงาน...")
    global current_servo_angle
    
    # ตั้งค่าเริ่มต้น
    servo.angle = 0
    current_servo_angle = 0
    time.sleep(1)
    
    while not stop_event.is_set():
        # 0 -> 90
        move_slowly(90)
        time.sleep(0.5)
        
        # 90 -> 0
        move_slowly(0)
        time.sleep(0.5)
        
        # 0 -> -90
        move_slowly(-90)
        time.sleep(0.5)
        
        # -90 -> 0
        move_slowly(0)
        time.sleep(0.5)
        
    print("[Servo] หยุดทำงาน")

def camera_worker():
    """Thread: แสดงภาพจากกล้อง (Main Thread)"""
    print("[Camera] กำลังเปิดกล้อง (rpicam-vid)...")
    
    cmd = [
        'rpicam-vid',
        '-t', '0',
        '--width', str(CAMERA_WIDTH),
        '--height', str(CAMERA_HEIGHT),
        '--codec', 'yuv420',
        '--framerate', '30',
        '-n',
        '-o', '-'
    ]
    
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("❌ ไม่พบคำสั่ง rpicam-vid (โปรดติดตั้ง rpicam-apps)")
        stop_event.set()
        return

    yuv_frame_size = CAMERA_WIDTH * CAMERA_HEIGHT * 3 // 2
    
    print("[Camera] พร้อมใช้งาน (กด 'q' เพื่อออก)")
    
    try:
        while not stop_event.is_set():
            # อ่านข้อมูล raw YUV420
            raw_data = proc.stdout.read(yuv_frame_size)
            
            if len(raw_data) != yuv_frame_size:
                print("[Camera] อ่านเฟรมไม่ได้")
                break
                
            # แปลง YUV -> BGR (สำหรับ OpenCV)
            yuv_frame = np.frombuffer(raw_data, dtype=np.uint8).reshape(
                (CAMERA_HEIGHT * 3 // 2, CAMERA_WIDTH)
            )
            frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)
            
            # วาดข้อมูลบนภาพ
            text = f"Servo Angle: {current_servo_angle} deg"
            cv2.putText(frame, text, (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # วาดเส้นกากบาทตรงกลาง (Crosshair)
            cx, cy = CAMERA_WIDTH // 2, CAMERA_HEIGHT // 2
            cv2.line(frame, (cx - 20, cy), (cx + 20, cy), (0, 0, 255), 2)
            cv2.line(frame, (cx, cy - 20), (cx, cy + 20), (0, 0, 255), 2)

            cv2.imshow("Camera + Servo Test", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set()
                break
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        proc.terminate()
        cv2.destroyAllWindows()
        print("[Camera] ปิดกล้องเรียบร้อย")

if __name__ == "__main__":
    try:
        # เริ่ม Servo Thread
        t_servo = threading.Thread(target=servo_worker)
        t_servo.start()
        
        # รันกล้องที่ Main Thread
        camera_worker()
        
        # รอ Servo จบ
        t_servo.join()
        
    except KeyboardInterrupt:
        stop_event.set()
