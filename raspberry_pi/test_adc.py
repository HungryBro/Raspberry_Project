"""
ADS1115 ADC Module
อ่านค่าแรงดันไฟ DC (0-3V) จากขา A0 ทุกๆ 0.5 วินาที
ใช้ library adafruit-circuitpython-ads1x15
"""

import threading
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn


class ADS1115Thread(threading.Thread):
    """Thread สำหรับอ่านค่าจาก ADS1115 ADC"""
    
    def __init__(self, channel=0, gain=1, interval=0.5):
        super().__init__()
        self.channel = channel  # ใช้เลข 0 แทน P0 เพื่อป้องกัน AttributeError
        self.gain = gain
        self.interval = interval  # อ่านทุกๆ 0.5 วินาที
        self.running = False
        self.i2c = None
        self.ads = None
        self.chan = None
        self.daemon = True
    
    def run(self):
        """เริ่มการทำงานของ Thread"""
        self.running = True
        
        try:
            # สร้าง I2C connection
            self.i2c = busio.I2C(board.SCL, board.SDA)
            
            # สร้าง ADS1115 object
            self.ads = ADS.ADS1115(self.i2c)
            
            # ตั้งค่า Gain = 1 (ช่วงวัด ±4.096V)
            self.ads.gain = self.gain
            
            # สร้าง channel object โดยใช้เลข 0 แทน P0
            # ใช้ ADS.P0, ADS.P1, ADS.P2, ADS.P3 หรือใช้เลข 0, 1, 2, 3
            self.chan = AnalogIn(self.ads, self.channel)
            
            print(f"[ADS1115] เริ่มอ่านค่าจากช่อง A{self.channel}")
            print(f"[ADS1115] Gain: {self.gain}, Interval: {self.interval}s")
            
            while self.running:
                try:
                    # อ่านค่า raw และแรงดัน
                    raw_value = self.chan.value
                    voltage = self.chan.voltage
                    
                    print(f"[ADS1115] Raw: {raw_value:>6}, Voltage: {voltage:.4f} V")
                    
                except Exception as e:
                    print(f"[ADS1115] เกิดข้อผิดพลาดในการอ่านค่า: {e}")
                
                # รอตามเวลาที่กำหนด
                for _ in range(int(self.interval / 0.1)):
                    if not self.running:
                        break
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"[ADS1115] เกิดข้อผิดพลาด: {e}")
        finally:
            self.cleanup()
    
    def stop(self):
        """หยุดการทำงานของ Thread"""
        self.running = False
    
    def cleanup(self):
        """ทำความสะอาดทรัพยากร"""
        if self.i2c is not None:
            self.i2c.deinit()
            self.i2c = None
        print("[ADS1115] ปิด ADS1115 เรียบร้อย")


def main():
    """ฟังก์ชันหลักสำหรับทดสอบโมดูล ADS1115"""
    ads_thread = ADS1115Thread(
        channel=0,  # ใช้เลข 0 แทน P0
        gain=1,     # Gain = 1
        interval=0.5
    )
    
    try:
        ads_thread.start()
        # รอจนกว่าจะกด Ctrl+C
        while ads_thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[ADS1115] กำลังหยุดโปรแกรม...")
    finally:
        ads_thread.stop()
        ads_thread.join(timeout=3)


if __name__ == "__main__":
    main()
