"""
test_sign_camera.py - ทดสอบ Sign Language Detection บน PC (ไม่ต้องมี hardware)

จำลองการทำงานเหมือน Project011 บน Pi 5:
  - ใช้ webcam แทน Pi Camera
  - แสดง OSD เหมือนจริง (Motor%, Servo°, Face, Sign)
  - จำลอง Motor / Servo ด้วยตัวแปร (ไม่ต้องมี GPIO)
  - ใช้ Roboflow Cloud API (ต้องต่อ internet)
  - ใช้ OpenCV Haar Cascade ตรวจจับหน้า (แทน MediaPipe)

วิธีใช้:
    cd testing
    pip install inference-sdk opencv-python
    python test_sign_camera.py
"""

import cv2
import time
import os
from inference_sdk import InferenceHTTPClient

# === Config ===
ROBOFLOW_API_KEY = "ekTKDcHd22SkTXRleX5r"
ROBOFLOW_MODEL_ID = "extrdb/2"
SIGN_CONFIDENCE = 0.70
GESTURE_INTERVAL = 0.3
SERVO_STEP = 5
SERVO_MIN_ANGLE = -90
SERVO_MAX_ANGLE = 90

# === Mapping: Sign → Action ===
SIGN_SPEED_MAP = {
    "s": 0.0,   # กำปั้น → Motor 0%
    "o": 0.0,   # วงกลม → Motor 0%
    "d": 0.3,   # ชี้ 1 นิ้ว → Motor 30%
    "x": 0.3,   # งอนิ้วชี้ → Motor 30%
    "v": 0.6,   # ชู 2 นิ้ว → Motor 60%
    "w": 1.0,   # ชู 3 นิ้ว → Motor 100%
}
SERVO_RIGHT_SIGNS = ["t"]  # Servo +5°
SERVO_LEFT_SIGNS = ["y"]   # Servo -5°

SIGN_DISPLAY = {
    "s": "S (fist) -> 0%",
    "o": "O (circle) -> 0%",
    "d": "D (point) -> 30%",
    "x": "X (hook) -> 30%",
    "v": "V (2 fingers) -> 60%",
    "w": "W (3 fingers) -> 100%",
    "t": "T -> Servo +5",
    "y": "Y -> Servo -5",
}

ALL_VALID = list(SIGN_SPEED_MAP.keys()) + SERVO_RIGHT_SIGNS + SERVO_LEFT_SIGNS


def main():
    print("=" * 60)
    print("  TEST MODE: Sign Language -> Smart Fan (No Hardware)")
    print("=" * 60)
    print("  Webcam + Roboflow Cloud API")
    print("=" * 60)
    print("  S,O = Motor 0%  |  D,X = Motor 30%")
    print("  V   = Motor 60% |  W   = Motor 100%")
    print("  T   = Servo +5  |  Y   = Servo -5")
    print("  'q' = quit      |  'r' = reset")
    print("=" * 60)

    # === Roboflow HTTP Client ===
    print("[Test] Connecting to Roboflow API...")
    client = InferenceHTTPClient(
        api_url="https://serverless.roboflow.com",
        api_key=ROBOFLOW_API_KEY
    )
    print("[Test] Roboflow API ready!")

    # === OpenCV Face Detection (Haar Cascade) ===
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    # === เปิด Webcam ===
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Test] เปิด Webcam ไม่ได้!")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("[Test] Webcam OK! Press 'q' to quit")

    # === ตัวแปรจำลอง Hardware ===
    sim_motor_speed = 0
    sim_servo_angle = 0

    last_jog_time = 0
    fps_time = time.time()
    fps_counter = 0
    current_fps = 0
    frame_skip = 0
    sign_label = "NO HAND"

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)

        # === FPS ===
        fps_counter += 1
        elapsed = time.time() - fps_time
        if elapsed >= 1.0:
            current_fps = fps_counter / elapsed
            fps_counter = 0
            fps_time = time.time()

        # === Face Detection (OpenCV Haar Cascade) ===
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        sim_face = len(faces) > 0

        for (fx, fy, fw, fh) in faces:
            cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), (0, 0, 255), 2)
            cv2.putText(frame, "FACE", (fx, fy - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # === Sign Language Detection (ทุก 5 frames เพราะ cloud มี delay) ===
        frame_skip += 1
        detected_sign = None

        if frame_skip >= 5:
            frame_skip = 0

            try:
                temp_path = "_temp_frame.jpg"
                cv2.imwrite(temp_path, frame)
                result = client.infer(temp_path, model_id=ROBOFLOW_MODEL_ID)

                best_conf = 0
                predictions = result.get("predictions", [])

                for pred in predictions:
                    cls_name = pred["class"].lower()
                    conf = pred["confidence"]

                    if cls_name in ALL_VALID and conf > best_conf:
                        detected_sign = cls_name
                        best_conf = conf

                if detected_sign:
                    display = SIGN_DISPLAY.get(detected_sign, detected_sign)
                    sign_label = f"{display} ({best_conf:.0%})"

                    # วาด bounding box
                    for pred in predictions:
                        if pred["class"].lower() == detected_sign:
                            x1 = int(pred["x"] - pred["width"] / 2)
                            y1 = int(pred["y"] - pred["height"] / 2)
                            x2 = int(pred["x"] + pred["width"] / 2)
                            y2 = int(pred["y"] + pred["height"] / 2)

                            is_servo = detected_sign in SERVO_RIGHT_SIGNS + SERVO_LEFT_SIGNS
                            color = (255, 165, 0) if is_servo else (0, 255, 0)

                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                            cv2.putText(frame, f"{detected_sign.upper()} {best_conf:.0%}",
                                        (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                            break

                    # --- จำลอง Motor ---
                    if detected_sign in SIGN_SPEED_MAP:
                        speed = SIGN_SPEED_MAP[detected_sign]
                        if sim_face:
                            sim_motor_speed = 0
                        else:
                            sim_motor_speed = int(speed * 100)

                    # --- จำลอง Servo ---
                    now = time.time()
                    if now - last_jog_time >= GESTURE_INTERVAL:
                        if detected_sign in SERVO_RIGHT_SIGNS:
                            sim_servo_angle = min(sim_servo_angle + SERVO_STEP, SERVO_MAX_ANGLE)
                            last_jog_time = now
                            print(f"[Servo] T -> +{SERVO_STEP} = {sim_servo_angle} deg")
                        elif detected_sign in SERVO_LEFT_SIGNS:
                            sim_servo_angle = max(sim_servo_angle - SERVO_STEP, SERVO_MIN_ANGLE)
                            last_jog_time = now
                            print(f"[Servo] Y -> -{SERVO_STEP} = {sim_servo_angle} deg")
                else:
                    sign_label = "NO HAND"

            except Exception as e:
                sign_label = f"API Error"
                print(f"[Test] API Error: {e}")

        # === OSD ===
        m = sim_motor_speed

        if sim_face:
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

        cv2.putText(frame, f"Servo: {sim_servo_angle} deg", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        if sim_face:
            cv2.putText(frame, "FACE: DETECTED", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "FACE: NONE", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.putText(frame, f"SIGN: {sign_label}", (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        # Progress bar Motor
        bar_width = int((m / 100) * 200)
        cv2.rectangle(frame, (10, 160), (210, 180), (50, 50, 50), -1)
        cv2.rectangle(frame, (10, 160), (10 + bar_width, 180), motor_color, -1)

        # Servo gauge
        gx = 250
        cv2.rectangle(frame, (gx, 160), (gx + 180, 180), (50, 50, 50), -1)
        sp = int((sim_servo_angle + 90) / 180 * 180)
        cv2.rectangle(frame, (gx + sp - 2, 158), (gx + sp + 2, 182), (0, 255, 0), -1)
        cv2.putText(frame, "Servo", (gx, 155),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        cv2.putText(frame, "[TEST MODE - No Hardware]", (10, 470),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 150, 255), 1)

        cv2.imshow('Smart Fan Test - Sign Language', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            sim_servo_angle = 0
            sim_motor_speed = 0
            print("[Test] Reset: Motor=0%, Servo=0 deg")

    face_detection.close() if hasattr(face_detection, 'close') else None
    cap.release()
    cv2.destroyAllWindows()

    if os.path.exists("_temp_frame.jpg"):
        os.remove("_temp_frame.jpg")

    print("[Test] Done!")


if __name__ == "__main__":
    main()
