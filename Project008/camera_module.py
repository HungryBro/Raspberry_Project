"""
camera_module.py - Pi Camera Module 3 + Face Detection (MediaPipe)
ใช้ rpicam-vid (pipe YUV420 → OpenCV) รองรับ pyenv Python
"""

import cv2
import numpy as np
import subprocess
import mediapipe as mp_lib
from config import CAMERA_WIDTH, CAMERA_HEIGHT, FACE_MODEL, FACE_CONFIDENCE
import shared_state


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
        '-t', '0',                          # ถ่ายไม่จำกัดเวลา
        '--width', str(CAMERA_WIDTH),
        '--height', str(CAMERA_HEIGHT),
        '--codec', 'yuv420',                 # ส่งเป็น YUV420 raw
        '--framerate', '30',
        '-n',                                # ไม่ต้องแสดง preview
        '-o', '-'                            # ส่งออกทาง stdout
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
    
    # ขนาด YUV420 frame = width * height * 1.5
    yuv_frame_size = CAMERA_WIDTH * CAMERA_HEIGHT * 3 // 2
    
    print("[Camera] เริ่มทำงาน + Face Detection (กด 'q' เพื่อออก)")
    
    try:
        while not shared_state.stop_event.is_set():
            # อ่าน YUV420 frame จาก rpicam-vid
            raw_data = proc.stdout.read(yuv_frame_size)
            
            if len(raw_data) != yuv_frame_size:
                print("[Camera] อ่านภาพไม่ได้ (rpicam-vid หยุดทำงาน)")
                break
            
            # แปลง YUV420 → BGR (สำหรับ OpenCV แสดงผล)
            yuv_frame = np.frombuffer(raw_data, dtype=np.uint8).reshape(
                (CAMERA_HEIGHT * 3 // 2, CAMERA_WIDTH)
            )
            frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)
            
            # แปลง YUV420 → RGB (สำหรับ MediaPipe)
            rgb_frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2RGB_I420)
            
            # ตรวจจับใบหน้า
            results = face_detection.process(rgb_frame)
            
            # ตรวจสอบว่าเจอหน้าหรือไม่
            if results.detections:
                shared_state.face_detected.set()
                for detection in results.detections:
                    mp_draw.draw_detection(frame, detection)
            else:
                shared_state.face_detected.clear()
            
            # อ่านค่าปัจจุบัน
            status = shared_state.get_status()
            v = status["voltage"]
            m = status["motor_speed"]
            s = status["servo_angle"]
            has_face = status["face"]
            
            # แสดงข้อมูลบนหน้าจอ
            if has_face:
                motor_color = (0, 0, 255)
                motor_text = "MOTOR: 0% (FACE!)"
                face_text = "FACE: DETECTED"
                face_color = (0, 0, 255)
            else:
                if m == 0:
                    motor_color = (128, 128, 128)
                elif m <= 30:
                    motor_color = (0, 255, 255)
                elif m <= 60:
                    motor_color = (0, 165, 255)
                else:
                    motor_color = (0, 0, 255)
                motor_text = f"MOTOR: {m}%"
                face_text = "FACE: NONE"
                face_color = (0, 255, 0)
            
            cv2.putText(frame, f"Voltage: {v:.2f}V", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, motor_text, (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, motor_color, 2)
            cv2.putText(frame, f"Servo: {s} deg", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, face_text, (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, face_color, 2)
            
            # Progress bar
            bar_width = int((m / 100) * 200)
            cv2.rectangle(frame, (10, 130), (210, 150), (50, 50, 50), -1)
            cv2.rectangle(frame, (10, 130), (10 + bar_width, 150), motor_color, -1)
            
            cv2.imshow('Smart Fan - Face Detection', frame)
            
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
