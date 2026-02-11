"""
adc_module.py - อ่านค่า ADS1115 ADC + ควบคุม Motor ตามแรงดัน
"""

import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from config import ADC_CHANNEL, ADC_INTERVAL
import shared_state
import motor_module


def adc_motor_worker():
    """Thread: อ่านค่า ADC และควบคุม Motor ตามแรงดัน
    - เจอหน้าคน → Motor = 0%
    - ไม่เจอหน้า → Motor ตามค่า ADC
    """
    i2c = None
    
    try:
        # สร้าง I2C connection
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c)
        ads.gain = 1
        chan = AnalogIn(ads, ADC_CHANNEL)
        
        # สร้าง Motor
        motor_module.init()
        
        print(f"[ADC+Motor] เริ่มทำงาน - ADC ช่อง A{ADC_CHANNEL}")
        
        while not shared_state.stop_event.is_set():
            try:
                # อ่านค่า ADC
                voltage = chan.voltage
                speed = motor_module.get_speed_from_voltage(voltage)
                
                shared_state.set_voltage(voltage)
                
                # ตรวจสอบว่าเจอหน้าหรือไม่
                if shared_state.face_detected.is_set():
                    motor_module.brake()
                    shared_state.set_motor_speed(0)
                    print(f"[ADC+Motor] Voltage: {voltage:.2f}V -> Motor: 0% (FACE DETECTED!)")
                else:
                    motor_module.control(speed)
                    shared_state.set_motor_speed(int(speed * 100))
                    print(f"[ADC+Motor] Voltage: {voltage:.2f}V -> Motor: {int(speed*100)}%")
                
            except Exception as e:
                print(f"[ADC+Motor] Error: {e}")
            
            # รอตามเวลาที่กำหนด
            for _ in range(int(ADC_INTERVAL / 0.1)):
                if shared_state.stop_event.is_set():
                    break
                time.sleep(0.1)
                
    except Exception as e:
        print(f"[ADC+Motor] เกิดข้อผิดพลาด: {e}")
    finally:
        motor_module.brake()
        if i2c is not None:
            i2c.deinit()
        print("[ADC+Motor] ปิดการทำงาน")
