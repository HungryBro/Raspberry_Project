"""
Project003: รวม Camera + Servo + ADC
- กล้องทำงานตลอด
- Servo หมุน 0° <-> 180°
- ถ้า ADC วัดได้ 0V จะหยุด Servo (แต่กล้องยังทำงานอยู่)
"""

import cv2
import threading
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from gpiozero import AngularServo

import warnings
warnings.filterwarnings("ignore")

# --- ค่าคงที่ ---
SERVO_PIN = 18
MIN_PULSE = 0.0005
MAX_PULSE = 0.0025
ADC_CHANNEL = 0
ADC_INTERVAL = 0.5  # อ่านค่าทุก 0.5 วินาที

# --- Shared Variables ---
stop_event = threading.Event()      # สำหรับหยุดโปรแกรมทั้งหมด
servo_pause = threading.Event()     # สำหรับหยุด Servo ชั่วคราว (เมื่อ ADC = 0)
current_voltage = 0.0               # เก็บค่าแรงดันปัจจุบัน
voltage_lock = threading.Lock()     # ป้องกัน race condition


def adc_worker():
    """Thread สำหรับอ่านค่าจาก ADS1115"""
    global current_voltage
    
    try:
        # สร้าง I2C connection
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        ads.gain = 1  # ช่วงวัด ±4.096V
        chan = AnalogIn(ads, ADC_CHANNEL)
        
        print(f"[ADC] เริ่มอ่านค่าจากช่อง A{ADC_CHANNEL}")
        
        while not stop_event.is_set():
            try:
                raw_value = chan.value
                voltage = chan.voltage
                
                with voltage_lock:
                    current_voltage = voltage
                
                print(f"[ADC] Raw: {raw_value:>6}, Voltage: {voltage:.4f} V")
                
                # ถ้าแรงดัน = 0 หรือต่ำมากๆ ให้หยุด Servo
                if voltage < 0.01:  # ใกล้ 0V
                    if not servo_pause.is_set():
                        print("[ADC] ⚠️ แรงดัน = 0V -> หยุด Servo!")
                        servo_pause.set()
                else:
                    if servo_pause.is_set():
                        print("[ADC] ✅ แรงดันกลับมา -> Servo ทำงานต่อ!")
                        servo_pause.clear()
                
            except Exception as e:
                print(f"[ADC] เกิดข้อผิดพลาดในการอ่านค่า: {e}")
            
            # รอตามเวลาที่กำหนด
            for _ in range(int(ADC_INTERVAL / 0.1)):
                if stop_event.is_set():
                    break
                time.sleep(0.1)
                
    except Exception as e:
        print(f"[ADC] เกิดข้อผิดพลาด: {e}")
    finally:
        if i2c is not None:
            i2c.deinit()
        print("[ADC] ปิด ADC เรียบร้อย")


def servo_worker():
    """Thread สำหรับควบคุม Servo"""
    try:
        servo = AngularServo(SERVO_PIN, 
                             min_angle=0, 
                             max_angle=180,
                             min_pulse_width=MIN_PULSE, 
                             max_pulse_width=MAX_PULSE)
        
        print("[Servo] เริ่มทำงาน (0° <-> 180°)")
        
        while not stop_event.is_set():
            # ตรวจสอบว่าต้องหยุด Servo หรือไม่
            if servo_pause.is_set():
                time.sleep(0.1)
                continue
            
            # หมุนไปที่ 0 องศา
            servo.angle = 0
            print("[Servo] Angle: 0°")
            
            # รอ 2 วินาที (แต่ตรวจสอบทุก 0.1 วินาที)
            for _ in range(20):
                if stop_event.is_set() or servo_pause.is_set():
                    break
                time.sleep(0.1)
            
            if stop_event.is_set():
                break
            if servo_pause.is_set():
                continue
            
            # หมุนไปที่ 180 องศา
            servo.angle = 180
            print("[Servo] Angle: 180°")
            
            for _ in range(20):
                if stop_event.is_set() or servo_pause.is_set():
                    break
                time.sleep(0.1)
                
    except Exception as e:
        print(f"[Servo] เกิดข้อผิดพลาด: {e}")
    finally:
        print("[Servo] ปิด Servo เรียบร้อย")


def camera_worker():
    """Thread สำหรับแสดงภาพจากกล้อง"""
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)  # Width
    cap.set(4, 480)  # Height
    
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
            
            # แสดงสถานะบนหน้าจอ
            with voltage_lock:
                v = current_voltage
            
            status = "SERVO: RUNNING" if not servo_pause.is_set() else "SERVO: PAUSED"
            color = (0, 255, 0) if not servo_pause.is_set() else (0, 0, 255)
            
            cv2.putText(frame, f"Voltage: {v:.3f}V", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, status, (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            cv2.imshow('Project003 - Camera + Servo + ADC', frame)
            
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
    print("=" * 50)
    print("Project003: Camera + Servo + ADC")
    print("=" * 50)
    print("- กล้องทำงานตลอด")
    print("- Servo หมุน 0° <-> 180°")
    print("- ถ้า ADC = 0V จะหยุด Servo")
    print("- กด 'q' บนหน้าต่างกล้องเพื่อออก")
    print("=" * 50)
    
    # สร้าง Threads
    adc_thread = threading.Thread(target=adc_worker, daemon=True)
    servo_thread = threading.Thread(target=servo_worker, daemon=True)
    
    try:
        # เริ่ม ADC และ Servo threads
        adc_thread.start()
        servo_thread.start()
        
        # รันกล้องใน main thread (เพราะ OpenCV ต้องการ main thread)
        camera_worker()
        
    except KeyboardInterrupt:
        print("\n[Main] กด Ctrl+C - กำลังหยุดโปรแกรม...")
    finally:
        stop_event.set()
        
        # รอให้ threads หยุด
        adc_thread.join(timeout=2)
        servo_thread.join(timeout=2)
        
        print("[Main] ปิดโปรแกรมเรียบร้อย")


if __name__ == "__main__":
    main()
