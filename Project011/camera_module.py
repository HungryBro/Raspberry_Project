"""
camera_module.py - Pi Camera Module 3 + Face Detection (MediaPipe)
                 + Sign Language Detection (Roboflow extrdb/2)

 Optimization (Frame Skipping):
  - Face: ตรวจทุก 5 เฟรม
  - Cloud Inference: ส่งทุก 5 เฟรม (ช่วยลด delay สะสม)
"""

import cv2
import numpy as np
import subprocess
import time
import os
import mediapipe as mp_lib
from inference import get_model
from config import (CAMERA_WIDTH, CAMERA_HEIGHT, FACE_MODEL, FACE_CONFIDENCE,
                    ROBOFLOW_API_KEY, ROBOFLOW_MODEL_ID, SIGN_CONFIDENCE,
                    SERVO_STEP, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE,
                    GESTURE_INTERVAL, SIGN_SPEED_MAP,
                    SERVO_RIGHT_SIGNS, SERVO_LEFT_SIGNS, SKIP_FACE, SKIP_CLOUD)
import shared_state


# === แปลง sign class เป็น action อ่านง่าย ===
SIGN_DISPLAY = {
    "s": "✊ S (fist) → 0%",
    "o": "👌 O (circle) → 0%",
    "d": "☝️ D (point) → 30%",
    "x": "🤞 X (hook) → 30%",
    "v": "✌️ V (2 fingers) → 60%",
    "w": "🤟 W (3 fingers) → 100%",
    "t": "👍 T → Servo +5°",
    "y": "🤙 Y → Servo -5°",
}


def camera_worker():
    """Thread (Main): Face Detection + Sign Language + OSD"""

    # === สร้าง MediaPipe Face Detection ===
    mp_face = mp_lib.solutions.face_detection
    mp_draw = mp_lib.solutions.drawing_utils
    face_detection = mp_face.FaceDetection(
        model_selection=FACE_MODEL,
        min_detection_confidence=FACE_CONFIDENCE
    )

    # === โหลด Roboflow Model ===
    print(f"[Camera] กำลังโหลด Roboflow model: {ROBOFLOW_MODEL_ID}")
    try:
        sign_model = get_model(model_id=ROBOFLOW_MODEL_ID, api_key=ROBOFLOW_API_KEY)
        print(f"[Camera] Roboflow model loaded!")
    except Exception as e:
        print(f"[Camera] Load Model Failed: {e}")
        return

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

    print("[Camera] เริ่มทำงาน (Optimized: Skip Frames)")

    last_jog_time = 0         # ป้องกัน Servo กระตุก
    sign_label = "NO HAND"    # ข้อมูล Sign สำหรับ OSD
    fps_time = time.time()    # สำหรับคำนวณ FPS
    fps_counter = 0
    current_fps = 0
    
    # Frame counters
    frame_cnt_face = 0
    frame_cnt_cloud = 0
    
    # Cache state (เก็บค่าไว้ใช้ระหว่าง frame ที่ skip)
    has_face = False
    face_detections = None
    detected_sign = None
    best_conf = 0
    latest_predictions = []

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
            frame = cv2.flip(frame, 1)  # กลับด้านกล้อง (Mirror)
            rgb_frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2RGB_I420)

            # === FPS Counter ===
            fps_counter += 1
            elapsed = time.time() - fps_time
            if elapsed >= 1.0:
                current_fps = fps_counter / elapsed
                fps_counter = 0
                fps_time = time.time()

            # ==========================================
            # 1. Face Detection (Every SKIP_FACE frames)
            # ==========================================
            frame_cnt_face += 1
            if frame_cnt_face >= SKIP_FACE:
                frame_cnt_face = 0
                face_results = face_detection.process(rgb_frame)
                
                has_face = False
                face_detections = None
                
                if face_results.detections:
                    has_face = True
                    face_detections = face_results.detections
                    shared_state.face_detected.set()
                else:
                    shared_state.face_detected.clear()
            
            # Draw Face (from cache)
            if face_detections:
                for detection in face_detections:
                    mp_draw.draw_detection(frame, detection)

            # ==========================================
            # 2. Sign Language Detection (Every SKIP_CLOUD frames)
            # ==========================================
            frame_cnt_cloud += 1
            if frame_cnt_cloud >= SKIP_CLOUD:
                frame_cnt_cloud = 0

                # ส่ง frame ให้ Roboflow model
                try:
                    results = sign_model.infer(frame, confidence=SIGN_CONFIDENCE)
                except Exception as e:
                    print(f"[Cloud] Error: {e}")
                    results = []

                # Reset temp vars
                detected_sign = None
                best_conf = 0
                latest_predictions = []

                if results and len(results) > 0:
                    latest_predictions = results[0].predictions if hasattr(results[0], 'predictions') else []

                    for pred in latest_predictions:
                        cls_name = pred.class_name.lower()
                        conf = pred.confidence

                        # เอาเฉพาะ class ที่เรา map ไว้ + confidence สูงสุด
                        all_valid = list(SIGN_SPEED_MAP.keys()) + SERVO_RIGHT_SIGNS + SERVO_LEFT_SIGNS
                        if cls_name in all_valid and conf > best_conf:
                            detected_sign = cls_name
                            best_conf = conf
            
            # --- Process Results (Logic Runs Every Frame based on Cache) ---
            if detected_sign:
                display = SIGN_DISPLAY.get(detected_sign, detected_sign)
                sign_label = f"{display} ({best_conf:.0%})"

                # --- วาด bounding box ---
                for pred in latest_predictions:
                    if pred.class_name.lower() == detected_sign:
                        x1 = int(pred.x - pred.width / 2)
                        y1 = int(pred.y - pred.height / 2)
                        x2 = int(pred.x + pred.width / 2)
                        y2 = int(pred.y + pred.height / 2)

                        is_servo = detected_sign in SERVO_RIGHT_SIGNS + SERVO_LEFT_SIGNS
                        color = (255, 165, 0) if is_servo else (0, 255, 0)

                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame, f"{detected_sign.upper()} {best_conf:.0%}",
                                    (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                        break

                # --- ควบคุมความเร็ว Motor ---
                if detected_sign in SIGN_SPEED_MAP:
                    speed = SIGN_SPEED_MAP[detected_sign]
                    if has_face:
                        shared_state.set_target_speed(0.0)
                        shared_state.set_finger_count(0)
                    else:
                        shared_state.set_target_speed(speed)
                        finger_map = {"s": 0, "o": 0, "d": 1, "x": 1, "v": 2, "w": 3}
                        shared_state.set_finger_count(finger_map.get(detected_sign, 0))

                # --- Servo Jog (ทำงานเสมอ แม้เจอหน้า) ---
                now = time.time()
                if now - last_jog_time >= GESTURE_INTERVAL:
                    status = shared_state.get_status()
                    current_target = status["target_servo_angle"]

                    if detected_sign in SERVO_RIGHT_SIGNS:
                        new_angle = min(current_target + SERVO_STEP, SERVO_MAX_ANGLE)
                        shared_state.set_target_servo_angle(new_angle)
                        last_jog_time = now
                        print(f"[Sign] T → Servo +{SERVO_STEP}° = {new_angle}°")
                    elif detected_sign in SERVO_LEFT_SIGNS:
                        new_angle = max(current_target - SERVO_STEP, SERVO_MIN_ANGLE)
                        shared_state.set_target_servo_angle(new_angle)
                        last_jog_time = now
                        print(f"[Sign] Y → Servo -{SERVO_STEP}° = {new_angle}°")
            else:
                sign_label = "NO HAND"


            # === อ่านค่าปัจจุบันสำหรับ OSD ===
            status = shared_state.get_status()
            m = status["motor_speed"]
            s = status["servo_angle"]

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

            # บรรทัดที่ 4: Sign detection result
            cv2.putText(frame, f"SIGN: {sign_label}", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            # บรรทัดที่ 5: FPS
            cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

            # Progress bar ความเร็ว Motor
            bar_width = int((m / 100) * 200)
            cv2.rectangle(frame, (10, 160), (210, 180), (50, 50, 50), -1)
            cv2.rectangle(frame, (10, 160), (10 + bar_width, 180), motor_color, -1)

            cv2.imshow('Smart Fan - Sign Language (Cloud)', frame)

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
