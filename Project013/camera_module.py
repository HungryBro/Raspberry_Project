"""
camera_module.py - Pi Camera Module 3 + Dual AI Detection
  1. YOLO (local model) → ตรวจจับท่ามือ ASL → ควบคุม Motor (primary)
  2. MediaPipe Hands    → ตรวจจับหัวแม่มือ/ก้อย → ควบคุม Servo
                        → นับนิ้ว → cross-check กับ YOLO
  3. MediaPipe Face     → ตรวจจับหน้า → หยุด Motor ฉุกเฉิน

ระบบ Cross-Check:
  - ถ้า YOLO + MediaPipe เห็นตรงกัน → DUAL CONFIRM (มั่นใจสูง)
  - ถ้า YOLO เห็นอย่างเดียว        → YOLO ONLY
  - ถ้า MediaPipe เห็นอย่างเดียว    → MP ONLY (backup)
  - ถ้าไม่มีใครเห็น               → NO HAND

Servo Control (MediaPipe):
  - 👍 ชูหัวแม่มืออย่างเดียว (นิ้วอื่นงอ) → Servo +5°
  - 🤙 ชูก้อยอย่างเดียว (นิ้วอื่นงอ)       → Servo -5°
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
                    GESTURE_INTERVAL, SIGN_SPEED_MAP, FINGER_SPEED_MAP,
                    SIGN_TO_FINGERS)
import shared_state


# === แปลง sign class เป็น action อ่านง่าย ===
SIGN_DISPLAY = {
    "s": "S (fist)", "o": "O (circle)",
    "d": "D (point)", "x": "X (hook)",
    "v": "V (2 fingers)", "w": "W (3 fingers)",
}

ALL_VALID = list(SIGN_SPEED_MAP.keys())


def _count_fingers_detail(hand_landmarks, handedness_label):
    """นับจำนวนนิ้วที่ชูขึ้น + ตรวจสอบหัวแม่มือ/ก้อยแยก

    Returns:
        dict: {
            "total": int (0-5),
            "thumb": bool,
            "index": bool,
            "middle": bool,
            "ring": bool,
            "pinky": bool,
        }
    """
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

    print("[Camera] Dual AI Detection: YOLO (Motor) + MediaPipe (Servo) (กด 'q' เพื่อออก)")

    last_jog_time = 0
    fps_time = time.time()
    fps_counter = 0
    current_fps = 0
    frame_skip = 0

    # สถานะ detection
    yolo_sign = None
    yolo_conf = 0
    mp_fingers = -1          # -1 = ไม่เจอมือ
    mp_detail = None         # finger detail dict
    detection_mode = "NONE"  # DUAL / YOLO / MP / NONE
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
            rgb_frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2RGB_I420)

            # === FPS ===
            fps_counter += 1
            elapsed = time.time() - fps_time
            if elapsed >= 1.0:
                current_fps = fps_counter / elapsed
                fps_counter = 0
                fps_time = time.time()

            # === Face Detection (ทุก frame) ===
            face_results = face_detection.process(rgb_frame)
            has_face = False
            if face_results.detections:
                has_face = True
                shared_state.face_detected.set()
                for det in face_results.detections:
                    mp_draw.draw_detection(frame, det)
            else:
                shared_state.face_detected.clear()

            # === Dual AI Detection (ทุก 2 frames) ===
            frame_skip += 1
            if frame_skip >= 2:
                frame_skip = 0
                servo_label = ""

                # --- AI #1: YOLO Sign Language (Motor) ---
                yolo_sign = None
                yolo_conf = 0
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

                    # วาด bounding box YOLO
                    if yolo_sign:
                        for box in yolo_results[0].boxes:
                            cls_id = int(box.cls[0])
                            if yolo_model.names[cls_id].lower() == yolo_sign:
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                cv2.putText(frame, f"YOLO:{yolo_sign.upper()} {yolo_conf:.0%}",
                                            (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                break

                # --- AI #2: MediaPipe Hands (Servo + Cross-Check) ---
                mp_fingers = -1
                mp_detail = None
                hand_results = hands.process(rgb_frame)

                if hand_results.multi_hand_landmarks:
                    for idx, hlm in enumerate(hand_results.multi_hand_landmarks):
                        # วาด landmarks
                        mp_lib.solutions.drawing_utils.draw_landmarks(
                            frame, hlm, mp_hands.HAND_CONNECTIONS,
                            mp_lib.solutions.drawing_styles.get_default_hand_landmarks_style(),
                            mp_lib.solutions.drawing_styles.get_default_hand_connections_style()
                        )
                        # นับนิ้ว (แบบละเอียด)
                        label = hand_results.multi_handedness[idx].classification[0].label
                        mp_detail = _count_fingers_detail(hlm, label)
                        mp_fingers = mp_detail["total"]

                # === Servo Control: MediaPipe (หัวแม่มือ / ก้อย) ===
                servo_action = None  # "right" or "left" or None

                if mp_detail:
                    thumb = mp_detail["thumb"]
                    index = mp_detail["index"]
                    middle = mp_detail["middle"]
                    ring = mp_detail["ring"]
                    pinky = mp_detail["pinky"]

                    # 👍 หัวแม่มือชูอย่างเดียว (นิ้วอื่นงอหมด) → Servo +5°
                    if thumb and not index and not middle and not ring and not pinky:
                        servo_action = "right"
                        servo_label = "SERVO: 👍 Thumb +5°"

                    # 🤙 ก้อยชูอย่างเดียว (นิ้วอื่นงอหมด) → Servo -5°
                    elif pinky and not thumb and not index and not middle and not ring:
                        servo_action = "left"
                        servo_label = "SERVO: 🤙 Pinky -5°"

                # ดำเนินการ Servo
                if servo_action:
                    now = time.time()
                    if now - last_jog_time >= GESTURE_INTERVAL:
                        status = shared_state.get_status()
                        current_target = status["target_servo_angle"]

                        if servo_action == "right":
                            new_angle = min(current_target + SERVO_STEP, SERVO_MAX_ANGLE)
                            shared_state.set_target_servo_angle(new_angle)
                            last_jog_time = now
                            print(f"[MP Servo] 👍 Thumb → +{SERVO_STEP}° = {new_angle}°")
                        elif servo_action == "left":
                            new_angle = max(current_target - SERVO_STEP, SERVO_MIN_ANGLE)
                            shared_state.set_target_servo_angle(new_angle)
                            last_jog_time = now
                            print(f"[MP Servo] 🤙 Pinky → -{SERVO_STEP}° = {new_angle}°")

                # === Motor Cross-Check Logic (YOLO + MediaPipe) ===
                yolo_expected_fingers = SIGN_TO_FINGERS.get(yolo_sign, -1) if yolo_sign else -1
                final_speed = None

                if yolo_sign and mp_fingers >= 0 and not servo_action:
                    # ทั้ง 2 ตัวเห็น (ไม่ใช่ Servo mode)
                    if yolo_expected_fingers == mp_fingers:
                        # เห็นตรงกัน!
                        detection_mode = "DUAL CONFIRM"
                        final_speed = SIGN_SPEED_MAP.get(yolo_sign)
                    else:
                        # ไม่ตรงกัน → ใช้ YOLO (primary)
                        detection_mode = "DUAL (YOLO)"
                        final_speed = SIGN_SPEED_MAP.get(yolo_sign)

                elif yolo_sign and not servo_action:
                    # YOLO อย่างเดียว
                    detection_mode = "YOLO"
                    if yolo_sign in SIGN_SPEED_MAP:
                        final_speed = SIGN_SPEED_MAP[yolo_sign]

                elif mp_fingers >= 0 and not servo_action:
                    # MediaPipe อย่างเดียว (backup motor)
                    detection_mode = "MP BACKUP"
                    if mp_fingers in FINGER_SPEED_MAP:
                        final_speed = FINGER_SPEED_MAP[mp_fingers]

                elif servo_action:
                    detection_mode = "MP SERVO"

                else:
                    detection_mode = "NONE"

                # --- สร้าง action label ---
                parts = []
                if yolo_sign:
                    parts.append(f"YOLO:{yolo_sign.upper()}")
                if mp_fingers >= 0:
                    parts.append(f"MP:{mp_fingers}f")
                if parts:
                    action_label = f"{' + '.join(parts)} [{detection_mode}]"
                else:
                    action_label = "NO HAND"

                # --- ควบคุม Motor ---
                if final_speed is not None:
                    if has_face:
                        shared_state.set_target_speed(0.0)
                        shared_state.set_finger_count(0)
                    else:
                        shared_state.set_target_speed(final_speed)
                        shared_state.set_finger_count(mp_fingers if mp_fingers >= 0 else 0)

            # === OSD ===
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

            # Dual AI result
            if "DUAL CONFIRM" in detection_mode:
                ai_color = (0, 255, 0)       # เขียว = ทั้ง 2 ตัวเห็นตรงกัน
            elif "DUAL" in detection_mode:
                ai_color = (255, 255, 0)     # เหลือง = ทั้ง 2 ตัว (ไม่ตรง)
            elif "YOLO" in detection_mode:
                ai_color = (0, 200, 255)     # ส้ม = YOLO อย่างเดียว
            elif "MP" in detection_mode:
                ai_color = (255, 165, 0)     # ฟ้า/ส้ม = MediaPipe
            else:
                ai_color = (128, 128, 128)   # เทา = ไม่เจอ

            cv2.putText(frame, f"AI: {action_label}", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, ai_color, 2)

            # FPS
            cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

            # Progress bar Motor
            bar_width = int((m / 100) * 200)
            cv2.rectangle(frame, (10, 160), (210, 180), (50, 50, 50), -1)
            cv2.rectangle(frame, (10, 160), (10 + bar_width, 180), motor_color, -1)

            cv2.imshow('Smart Fan - Dual AI (YOLO + MediaPipe)', frame)

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
