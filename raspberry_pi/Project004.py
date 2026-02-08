"""
Project004: Camera + Servo + ADC + Motor Driver
ต่อยอดจาก Project003:
1. กล้องทำงานตลอด
2. Servo หมุน -90° ถึง 90° ทีละ 10°
3. ADC ควบคุมความเร็ว Motor:
   - < 1V     = 0%
   - 1.1-1.6V = 30%
   - 1.7-2.0V = 60%
   - > 2V     = 100%
"""

import cv2
import threading
import time
import board
import busio
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
SERVO_STEP = 10  # ขยับทีละ 10 องศา
SERVO_MIN = -90
SERVO_MAX = 90

# --- ค่าคงที่ ADC ---
ADC_CHANNEL = 0
ADC_INTERVAL = 0.3  # อ่านค่าทุก 0.3 วินาที

# --- ค่าคงที่ Motor ---
PWM_PIN = 12   # GPIO 12
AIN1_PIN = 17  # GPIO 17
AIN2_PIN = 27  # GPIO 27

# --- Shared Variables ---
stop_event = threading.Event()
current_voltage = 0.0
current_motor_speed = 0
current_servo_angle = 0
data_lock = threading.Lock()


def get_motor_speed(voltage):
    """คำนวณความเร็ว Motor จากแรงดัน ADC"""
    if voltage < 1.0:
        return 0
    elif 1.0 <= voltage <= 1.6:
        return 0.3  # 30%
    elif 1.6 < voltage <= 2.0:
        return 0.6  # 60%
    else:  # > 2.0V
        return 1.0  # 100%


def adc_motor_worker():
    """Thread สำหรับอ่านค่า ADC และควบคุม Motor"""
    global current_voltage, current_motor_speed
    
    try:
        # สร้าง I2C connection
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        ads.gain = 1
        chan = AnalogIn(ads, ADC_CHANNEL)
        
        # สร้าง Motor objects
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
                    current_motor_speed = int(speed * 100)
                
                # ควบคุม Motor
                if speed > 0:
                    ain1.on()
                    ain2.off()
                    pwm_a.value = speed
                else:
                    ain1.on()
                    ain2.on()
                    pwm_a.value = 0  # เบรค
                
                print(f"[ADC+Motor] Voltage: {voltage:.2f}V -> Motor: {int(speed*100)}%")
                
            except Exception as e:
                print(f"[ADC+Motor] Error: {e}")
            
            # รอตามเวลาที่กำหนด
            for _ in range(int(ADC_INTERVAL / 0.1)):
                if stop_event.is_set():
                    break
                time.sleep(0.1)
                
    except Exception as e:
        print(f"[ADC+Motor] เกิดข้อผิดพลาด: {e}")
    finally:
        # หยุด Motor
        try:
            ain1.on()
            ain2.on()
            pwm_a.value = 0
        except:
            pass
        if i2c is not None:
            i2c.deinit()
        print("[ADC+Motor] ปิดการทำงาน")


def servo_worker():
    """Thread สำหรับควบคุม Servo หมุน 90° → 0° → -90° วนลูป"""
    global current_servo_angle
    
    # ลำดับมุมที่จะหมุน
    angles = [90, 0, -90]
    
    try:
        servo = AngularServo(SERVO_PIN, 
                             min_angle=SERVO_MIN, 
                             max_angle=SERVO_MAX,
                             min_pulse_width=MIN_PULSE, 
                             max_pulse_width=MAX_PULSE,
                             pin_factory=factory)
        
        print(f"[Servo] เริ่มทำงาน (90° -> 0° -> -90°)")
        
        index = 0
        
        while not stop_event.is_set():
            angle = angles[index]
            
            # ตั้งค่ามุม
            servo.angle = angle
            
            with data_lock:
                current_servo_angle = angle
            
            print(f"[Servo] Angle: {angle}°")
            
            # รอ 1 วินาที
            for _ in range(10):
                if stop_event.is_set():
                    break
                time.sleep(0.1)
            
            if stop_event.is_set():
                break
            
            # ไปมุมถัดไป (วนลูป)
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
    """Thread สำหรับแสดงภาพจากกล้อง"""
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    
    if not cap.isOpened():
        print("[Camera] ไม่สามารถเปิดกล้องได้")
        stop_event.set()
        return
    
    print("[Camera] เริ่มทำงาน (กด 'q' เพื่อออก)")
    
    try:
        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("[Camera] อ่านภาพไม่ได้")
                break
            
            # อ่านค่าปัจจุบัน
            with data_lock:
                v = current_voltage
                m = current_motor_speed
                s = current_servo_angle
            
            # แสดงข้อมูลบนหน้าจอ
            # สีตามความเร็ว Motor
            if m == 0:
                color = (128, 128, 128)  # เทา
                status = "MOTOR: STOP"
            elif m <= 30:
                color = (0, 255, 255)  # เหลือง
                status = f"MOTOR: {m}%"
            elif m <= 60:
                color = (0, 165, 255)  # ส้ม
                status = f"MOTOR: {m}%"
            else:
                color = (0, 0, 255)  # แดง
                status = f"MOTOR: {m}%"
            
            cv2.putText(frame, f"Voltage: {v:.2f}V", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, status, (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.putText(frame, f"Servo: {s} deg", (10, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # วาด progress bar สำหรับ Motor
            bar_width = int((m / 100) * 200)
            cv2.rectangle(frame, (10, 100), (210, 120), (50, 50, 50), -1)
            cv2.rectangle(frame, (10, 100), (10 + bar_width, 120), color, -1)
            
            cv2.imshow('Project004 - Camera + Servo + ADC + Motor', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set()
                break
                
    except Exception as e:
        print(f"[Camera] เกิดข้อผิดพลาด: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[Camera] ปิดกล้องเรียบร้อย")


def main():
    """ฟังก์ชันหลัก"""
    print("=" * 60)
    print("Project004: Camera + Servo + ADC + Motor")
    print("=" * 60)
    print("1. กล้องทำงานตลอด")
    print(f"2. Servo หมุน {SERVO_MIN}° <-> {SERVO_MAX}° ทีละ {SERVO_STEP}°")
    print("3. ADC ควบคุม Motor:")
    print("   - < 1.0V     = 0%")
    print("   - 1.0-1.6V   = 30%")
    print("   - 1.6-2.0V   = 60%")
    print("   - > 2.0V     = 100%")
    print("=" * 60)
    print("กด 'q' บนหน้าต่างกล้องเพื่อออก")
    print("=" * 60)
    
    # สร้าง Threads
    adc_motor_thread = threading.Thread(target=adc_motor_worker, daemon=True)
    servo_thread = threading.Thread(target=servo_worker, daemon=True)
    
    try:
        # เริ่ม threads
        adc_motor_thread.start()
        servo_thread.start()
        
        # รันกล้องใน main thread
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
