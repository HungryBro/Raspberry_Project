"""
camera_module.py - Pi Camera Module 3 + Dual AI Detection
  1. YOLO (local model) → ตรวจจับท่ามือ ASL → ควบคุม Motor (Exclusive)
  2. MediaPipe Hands    → ตรวจจับหัวแม่มือ/ก้อย → ควบคุม Servo (Exclusive)
  3. MediaPipe Face     → ตรวจจับหน้า → หยุด Motor ฉุกเฉิน

Optimization (Frame Skipping):
  - Face: ตรวจทุก 5 เฟรม
  - YOLO: ตรวจทุก 5 เฟรม
  - Hands: ตรวจทุก 3 เฟรม
"""

import cv2
import numpy as np
import subprocess
import time
import os
import mediapipe as mp_lib
from ultralytics import YOLO
from config import (CAMERA_WIDTH, CAMERA_HEIGHT, FACE_MODEL, FACE_CONFIDENCE,
                    HAND_MAX_NUM, HAND_CONFIDENCE, HAND_TRACKING,
                    YOLO_MODEL_PATH, YOLO_CONFIDENCE, YOLO_IMG_SIZE,
                    SERVO_STEP, SERVO_MIN_ANGLE, SERVO_MAX_ANGLE,
                    GESTURE_INTERVAL, SIGN_SPEED_MAP, SKIP_FACE, SKIP_YOLO, SKIP_HANDS)
import shared_state


# === แปลง sign class เป็น action อ่านง่าย ===
SIGN_DISPLAY = {
    "s": "0 (Stop)",
    "o": "0 (Stop)",
    "d": "1 (Low)",
    "x": "1 (Low)",
    "v": "2 (Medium)",
    "w": "3 (High)",
}

ALL_VALID = list(SIGN_SPEED_MAP.keys())


def _count_fingers_detail(hand_landmarks, handedness_label):
    """นับจำนวนนิ้วที่ชูขึ้น + ตรวจสอบหัวแม่มือ/ก้อยแยก"""
    lm = hand_landmarks.landmark

    # หัวแม่มือ (แกน X)
    thumb_tip = lm[mp_lib.solutions.hands.HandLandmark.THUMB_TIP]
    thumb_ip = lm[mp_lib.solutions.hands.HandLandmark.THUMB_IP]

    if handedness_label == "Right":
        thumb_up = thumb_tip.x < thumb_ip.x
    else:
        thumb_up = thumb_tip.x > thumb_ip.x

    # นิ้วชี้
    index_up = lm[mp_lib.solutions.hands.HandLandmark.INDEX_FINGER_TIP].y < \
               lm[mp_lib.solutions.hands.HandLandmark.INDEX_FINGER_PIP].y

    # นิ้วกลาง
    middle_up = lm[mp_lib.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP].y < \
                lm[mp_lib.solutions.hands.HandLandmark.MIDDLE_FINGER_PIP].y

    # นิ้วนาง
    ring_up = lm[mp_lib.solutions.hands.HandLandmark.RING_FINGER_TIP].y < \
              lm[mp_lib.solutions.hands.HandLandmark.RING_FINGER_PIP].y

    # ก้อย
    pinky_up = lm[mp_lib.solutions.hands.HandLandmark.PINKY_TIP].y < \
               lm[mp_lib.solutions.hands.HandLandmark.PINKY_PIP].y

    total = sum([thumb_up, index_up, middle_up, ring_up, pinky_up])

    return {
        "total": total,
        "thumb": thumb_up,
        "index": index_up,
        "middle": middle_up,
        "ring": ring_up,
        "pinky": pinky_up,
    }


def camera_worker():
    """Thread (Main): Dual AI Detection - YOLO + MediaPipe"""

    # === MediaPipe Face Detection ===
    mp_face = mp_lib.solutions.face_detection
    mp_draw = mp_lib.solutions.drawing_utils
    face_detection = mp_face.FaceDetection(
        model_selection=FACE_MODEL,
        min_detection_confidence=FACE_CONFIDENCE
    )

    # === MediaPipe Hands ===
    mp_hands = mp_lib.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=HAND_MAX_NUM,
        min_detection_confidence=HAND_CONFIDENCE,
        min_tracking_confidence=HAND_TRACKING
    )

    # === โหลด YOLO Model (local) ===
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, YOLO_MODEL_PATH)

    print(f"[Camera] โหลด YOLO model: {model_path}")
    yolo_model = YOLO(model_path)
    print(f"[Camera] YOLO loaded! Classes: {yolo_model.names}")

    # === เปิด Pi Camera ===
    print("[Camera] เปิด Pi Camera Module 3 (rpicam-vid)...")

    cmd = [
        'rpicam-vid', '-t', '0',
        '--width', str(CAMERA_WIDTH), '--height', str(CAMERA_HEIGHT),
        '--codec', 'yuv420', '--framerate', '30', '-n', '-o', '-'
    ]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("[Camera] ไม่พบ rpicam-vid!")
        shared_state.stop_event.set()
        return
    except Exception as e:
        print(f"[Camera] เปิดกล้องไม่ได้: {e}")
        shared_state.stop_event.set()
        return

    yuv_frame_size = CAMERA_WIDTH * CAMERA_HEIGHT * 3 // 2

    print("[Camera] Dual AI Optimization Mode (Skipping Frames)")
    print(f"  - Face Check: ทุก {SKIP_FACE} frames")
    print(f"  - YOLO Check: ทุก {SKIP_YOLO} frames")
    print(f"  - Hands Check: ทุก {SKIP_HANDS} frames")

    last_jog_time = 0
    fps_time = time.time()
    fps_counter = 0
    current_fps = 0
    
    # Frame Counters
    frame_cnt_face = 0
    frame_cnt_yolo = 0
    frame_cnt_hands = 0

    # สถานะ detection (เก็บค่าไว้ใช้ข้ามเฟรม)
    yolo_sign = None
    yolo_conf = 0
    yolo_box_coords = None  # เก็บตำแหน่ง box ล่าสุด

    mp_fingers = -1          # -1 = ไม่เจอมือ
    mp_detail = None         # finger detail dict
    mp_landmarks = None      # เก็บ landmarks ล่าสุดเพื่อวาด
    
    has_face = False
    face_detections = None   # เก็บ face detection ล่าสุด

    detection_mode = "NONE"  # YOLO / MP SERVO / NONE
    action_label = "NO HAND"
    servo_label = ""         # สำหรับ OSD

    try:
        while not shared_state.stop_event.is_set():
            raw_data = proc.stdout.read(yuv_frame_size)
            if len(raw_data) != yuv_frame_size:
                break

            yuv_frame = np.frombuffer(raw_data, dtype=np.uint8).reshape(
                (CAMERA_HEIGHT * 3 // 2, CAMERA_WIDTH)
            )
            frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)
            frame = cv2.flip(frame, 1)  # กลับด้านกล้อง (Mirror)
            rgb_frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2RGB_I420)

            # === FPS ===
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
            
            # วาด Face (ใช้ผลล่าสุด)
            if face_detections:
                for det in face_detections:
                    mp_draw.draw_detection(frame, det)


            # ==========================================
            # 2. YOLO Sign Language (Every SKIP_YOLO frames)
            # ==========================================
            frame_cnt_yolo += 1
            if frame_cnt_yolo >= SKIP_YOLO:
                frame_cnt_yolo = 0
                
                # Reset ค่าเก่าก่อน detect ใหม่
                yolo_sign = None
                yolo_conf = 0
                yolo_box_coords = None

                yolo_results = yolo_model(frame, imgsz=YOLO_IMG_SIZE,
                                          conf=YOLO_CONFIDENCE, verbose=False)

                if yolo_results and len(yolo_results[0].boxes) > 0:
                    for box in yolo_results[0].boxes:
                        cls_id = int(box.cls[0])
                        cls_name = yolo_model.names[cls_id].lower()
                        conf = float(box.conf[0])
                        
                        if cls_name in ALL_VALID and conf > yolo_conf:
                            yolo_sign = cls_name
                            yolo_conf = conf
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            yolo_box_coords = (x1, y1, x2, y2)
            
            # วาด YOLO Box (ใช้ผลล่าสุด)
            if yolo_box_coords and yolo_sign:
                x1, y1, x2, y2 = yolo_box_coords
                
                # ใช้ SIGN_DISPLAY เพื่อแสดงเป็นตัวเลข (d=1, s=0 ฯลฯ)
                display_text = SIGN_DISPLAY.get(yolo_sign, yolo_sign.upper())
                # ตัดเอาเฉพาะส่วนหน้า "0", "1" ถ้าต้องการ หรือจะโชว์เต็มๆ "0 (Stop)" ก็ได้
                # ในที่นี้โชว์ตามที่ config ไว้น่าจะสวยกว่า
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"YOLO:{display_text}",
                            (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)


            # ==========================================
            # 3. MediaPipe Hands (Every SKIP_HANDS frames)
            # ==========================================
            frame_cnt_hands += 1
            if frame_cnt_hands >= SKIP_HANDS:
                frame_cnt_hands = 0
                servo_label = ""
                
                mp_fingers = -1
                mp_detail = None
                mp_landmarks = None

                hand_results = hands.process(rgb_frame)

                if hand_results.multi_hand_landmarks:
                    # เอาแค่มือแรก
                    hlm = hand_results.multi_hand_landmarks[0]
                    mp_landmarks = hlm
                    
                    label = hand_results.multi_handedness[0].classification[0].label
                    mp_detail = _count_fingers_detail(hlm, label)
                    mp_fingers = mp_detail["total"]

            # วาด Hands (ใช้ผลล่าสุด) -- แสดงเฉพาะเมื่อ *ไม่เจอ* YOLO Sign
            if mp_landmarks and not yolo_sign:
                mp_lib.solutions.drawing_utils.draw_landmarks(
                    frame, mp_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_lib.solutions.drawing_styles.get_default_hand_landmarks_style(),
                    mp_lib.solutions.drawing_styles.get_default_hand_connections_style()
                )


            # ==========================================
            # Logic & Control (Update every frame based on latest state)
            # ==========================================
            
            # --- Servo Control Logic (MediaPipe Only) ---
            servo_action = None  # "right" or "left" or None

            if mp_detail:
                thumb = mp_detail["thumb"]
                index = mp_detail["index"]
                middle = mp_detail["middle"]
                ring = mp_detail["ring"]
                pinky = mp_detail["pinky"]

                # 👍 หัวแม่มือชูอย่างเดียว (นิ้วอื่นงอหมด)
                if thumb and not index and not middle and not ring and not pinky:
                    servo_action = "right"
                    servo_label = "SERVO: 👍 Thumb +5°"

                # 🤙 ก้อยชูอย่างเดียว (นิ้วอื่นงอหมด)
                elif pinky and not thumb and not index and not middle and not ring:
                    servo_action = "left"
                    servo_label = "SERVO: 🤙 Pinky -5°"
                else:
                    servo_label = "" # Clear label if hand is present but not servo gesture

            # ดำเนินการ Servo (check timer)
            if servo_action:
                now = time.time()
                if now - last_jog_time >= GESTURE_INTERVAL:
                    status = shared_state.get_status()
                    current_target = status["target_servo_angle"]

                    if servo_action == "right":
                        new_angle = min(current_target + SERVO_STEP, SERVO_MAX_ANGLE)
                        shared_state.set_target_servo_angle(new_angle)
                        last_jog_time = now
                    elif servo_action == "left":
                        new_angle = max(current_target - SERVO_STEP, SERVO_MIN_ANGLE)
                        shared_state.set_target_servo_angle(new_angle)
                        last_jog_time = now


            # --- Motor Logic (YOLO Only - No Cross Check) ---
            final_speed = None

            if yolo_sign and not servo_action:
                detection_mode = "YOLO"
                if yolo_sign in SIGN_SPEED_MAP:
                    final_speed = SIGN_SPEED_MAP[yolo_sign]
            
            elif servo_action:
                detection_mode = "MP SERVO"

            else:
                detection_mode = "NONE"


            # --- สร้าง action label ---
            parts = []
            if yolo_sign:
                parts.append(f"YOLO:{yolo_sign.upper()}")
            
            if parts:
                action_label = f"{' + '.join(parts)} [{detection_mode}]"
            else:
                action_label = "NO HAND"


            # --- สั่งงาน Motor Shared State ---
            if final_speed is not None:
                if has_face:
                    shared_state.set_target_speed(0.0)
                    shared_state.set_finger_count(0)
                else:
                    shared_state.set_target_speed(final_speed)
                    # Translate YOLO sign to arbitrary finger count for display if needed, 
                    # but here we just pass 0 or maybe mapped number for UI consisteny
                    # (optional: mapping logic kept simple)
                    finger_map = {"0":0,"0":0,"1":1,"1":1,"2":2,"3":3}
                    shared_state.set_finger_count(finger_map.get(yolo_sign, 0))


            # ==========================================
            # OSD Display
            # ==========================================
            status = shared_state.get_status()
            m = status["motor_speed"]
            s = status["servo_angle"]

            # Motor
            if has_face:
                motor_color = (0, 0, 255)
                motor_text = "MOTOR: 0% (FACE!)"
            else:
                if m == 0:   motor_color = (128, 128, 128)
                elif m <= 30: motor_color = (0, 255, 255)
                elif m <= 60: motor_color = (0, 165, 255)
                else:         motor_color = (0, 0, 255)
                motor_text = f"MOTOR: {m}%"

            cv2.putText(frame, motor_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, motor_color, 2)

            # Servo
            cv2.putText(frame, f"Servo: {s} deg", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Servo action (thumb/pinky)
            if servo_label:
                cv2.putText(frame, servo_label, (10, CAMERA_HEIGHT - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)

            # Face
            face_color = (0, 0, 255) if has_face else (0, 255, 0)
            face_text = "FACE: DETECTED" if has_face else "FACE: NONE"
            cv2.putText(frame, face_text, (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, face_color, 2)

            # AI Result
            if "YOLO" in detection_mode:
                ai_color = (0, 255, 0)       # เขียว
            elif "MP" in detection_mode:
                ai_color = (255, 165, 0)     # ส้ม
            else:
                ai_color = (128, 128, 128)   # เทา

            cv2.putText(frame, f"AI: {action_label}", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, ai_color, 2)

            # FPS
            cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

            # Progress bar Motor
            bar_width = int((m / 100) * 200)
            cv2.rectangle(frame, (10, 160), (210, 180), (50, 50, 50), -1)
            cv2.rectangle(frame, (10, 160), (10 + bar_width, 180), motor_color, -1)

            cv2.imshow('Smart Fan - Dual AI (No Cross-Check)', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                shared_state.stop_event.set()
                break

    except Exception as e:
        print(f"[Camera] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        face_detection.close()
        hands.close()
        proc.terminate()
        proc.wait()
        cv2.destroyAllWindows()
        print("[Camera] ปิดกล้อง")
