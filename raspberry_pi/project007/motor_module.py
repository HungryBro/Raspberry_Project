"""
motor_module.py - ควบคุม Motor Driver (TB6612 / L298N)
"""

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
    
    with shared_state.motor_lock:
        pwm_a = PWMOutputDevice(MOTOR_PWM_PIN, pin_factory=factory)
        ain1 = DigitalOutputDevice(MOTOR_AIN1_PIN, pin_factory=factory)
        ain2 = DigitalOutputDevice(MOTOR_AIN2_PIN, pin_factory=factory)
    
    print("[Motor] พร้อมทำงาน")


def control(speed):
    """ควบคุม Motor
    speed: 0.0 - 1.0 (0 = หยุด, 1 = เต็มกำลัง)
    """
    global pwm_a, ain1, ain2
    
    with shared_state.motor_lock:
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


def brake():
    """เบรค Motor"""
    control(0)


def get_speed_from_voltage(voltage):
    """คำนวณความเร็ว Motor จากแรงดัน ADC
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
