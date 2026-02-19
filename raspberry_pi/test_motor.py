"""
Test Motor Driver (TB6612 / L298N)
ทดสอบมอเตอร์ DC โดยใช้ PWM ควบคุมความเร็ว
สำหรับ Raspberry Pi 5 (ใช้ LGPIOFactory)
"""

from gpiozero import PWMOutputDevice, DigitalOutputDevice
from gpiozero.pins.lgpio import LGPIOFactory
from time import sleep

import warnings
warnings.filterwarnings("ignore")

# ใช้ LGPIOFactory สำหรับ Pi 5
factory = LGPIOFactory()

# --- ตั้งค่า Pin ---
# PWM_A: ควบคุมความเร็ว (0-100%)
# AIN1, AIN2: ควบคุมทิศทาง
PWM_PIN = 12   # GPIO 12 (Pin 32)
AIN1_PIN = 17  # GPIO 17 (Pin 11)
AIN2_PIN = 27  # GPIO 27 (Pin 13)

# สร้าง Objects
pwm_a = PWMOutputDevice(PWM_PIN, pin_factory=factory)
ain1 = DigitalOutputDevice(AIN1_PIN, pin_factory=factory)
ain2 = DigitalOutputDevice(AIN2_PIN, pin_factory=factory)


def motor_forward(speed=1.0):
    """หมุนไปข้างหน้า (speed: 0.0 - 1.0)"""
    ain1.on()
    ain2.off()
    pwm_a.value = speed
    print(f"[Motor] หมุนไปข้างหน้า ความเร็ว {int(speed*100)}%")


def motor_backward(speed=1.0):
    """หมุนถอยหลัง (speed: 0.0 - 1.0)"""
    ain1.off()
    ain2.on()
    pwm_a.value = speed
    print(f"[Motor] หมุนถอยหลัง ความเร็ว {int(speed*100)}%")


def motor_brake():
    """เบรค (หยุดทันที)"""
    ain1.on()
    ain2.on()
    pwm_a.value = 0
    print("[Motor] เบรค!")


def motor_coast():
    """ปล่อยลอย (หยุดช้าๆ)"""
    ain1.off()
    ain2.off()
    pwm_a.value = 0
    print("[Motor] ปล่อยลอย")


def main():
    print("=" * 50)
    print("ทดสอบ Motor Driver")
    print("=" * 50)
    print(f"PWM Pin: GPIO {PWM_PIN}")
    print(f"AIN1 Pin: GPIO {AIN1_PIN}")
    print(f"AIN2 Pin: GPIO {AIN2_PIN}")
    print("=" * 50)
    print("กด Ctrl+C เพื่อหยุด")
    print()

    try:
        while True:
            # ทดสอบหมุนไปข้างหน้า หลายระดับความเร็ว
            motor_forward(0.3)
            sleep(2)

            motor_forward(0.6)
            sleep(2)

            motor_forward(1.0)
            sleep(2)

            # เบรค
            motor_brake()
            sleep(1)

            # ทดสอบหมุนถอยหลัง
            motor_backward(0.5)
            sleep(2)

            motor_backward(1.0)
            sleep(2)

            # หยุด
            motor_coast()
            sleep(2)

    except KeyboardInterrupt:
        print("\n[Motor] หยุดการทำงาน")
    finally:
        motor_brake()
        print("[Motor] ปิดโปรแกรมเรียบร้อย")


if __name__ == "__main__":
    main()
