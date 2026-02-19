"""
Project005: Camera + Servo + ADC + Motor + Face Detection (MediaPipe)
ต่อยอดจาก Project004:
1. กล้องทำงานตลอด + ตรวจจับใบหน้าด้วย MediaPipe
2. Servo หมุน 90° → 0° → -90° วนลูป
3. ADC ควบคุมความเร็ว Motor:
   - < 1V     = 0%
   - 1.0-1.6V = 30%
   - 1.6-2.0V = 60%
   - > 2V     = 100%
4. ⚠️ เมื่อเจอหน้าคน → Motor หยุดทันที (0%)
   เมื่อไม่เจอหน้า → Motor ทำงานตามค่า ADC ปกติ
"""

import cv2
import threading
import time
import board
import busio
import mediapipe as mp
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from gpiozero import AngularServo, PWMOutputDevice, DigitalOutputDevice
from gpiozero.pins.lgpio import LGPIOFactory

import warnings
warnings.filterwarnings("ignore")

# --- ใช้ LGPIOFactory สำหรับ Pi 5 ---
factory = LGPIOFactory()

# --- ค่าคงที่ Servo ---
SERVO_PIN = 18
MIN_PULSE = 0.0005
MAX_PULSE = 0.0025
SERVO_MIN = -90
SERVO_MAX = 90

# --- ค่าคงที่ ADC ---
ADC_CHANNEL = 0
ADC_INTERVAL = 0.3

# --- ค่าคงที่ Motor ---
PWM_PIN = 12
AIN1_PIN = 17
AIN2_PIN = 27

# --- Shared Variables ---
stop_event = threading.Event()
face_detected = threading.Event()  # ใหม่! สำหรับแจ้งเมื่อเจอหน้า
current_voltage = 0.0
current_motor_speed = 0
current_servo_angle = 0
data_lock = threading.Lock()

# --- Motor Objects (Global เพื่อให้ camera thread ควบคุมได้) ---
pwm_a = None
ain1 = None
ain2 = None
motor_lock = threading.Lock()


def get_motor_speed(voltage):
    """คำนวณความเร็ว Motor จากแรงดัน ADC"""
    if voltage < 1.0:
        return 0
    elif 1.0 <= voltage <= 1.6:
        return 0.3
    elif 1.6 < voltage <= 2.0:
        return 0.6
    else:
        return 1.0


def motor_control(speed):
    """ควบคุม Motor"""
    global pwm_a, ain1, ain2
    
    with motor_lock:
        if pwm_a is None:
            return
            
        if speed > 0:
            ain1.on()
            ain2.off()
            pwm_a.value = speed
        else:
            ain1.on()
            ain2.on()
            pwm_a.value = 0


def adc_motor_worker():
    """Thread สำหรับอ่านค่า ADC และควบคุม Motor"""
    global current_voltage, current_motor_speed, pwm_a, ain1, ain2
    
    try:
        # สร้าง I2C connection
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        ads.gain = 1
        chan = AnalogIn(ads, ADC_CHANNEL)
        
        # สร้าง Motor objects
        with motor_lock:
            pwm_a = PWMOutputDevice(PWM_PIN, pin_factory=factory)
            ain1 = DigitalOutputDevice(AIN1_PIN, pin_factory=factory)
            ain2 = DigitalOutputDevice(AIN2_PIN, pin_factory=factory)
        
        print(f"[ADC+Motor] เริ่มทำงาน - ADC ช่อง A{ADC_CHANNEL}")
        
        while not stop_event.is_set():
            try:
                # อ่านค่า ADC
                voltage = chan.voltage
                speed = get_motor_speed(voltage)
                
                with data_lock:
                    current_voltage = voltage
                
                # ตรวจสอบว่าเจอหน้าหรือไม่
                if face_detected.is_set():
                    # เจอหน้า -> หยุด Motor
                    motor_control(0)
                    with data_lock:
                        current_motor_speed = 0
                    print(f"[ADC+Motor] Voltage: {voltage:.2f}V -> Motor: 0% (FACE DETECTED!)")
                else:
                    # ไม่เจอหน้า -> ทำงานตาม ADC
                    motor_control(speed)
                    with data_lock:
                        current_motor_speed = int(speed * 100)
                    print(f"[ADC+Motor] Voltage: {voltage:.2f}V -> Motor: {int(speed*100)}%")
                
            except Exception as e:
                print(f"[ADC+Motor] Error: {e}")
            
            for _ in range(int(ADC_INTERVAL / 0.1)):
                if stop_event.is_set():
                    break
                time.sleep(0.1)
                
    except Exception as e:
        print(f"[ADC+Motor] เกิดข้อผิดพลาด: {e}")
    finally:
        motor_control(0)
        if i2c is not None:
            i2c.deinit()
        print("[ADC+Motor] ปิดการทำงาน")


def servo_worker():
    """Thread สำหรับควบคุม Servo หมุน 90° → 0° → -90° วนลูป"""
    global current_servo_angle
    
    angles = [90, 0, -90]
    
    try:
        servo = AngularServo(SERVO_PIN, 
                             min_angle=SERVO_MIN, 
                             max_angle=SERVO_MAX,
                             min_pulse_width=MIN_PULSE, 
                             max_pulse_width=MAX_PULSE,
                             pin_factory=factory)
        
        print("[Servo] เริ่มทำงาน (90° -> 0° -> -90°)")
        
        index = 0
        
        while not stop_event.is_set():
            angle = angles[index]
            servo.angle = angle
            
            with data_lock:
                current_servo_angle = angle
            
            print(f"[Servo] Angle: {angle}°")
            
            for _ in range(10):
                if stop_event.is_set():
                    break
                time.sleep(0.1)
            
            if stop_event.is_set():
                break
            
            index = (index + 1) % len(angles)
                
    except Exception as e:
        print(f"[Servo] เกิดข้อผิดพลาด: {e}")
    finally:
        try:
            servo.detach()
        except:
            pass
        print("[Servo] ปิดการทำงาน")


def camera_worker():
    """Thread สำหรับแสดงภาพจากกล้อง + Face Detection"""
    
    # สร้าง MediaPipe Face Detection
    mp_face = mp.solutions.face_detection
    mp_draw = mp.solutions.drawing_utils
    face_detection = mp_face.FaceDetection(
        model_selection=0,  # 0 = short range (2m), 1 = full range (5m)
        min_detection_confidence=0.5
    )
    
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    
    if not cap.isOpened():
        print("[Camera] ไม่สามารถเปิดกล้องได้")
        stop_event.set()
        return
    
    print("[Camera] เริ่มทำงาน + Face Detection (กด 'q' เพื่อออก)")
    
    try:
        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("[Camera] อ่านภาพไม่ได้")
                break
            
            # แปลง BGR → RGB สำหรับ MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # ตรวจจับใบหน้า
            results = face_detection.process(rgb_frame)
            
            # ตรวจสอบว่าเจอหน้าหรือไม่
            if results.detections:
                face_detected.set()  # แจ้งว่าเจอหน้า
                
                # วาดกรอบรอบใบหน้า
                for detection in results.detections:
                    mp_draw.draw_detection(frame, detection)
            else:
                face_detected.clear()  # ไม่เจอหน้า
            
            # อ่านค่าปัจจุบัน
            with data_lock:
                v = current_voltage
                m = current_motor_speed
                s = current_servo_angle
            
            # แสดงข้อมูลบนหน้าจอ
            if face_detected.is_set():
                motor_color = (0, 0, 255)  # แดง
                status = "MOTOR: 0% (FACE!)"
                face_status = "FACE: DETECTED"
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
                status = f"MOTOR: {m}%"
                face_status = "FACE: NONE"
                face_color = (0, 255, 0)
            
            cv2.putText(frame, f"Voltage: {v:.2f}V", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, status, (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, motor_color, 2)
            cv2.putText(frame, f"Servo: {s} deg", (10, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, face_status, (10, 120), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, face_color, 2)
            
            # วาด progress bar สำหรับ Motor
            bar_width = int((m / 100) * 200)
            cv2.rectangle(frame, (10, 130), (210, 150), (50, 50, 50), -1)
            cv2.rectangle(frame, (10, 130), (10 + bar_width, 150), motor_color, -1)
            
            cv2.imshow('Project005 - Face Detection', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set()
                break
                
    except Exception as e:
        print(f"[Camera] เกิดข้อผิดพลาด: {e}")
    finally:
        face_detection.close()
        cap.release()
        cv2.destroyAllWindows()
        print("[Camera] ปิดกล้องเรียบร้อย")


def main():
    """ฟังก์ชันหลัก"""
    print("=" * 60)
    print("Project005: Camera + Servo + ADC + Motor + Face Detection")
    print("=" * 60)
    print("1. กล้อง + Face Detection (MediaPipe)")
    print("2. Servo หมุน 90° -> 0° -> -90°")
    print("3. ADC ควบคุม Motor:")
    print("   - < 1.0V     = 0%")
    print("   - 1.0-1.6V   = 30%")
    print("   - 1.6-2.0V   = 60%")
    print("   - > 2.0V     = 100%")
    print("4. ⚠️ เจอหน้าคน -> Motor หยุดทันที!")
    print("=" * 60)
    print("กด 'q' บนหน้าต่างกล้องเพื่อออก")
    print("=" * 60)
    
    adc_motor_thread = threading.Thread(target=adc_motor_worker, daemon=True)
    servo_thread = threading.Thread(target=servo_worker, daemon=True)
    
    try:
        adc_motor_thread.start()
        servo_thread.start()
        camera_worker()
        
    except KeyboardInterrupt:
        print("\n[Main] กด Ctrl+C - กำลังหยุดโปรแกรม...")
    finally:
        stop_event.set()
        adc_motor_thread.join(timeout=2)
        servo_thread.join(timeout=2)
        print("[Main] ปิดโปรแกรมเรียบร้อย")


if __name__ == "__main__":
    main()
