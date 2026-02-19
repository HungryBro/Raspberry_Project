"""
camera_module.py - Pi Camera Module 3 + Face Detection (MediaPipe) + YOLO Finger Detection
ใช้ rpicam-vid (pipe YUV420 → OpenCV) รองรับ pyenv Python

ระบบควบคุม:
  - Face Detection (MediaPipe) → หยุด Motor ฉุกเฉิน
  - YOLO Finger Detection → ควบคุมความเร็ว Motor + Servo Jog
    class 0-3 → Motor Speed / class 4 → Servo +5° / class 5 → Servo -5°
"""

import cv2
import numpy as np
import subprocess
import time
import os
import mediapipe as mp_lib
from ultralytics import YOLO
from config import (CAMERA_WIDTH, CAMERA_HEIGHT, FACE_MODEL, FACE_CONFIDENCE,
                    YOLO_MODEL_PATH, YOLO_CONFIDENCE, YOLO_IMG_SIZE,
                    SERVO_STEP, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE,
                    GESTURE_INTERVAL, FINGER_SPEED_MAP)
import shared_state


def camera_worker():
    """Thread (Main): เปิด Pi Camera ผ่าน rpicam-vid + Face Detection + YOLO Finger + แสดง OSD"""

    # === สร้าง MediaPipe Face Detection ===
    mp_face = mp_lib.solutions.face_detection
    mp_draw = mp_lib.solutions.drawing_utils
    face_detection = mp_face.FaceDetection(
        model_selection=FACE_MODEL,
        min_detection_confidence=FACE_CONFIDENCE
    )

    # === โหลด YOLO Model ===
    # หา path ของ model ให้ถูกต้อง (relative จาก script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, YOLO_MODEL_PATH)

    print(f"[Camera] กำลังโหลด YOLO model: {model_path}")
    yolo_model = YOLO(model_path)
    print(f"[Camera] YOLO model loaded! Classes: {yolo_model.names}")

    # === เปิด Pi Camera ผ่าน rpicam-vid ===
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

    print("[Camera] เริ่มทำงาน + Face Detection + YOLO Finger (กด 'q' เพื่อออก)")

    last_jog_time = 0       # ป้องกัน Servo กระตุก
    yolo_label = "NO HAND"  # ข้อมูล YOLO สำหรับ OSD
    fps_time = time.time()  # สำหรับคำนวณ FPS
    fps_counter = 0
    current_fps = 0

    try:
        while not shared_state.stop_event.is_set():
            # === อ่าน YUV420 frame จาก rpicam-vid ===
            raw_data = proc.stdout.read(yuv_frame_size)

            if len(raw_data) != yuv_frame_size:
                print("[Camera] อ่านภาพไม่ได้ (rpicam-vid หยุดทำงาน)")
                break

            # แปลง YUV420 → BGR (สำหรับ OpenCV แสดงผล)
            yuv_frame = np.frombuffer(raw_data, dtype=np.uint8).reshape(
                (CAMERA_HEIGHT * 3 // 2, CAMERA_WIDTH)
            )
            frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)

            # แปลง YUV420 → RGB (สำหรับ MediaPipe + YOLO)
            rgb_frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2RGB_I420)

            # === FPS Counter ===
            fps_counter += 1
            elapsed = time.time() - fps_time
            if elapsed >= 1.0:
                current_fps = fps_counter / elapsed
                fps_counter = 0
                fps_time = time.time()

            # === Face Detection (MediaPipe) ===
            face_results = face_detection.process(rgb_frame)
            has_face = False

            if face_results.detections:
                has_face = True
                shared_state.face_detected.set()
                for detection in face_results.detections:
                    mp_draw.draw_detection(frame, detection)
            else:
                shared_state.face_detected.clear()

            # === YOLO Finger Detection (ทำงานเสมอ) ===
            results = yolo_model(rgb_frame, conf=YOLO_CONFIDENCE,
                                 imgsz=YOLO_IMG_SIZE, verbose=False)

            detected_class = -1  # ยังไม่ detect อะไร

            if results and len(results[0].boxes) > 0:
                # เอา detection ที่ confidence สูงสุด
                boxes = results[0].boxes
                best_idx = boxes.conf.argmax()
                detected_class = int(boxes.cls[best_idx])
                confidence = float(boxes.conf[best_idx])
                class_name = yolo_model.names[detected_class]

                # วาด bounding box
                x1, y1, x2, y2 = boxes.xyxy[best_idx].cpu().numpy().astype(int)
                color = (0, 255, 0) if detected_class <= 3 else (255, 165, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label_text = f"{class_name}: {confidence:.0%}"
                cv2.putText(frame, label_text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                yolo_label = f"Class {detected_class} ({class_name}) {confidence:.0%}"

                # --- ควบคุมความเร็ว Motor ---
                if detected_class in FINGER_SPEED_MAP:
                    speed = FINGER_SPEED_MAP[detected_class]
                    if has_face:
                        shared_state.set_target_speed(0.0)
                        shared_state.set_finger_count(0)
                    else:
                        shared_state.set_target_speed(speed)
                        shared_state.set_finger_count(detected_class)

                # --- Servo Jog (ทำงานเสมอ แม้เจอหน้า) ---
                now = time.time()
                if now - last_jog_time >= GESTURE_INTERVAL:
                    status = shared_state.get_status()
                    current_target = status["target_servo_angle"]

                    if detected_class == 4:
                        # 4 นิ้ว → Servo +5°
                        new_angle = min(current_target + SERVO_STEP, SERVO_MAX_ANGLE)
                        shared_state.set_target_servo_angle(new_angle)
                        last_jog_time = now
                        print(f"[YOLO] 4 นิ้ว -> Servo +{SERVO_STEP}° = {new_angle}°")
                    elif detected_class == 5:
                        # 5 นิ้ว → Servo -5°
                        new_angle = max(current_target - SERVO_STEP, SERVO_MIN_ANGLE)
                        shared_state.set_target_servo_angle(new_angle)
                        last_jog_time = now
                        print(f"[YOLO] 5 นิ้ว -> Servo -{SERVO_STEP}° = {new_angle}°")
            else:
                yolo_label = "NO HAND"

            # === อ่านค่าปัจจุบันสำหรับ OSD ===
            status = shared_state.get_status()
            m = status["motor_speed"]
            s = status["servo_angle"]
            fc = status["finger_count"]

            # === แสดง OSD ===

            # บรรทัดที่ 1: Motor
            if has_face:
                motor_color = (0, 0, 255)
                motor_text = "MOTOR: 0% (FACE!)"
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

            cv2.putText(frame, motor_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, motor_color, 2)

            # บรรทัดที่ 2: Servo
            cv2.putText(frame, f"Servo: {s} deg", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # บรรทัดที่ 3: Face
            if has_face:
                face_text = "FACE: DETECTED"
                face_color = (0, 0, 255)
            else:
                face_text = "FACE: NONE"
                face_color = (0, 255, 0)

            cv2.putText(frame, face_text, (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, face_color, 2)

            # บรรทัดที่ 4: YOLO detection result
            cv2.putText(frame, f"YOLO: {yolo_label}", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            # บรรทัดที่ 5: FPS
            cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

            # Progress bar ความเร็ว Motor
            bar_width = int((m / 100) * 200)
            cv2.rectangle(frame, (10, 160), (210, 180), (50, 50, 50), -1)
            cv2.rectangle(frame, (10, 160), (10 + bar_width, 180), motor_color, -1)

            cv2.imshow('Smart Fan - YOLO Finger Control', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                shared_state.stop_event.set()
                break

    except Exception as e:
        print(f"[Camera] เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()
    finally:
        face_detection.close()
        proc.terminate()
        proc.wait()
        cv2.destroyAllWindows()
        print("[Camera] ปิดกล้องเรียบร้อย")
