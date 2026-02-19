from gpiozero import AngularServo
from time import sleep

# ปรับค่า pulse width ให้ตรงกับ MG996R (0.5ms - 2.5ms)
# และปิดการแจ้งเตือน Warning รกๆ ตา (ถ้าต้องการ)
import warnings
warnings.filterwarnings("ignore")

# GPIO 18
servo = AngularServo(19, 
                     min_angle=-90, 
                     max_angle=90,
                     min_pulse_width=0.0005, 
                     max_pulse_width=0.0025)

# ฟังก์ชันหมุนช้าๆ
def move_slowly(current, target, step_delay=0.02):
    step = 1 if target > current else -1
    for angle in range(current, target, step):
        servo.angle = angle
        sleep(step_delay)
    servo.angle = target

print("เริ่มทดสอบ Servo แบบนุ่มนวล... (กด Ctrl+C เพื่อหยุด)")

try:
    current_angle = 0
    servo.angle = current_angle
    sleep(1)

    while True:
        print("Move to 90")
        move_slowly(current_angle, 90)
        current_angle = 90
        sleep(0.5)

        print("Move to 0")
        move_slowly(current_angle, 0)
        current_angle = 0
        sleep(0.5)

        print("Move to -90")
        move_slowly(current_angle, -90)
        current_angle = -90
        sleep(0.5)

        print("Move to 0")
        move_slowly(current_angle, 0)
        current_angle = 0
        sleep(0.5)

except KeyboardInterrupt:
    print("\nหยุดการทำงาน")
    servo.detach() # คลายล็อคเซอร์โว
