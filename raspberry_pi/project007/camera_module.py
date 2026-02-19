"""
camera_module.py - กล้อง USB + Face Detection (MediaPipe)
"""

import cv2
import mediapipe as mp_lib
from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, FACE_MODEL, FACE_CONFIDENCE
import shared_state


def camera_worker():
    """Thread (Main): เปิดกล้อง + ตรวจจับใบหน้า + แสดง OSD"""
    
    # สร้าง MediaPipe Face Detection
    mp_face = mp_lib.solutions.face_detection
    mp_draw = mp_lib.solutions.drawing_utils
    face_detection = mp_face.FaceDetection(
        model_selection=FACE_MODEL,
        min_detection_confidence=FACE_CONFIDENCE
    )
    
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(3, CAMERA_WIDTH)
    cap.set(4, CAMERA_HEIGHT)
    
    if not cap.isOpened():
        print("[Camera] ไม่สามารถเปิดกล้องได้")
        shared_state.stop_event.set()
        return
    
    print("[Camera] เริ่มทำงาน + Face Detection (กด 'q' เพื่อออก)")
    
    try:
        while not shared_state.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("[Camera] อ่านภาพไม่ได้")
                break
            
            # แปลง BGR → RGB สำหรับ MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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
        cap.release()
        cv2.destroyAllWindows()
        print("[Camera] ปิดกล้องเรียบร้อย")
