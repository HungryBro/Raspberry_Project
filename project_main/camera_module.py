"""
camera_module.py - Pi Camera Module 3 + Face Detection (MediaPipe)
ใช้ rpicam-vid (pipe YUV420 → OpenCV) รองรับ pyenv Python
UI: แสดง 6 Sector grid + No-Go Zone + สถานะพัดลม
"""

import cv2
import numpy as np
import subprocess
import mediapipe as mp_lib
from config import (CAMERA_WIDTH, CAMERA_HEIGHT, FACE_MODEL, FACE_CONFIDENCE,
                    NUM_SECTORS, SERVO_SCAN_MIN, SECTOR_DEG)
import shared_state


def pixel_to_sector(center_x):
    """แปลงตำแหน่ง pixel (0-640) เป็นหมายเลข Sector (0-5)"""
    sector = int((center_x / CAMERA_WIDTH) * NUM_SECTORS)
    return max(0, min(NUM_SECTORS - 1, sector))


def get_no_go_zones(face_sectors):
    """คำนวณ No-Go Zone จาก Sector ที่มีคน"""
    no_go = set()
    for s in face_sectors:
        no_go.add(s)
        if s - 1 >= 0:
            no_go.add(s - 1)
    return no_go


def draw_sector_grid(frame, face_sectors, fan_active, servo_angle):
    """วาด UI แสดง 6 Sector, No-Go Zone, สถานะพัดลม"""
    h, w = frame.shape[:2]
    sector_width = w // NUM_SECTORS
    
    no_go = get_no_go_zones(face_sectors)
    
    # คำนวณ Sector ปัจจุบันของ Servo
    servo_sector = int((servo_angle - SERVO_SCAN_MIN) / SECTOR_DEG)
    servo_sector = max(0, min(NUM_SECTORS - 1, servo_sector))
    
    for i in range(NUM_SECTORS):
        x1 = i * sector_width
        x2 = (i + 1) * sector_width
        
        # ระบายสี No-Go Zone (สีแดงโปร่ง)
        if i in no_go:
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, 0), (x2, h), (0, 0, 200), -1)
            cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)
        
        # ระบายสี Sector ที่มีคน (สีแดงเข้มกว่า)
        if i in face_sectors:
            overlay = frame.copy()
            cv2.rectangle(overlay, (x1, 0), (x2, h), (0, 0, 255), -1)
            cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
        
        # วาดเส้น grid แนวตั้ง
        if i > 0:
            cv2.line(frame, (x1, 0), (x1, h), (100, 100, 100), 1)
        
        # แสดงหมายเลข Sector
        angle_start = SERVO_SCAN_MIN + i * SECTOR_DEG
        angle_end = angle_start + SECTOR_DEG
        label = f"S{i}"
        label_deg = f"{angle_start}-{angle_end}"
        
        cv2.putText(frame, label, (x1 + 5, h - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(frame, label_deg, (x1 + 5, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 150, 150), 1)
    
    # วาดตำแหน่ง Servo ปัจจุบัน (เส้นสีเขียว)
    servo_x = int(((servo_angle - SERVO_SCAN_MIN) / (NUM_SECTORS * SECTOR_DEG)) * w)
    servo_x = max(0, min(w - 1, servo_x))
    cv2.line(frame, (servo_x, 0), (servo_x, h), (0, 255, 0), 2)
    
    # แสดง OSD ข้อมูล
    status = shared_state.get_status()
    v = status["voltage"]
    m = status["motor_speed"]
    
    # Fan Status
    if fan_active:
        fan_text = f"FAN: ON ({m}%)"
        fan_color = (0, 255, 0)
    else:
        fan_text = "FAN: OFF (NO-GO ZONE)"
        fan_color = (0, 0, 255)
    
    # วาด background bar สำหรับ OSD
    cv2.rectangle(frame, (0, 0), (w, 105), (0, 0, 0), -1)
    cv2.addWeighted(frame, 0.6, frame, 0.4, 0, frame)
    
    cv2.putText(frame, f"Servo: {servo_angle} deg (Sector {servo_sector})", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, fan_text, (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, fan_color, 2)
    cv2.putText(frame, f"Voltage: {v:.2f}V | Motor: {m}%", (10, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    if face_sectors:
        sectors_str = ", ".join([f"S{s}" for s in sorted(face_sectors)])
        cv2.putText(frame, f"Face at: {sectors_str}", (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    else:
        cv2.putText(frame, "Face: NONE", (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 2)
    
    return frame


def camera_worker():
    """Thread (Main): เปิด Pi Camera ผ่าน rpicam-vid + ตรวจจับใบหน้า + แสดง OSD"""
    
    # สร้าง MediaPipe Face Detection
    mp_face = mp_lib.solutions.face_detection
    mp_draw = mp_lib.solutions.drawing_utils
    face_detection = mp_face.FaceDetection(
        model_selection=FACE_MODEL,
        min_detection_confidence=FACE_CONFIDENCE
    )
    
    # เปิด Pi Camera ผ่าน rpicam-vid (pipe YUV420 ออกมา)
    print("[Camera] กำลังเปิด Pi Camera Module 3 (rpicam-vid)...")
    
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
        print("[Camera] ไม่พบคำสั่ง rpicam-vid กรุณาติดตั้ง: sudo apt install rpicam-apps")
        shared_state.stop_event.set()
        return
    except Exception as e:
        print(f"[Camera] ไม่สามารถเปิดกล้องได้: {e}")
        shared_state.stop_event.set()
        return
    
    yuv_frame_size = CAMERA_WIDTH * CAMERA_HEIGHT * 3 // 2
    
    print(f"[Camera] เริ่มทำงาน + Face Detection ({NUM_SECTORS} Sectors)")
    
    try:
        while not shared_state.stop_event.is_set():
            # อ่าน YUV420 frame
            raw_data = proc.stdout.read(yuv_frame_size)
            
            if len(raw_data) != yuv_frame_size:
                print("[Camera] อ่านภาพไม่ได้ (rpicam-vid หยุดทำงาน)")
                break
            
            # แปลง YUV420 → BGR + RGB
            yuv_frame = np.frombuffer(raw_data, dtype=np.uint8).reshape(
                (CAMERA_HEIGHT * 3 // 2, CAMERA_WIDTH)
            )
            frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)
            rgb_frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2RGB_I420)
            
            # ตรวจจับใบหน้า (MediaPipe)
            results = face_detection.process(rgb_frame)
            
            # คำนวณ Sector ที่เจอคน
            detected_sectors = set()
            
            if results.detections:
                shared_state.face_detected.set()
                for detection in results.detections:
                    # วาดกรอบใบหน้า
                    mp_draw.draw_detection(frame, detection)
                    
                    # คำนวณ center_x ของใบหน้า
                    bbox = detection.location_data.relative_bounding_box
                    center_x = (bbox.xmin + bbox.width / 2) * CAMERA_WIDTH
                    
                    # แปลง pixel → sector
                    sector = pixel_to_sector(int(center_x))
                    detected_sectors.add(sector)
            else:
                shared_state.face_detected.clear()
            
            # อัปเดต face_sectors ให้ module อื่นอ่าน
            shared_state.set_face_sectors(detected_sectors)
            
            # อ่านสถานะปัจจุบัน
            status = shared_state.get_status()
            servo_angle = status["servo_angle"]
            fan_active = status["fan_active"]
            
            # วาด Sector Grid + OSD
            frame = draw_sector_grid(frame, detected_sectors, fan_active, servo_angle)
            
            cv2.imshow('Smart Fan - Anti-Direct-Blow', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                shared_state.stop_event.set()
                break
                
    except Exception as e:
        print(f"[Camera] เกิดข้อผิดพลาด: {e}")
    finally:
        face_detection.close()
        proc.terminate()
        proc.wait()
        cv2.destroyAllWindows()
        print("[Camera] ปิดกล้องเรียบร้อย")
