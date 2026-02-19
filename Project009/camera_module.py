"""
<<<<<<< HEAD
camera_module.py - Pi Camera Module 3 + Face Detection + Hand Gesture (MediaPipe)
ใช้ rpicam-vid (pipe YUV420 → OpenCV) รองรับ pyenv Python

รองรับ 2 โหมด:
  - Mode ADC:     Face Detection อย่างเดียว (เหมือนเดิม)
  - Mode Gesture:  Face Detection + Hand Gesture Control
=======
camera_module.py - Pi Camera Module 3 + Face Detection (MediaPipe)
ใช้ rpicam-vid (pipe YUV420 → OpenCV) รองรับ pyenv Python
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
"""

import cv2
import numpy as np
import subprocess
<<<<<<< HEAD
import time
import mediapipe as mp_lib
from config import (CAMERA_WIDTH, CAMERA_HEIGHT, FACE_MODEL, FACE_CONFIDENCE,
                    CONTROL_MODE, HAND_MODEL_COMPLEXITY, HAND_CONFIDENCE,
                    HAND_TRACKING_CONFIDENCE, SERVO_STEP, SERVO_MIN_ANGLE,
                    SERVO_MAX_ANGLE, GESTURE_INTERVAL)
import shared_state


def _count_fingers(hand_landmarks):
    """นับจำนวนนิ้วที่ชูขึ้น จาก MediaPipe Hand Landmarks

    Returns:
        dict: {
            "index": bool,   "middle": bool,  "ring": bool,
            "thumb": bool,   "pinky": bool,
            "speed_fingers": int (0-3, นิ้วชี้+กลาง+นาง),
        }
    """
    lm = hand_landmarks.landmark

    # นิ้วชี้: ปลายนิ้ว (8) สูงกว่าข้อ PIP (6)
    index_up = lm[8].y < lm[6].y

    # นิ้วกลาง: ปลายนิ้ว (12) สูงกว่าข้อ PIP (10)
    middle_up = lm[12].y < lm[10].y

    # นิ้วนาง: ปลายนิ้ว (16) สูงกว่าข้อ PIP (14)
    ring_up = lm[16].y < lm[14].y

    # หัวแม่มือ: ปลายนิ้ว (4) ห่างจากโคนนิ้วชี้ (5) ในแนวนอน
    thumb_up = abs(lm[4].x - lm[5].x) > 0.05

    # นิ้วก้อย: ปลายนิ้ว (20) สูงกว่าข้อ PIP (18)
    pinky_up = lm[20].y < lm[18].y

    # นับเฉพาะนิ้วชี้ + กลาง + นาง สำหรับควบคุมความเร็ว
    speed_fingers = sum([index_up, middle_up, ring_up])

    return {
        "index": index_up,
        "middle": middle_up,
        "ring": ring_up,
        "thumb": thumb_up,
        "pinky": pinky_up,
        "speed_fingers": speed_fingers,
    }


def _speed_from_fingers(count):
    """แปลงจำนวนนิ้ว (0-3) เป็นความเร็ว Motor (0.0-1.0)
    0 นิ้ว (กำปั้น) = 0%
    1 นิ้ว (ชี้)     = 30%
    2 นิ้ว (ชี้+กลาง) = 60%
    3 นิ้ว (ชี้+กลาง+นาง) = 100%
    """
    mapping = {0: 0.0, 1: 0.3, 2: 0.6, 3: 1.0}
    return mapping.get(count, 0.0)


def camera_worker():
    """Thread (Main): เปิด Pi Camera ผ่าน rpicam-vid + ตรวจจับใบหน้า + ท่ามือ + แสดง OSD"""

    # === สร้าง MediaPipe Face Detection ===
=======
import mediapipe as mp_lib
from config import CAMERA_WIDTH, CAMERA_HEIGHT, FACE_MODEL, FACE_CONFIDENCE
import shared_state


def camera_worker():
    """Thread (Main): เปิด Pi Camera ผ่าน rpicam-vid + ตรวจจับใบหน้า + แสดง OSD"""
    
    # สร้าง MediaPipe Face Detection
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
    mp_face = mp_lib.solutions.face_detection
    mp_draw = mp_lib.solutions.drawing_utils
    face_detection = mp_face.FaceDetection(
        model_selection=FACE_MODEL,
        min_detection_confidence=FACE_CONFIDENCE
    )
<<<<<<< HEAD

    # === สร้าง MediaPipe Hands (เฉพาะ Mode Gesture) ===
    hand_detection = None
    mp_hands = None
    mp_drawing_styles = None

    if CONTROL_MODE == "gesture":
        mp_hands = mp_lib.solutions.hands
        mp_drawing_styles = mp_lib.solutions.drawing_styles
        hand_detection = mp_hands.Hands(
            model_complexity=HAND_MODEL_COMPLEXITY,
            max_num_hands=1,
            min_detection_confidence=HAND_CONFIDENCE,
            min_tracking_confidence=HAND_TRACKING_CONFIDENCE,
        )

    # === เปิด Pi Camera ผ่าน rpicam-vid ===
    print("[Camera] กำลังเปิด Pi Camera Module 3 (rpicam-vid)...")

=======
    
    # เปิด Pi Camera ผ่าน rpicam-vid (pipe YUV420 ออกมา)
    print("[Camera] กำลังเปิด Pi Camera Module 3 (rpicam-vid)...")
    
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
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
<<<<<<< HEAD

=======
    
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
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
<<<<<<< HEAD

    # ขนาด YUV420 frame = width * height * 1.5
    yuv_frame_size = CAMERA_WIDTH * CAMERA_HEIGHT * 3 // 2

    mode_text = "GESTURE" if CONTROL_MODE == "gesture" else "ADC"
    print(f"[Camera] เริ่มทำงาน (Mode: {mode_text}) + Face Detection (กด 'q' เพื่อออก)")

    last_jog_time = 0  # ป้องกัน Servo กระตุก

    try:
        while not shared_state.stop_event.is_set():
            # === อ่าน YUV420 frame จาก rpicam-vid ===
            raw_data = proc.stdout.read(yuv_frame_size)

            if len(raw_data) != yuv_frame_size:
                print("[Camera] อ่านภาพไม่ได้ (rpicam-vid หยุดทำงาน)")
                break

=======
    
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
            
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
            # แปลง YUV420 → BGR (สำหรับ OpenCV แสดงผล)
            yuv_frame = np.frombuffer(raw_data, dtype=np.uint8).reshape(
                (CAMERA_HEIGHT * 3 // 2, CAMERA_WIDTH)
            )
            frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_I420)
<<<<<<< HEAD

            # แปลง YUV420 → RGB (สำหรับ MediaPipe)
            rgb_frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2RGB_I420)

            # === Priority 1: Face Detection ===
            face_results = face_detection.process(rgb_frame)

            if face_results.detections:
                shared_state.face_detected.set()
                for detection in face_results.detections:
                    mp_draw.draw_detection(frame, detection)

                # Mode Gesture: เจอหน้า → บังคับ speed = 0
                if CONTROL_MODE == "gesture":
                    shared_state.set_target_speed(0.0)
                    shared_state.set_finger_count(0)
            else:
                shared_state.face_detected.clear()

            # === Priority 2 & 3: Hand Gesture (เฉพาะ Mode Gesture + ไม่เจอหน้า) ===
            if CONTROL_MODE == "gesture" and hand_detection is not None:
                if not shared_state.face_detected.is_set():
                    hand_results = hand_detection.process(rgb_frame)

                    if hand_results.multi_hand_landmarks:
                        for hand_lm in hand_results.multi_hand_landmarks:
                            # วาดโครงกระดูกมือ
                            mp_draw.draw_landmarks(
                                frame, hand_lm, mp_hands.HAND_CONNECTIONS,
                                mp_drawing_styles.get_default_hand_landmarks_style(),
                                mp_drawing_styles.get_default_hand_connections_style()
                            )

                            # นับนิ้ว
                            fingers = _count_fingers(hand_lm)
                            speed_fingers = fingers["speed_fingers"]

                            # อัปเดตความเร็ว Motor
                            speed = _speed_from_fingers(speed_fingers)
                            shared_state.set_target_speed(speed)
                            shared_state.set_finger_count(speed_fingers)

                            # Servo Jog (หัวแม่มือ / นิ้วก้อย) พร้อม debounce
                            now = time.time()
                            if now - last_jog_time >= GESTURE_INTERVAL:
                                status = shared_state.get_status()
                                current_target = status["target_servo_angle"]

                                if fingers["thumb"] and not fingers["pinky"]:
                                    new_angle = min(current_target + SERVO_STEP, SERVO_MAX_ANGLE)
                                    shared_state.set_target_servo_angle(new_angle)
                                    last_jog_time = now
                                elif fingers["pinky"] and not fingers["thumb"]:
                                    new_angle = max(current_target - SERVO_STEP, SERVO_MIN_ANGLE)
                                    shared_state.set_target_servo_angle(new_angle)
                                    last_jog_time = now

                            break  # ใช้แค่มือแรก
                    else:
                        # ไม่เจอมือ → ไม่เปลี่ยน speed/servo (คงค่าเดิม)
                        pass

            # === อ่านค่าปัจจุบันสำหรับ OSD ===
=======
            
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
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
            status = shared_state.get_status()
            v = status["voltage"]
            m = status["motor_speed"]
            s = status["servo_angle"]
            has_face = status["face"]
<<<<<<< HEAD
            fc = status["finger_count"]

            # === แสดง OSD ===

            # บรรทัดที่ 1: โหมด
            cv2.putText(frame, f"MODE: {mode_text}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)

            # บรรทัดที่ 2: แรงดัน (แสดงเสมอ)
            cv2.putText(frame, f"Voltage: {v:.2f}V", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # บรรทัดที่ 3: Motor
            if has_face:
                motor_color = (0, 0, 255)
                motor_text = "MOTOR: 0% (FACE!)"
=======
            
            # แสดงข้อมูลบนหน้าจอ
            if has_face:
                motor_color = (0, 0, 255)
                motor_text = "MOTOR: 0% (FACE!)"
                face_text = "FACE: DETECTED"
                face_color = (0, 0, 255)
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
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
<<<<<<< HEAD

            cv2.putText(frame, motor_text, (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, motor_color, 2)

            # บรรทัดที่ 4: Servo
            cv2.putText(frame, f"Servo: {s} deg", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # บรรทัดที่ 5: Face
            if has_face:
                face_text = "FACE: DETECTED"
                face_color = (0, 0, 255)
            else:
                face_text = "FACE: NONE"
                face_color = (0, 255, 0)

            cv2.putText(frame, face_text, (10, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, face_color, 2)

            # บรรทัดที่ 6: Fingers (เฉพาะ Mode Gesture)
            if CONTROL_MODE == "gesture":
                cv2.putText(frame, f"Fingers: {fc}", (10, 180),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            # Progress bar ความเร็ว Motor
            bar_y = 190 if CONTROL_MODE == "gesture" else 160
            bar_width = int((m / 100) * 200)
            cv2.rectangle(frame, (10, bar_y), (210, bar_y + 20), (50, 50, 50), -1)
            cv2.rectangle(frame, (10, bar_y), (10 + bar_width, bar_y + 20), motor_color, -1)

            cv2.imshow('Smart Fan - AI Control', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                shared_state.stop_event.set()
                break

=======
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
                
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
    except Exception as e:
        print(f"[Camera] เกิดข้อผิดพลาด: {e}")
    finally:
        face_detection.close()
<<<<<<< HEAD
        if hand_detection is not None:
            hand_detection.close()
=======
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
        proc.terminate()
        proc.wait()
        cv2.destroyAllWindows()
        print("[Camera] ปิดกล้องเรียบร้อย")
