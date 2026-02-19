"""
motor_module.py - ควบคุม Motor Driver (TB6612 / L298N)
<<<<<<< HEAD
รองรับทั้ง Mode ADC (เรียกจาก adc_module) และ Mode Gesture (motor_worker)
"""

import time
=======
"""

>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
from gpiozero import PWMOutputDevice, DigitalOutputDevice
from config import factory, MOTOR_PWM_PIN, MOTOR_AIN1_PIN, MOTOR_AIN2_PIN
import shared_state

# --- Motor Objects ---
pwm_a = None
ain1 = None
ain2 = None


def init():
    """สร้าง Motor objects"""
    global pwm_a, ain1, ain2
<<<<<<< HEAD

=======
    
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
    with shared_state.motor_lock:
        pwm_a = PWMOutputDevice(MOTOR_PWM_PIN, pin_factory=factory)
        ain1 = DigitalOutputDevice(MOTOR_AIN1_PIN, pin_factory=factory)
        ain2 = DigitalOutputDevice(MOTOR_AIN2_PIN, pin_factory=factory)
<<<<<<< HEAD

=======
    
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
    print("[Motor] พร้อมทำงาน")


def control(speed):
    """ควบคุม Motor
    speed: 0.0 - 1.0 (0 = หยุด, 1 = เต็มกำลัง)
    """
    global pwm_a, ain1, ain2
<<<<<<< HEAD

    with shared_state.motor_lock:
        if pwm_a is None:
            return

=======
    
    with shared_state.motor_lock:
        if pwm_a is None:
            return
            
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
        if speed > 0:
            ain1.on()
            ain2.off()
            pwm_a.value = speed
        else:
            ain1.on()
            ain2.on()
            pwm_a.value = 0


def brake():
    """เบรค Motor"""
    control(0)


def get_speed_from_voltage(voltage):
<<<<<<< HEAD
    """คำนวณความเร็ว Motor จากแรงดัน ADC (Mode ADC)
=======
    """คำนวณความเร็ว Motor จากแรงดัน ADC
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
    - < 1V     = 0%
    - 1.0-1.6V = 30%
    - 1.6-2.0V = 60%
    - > 2V     = 100%
    """
    if voltage < 1.0:
        return 0
    elif 1.0 <= voltage <= 1.6:
        return 0.3
    elif 1.6 < voltage <= 2.0:
        return 0.6
    else:
        return 1.0
<<<<<<< HEAD


def motor_worker():
    """Thread (Mode Gesture): อ่าน target_speed จาก shared_state แล้วสั่ง Motor
    - เจอหน้าคน → Motor = 0% (หยุดฉุกเฉิน)
    - ไม่เจอหน้า → Motor ตาม target_speed ที่กล้องคำนวณจากท่ามือ
    """
    try:
        init()
        print("[Motor] เริ่มทำงาน (Mode Gesture)")

        while not shared_state.stop_event.is_set():
            try:
                # ตรวจสอบว่าเจอหน้าหรือไม่
                if shared_state.face_detected.is_set():
                    brake()
                    shared_state.set_motor_speed(0)
                else:
                    status = shared_state.get_status()
                    speed = status["target_speed"]
                    control(speed)
                    shared_state.set_motor_speed(int(speed * 100))

            except Exception as e:
                print(f"[Motor] Error: {e}")

            time.sleep(0.1)

    except Exception as e:
        print(f"[Motor] เกิดข้อผิดพลาด: {e}")
    finally:
        brake()
        print("[Motor] ปิดการทำงาน")
=======
>>>>>>> 00a500696ae068019fae394ee6ef2b6476c87d77
