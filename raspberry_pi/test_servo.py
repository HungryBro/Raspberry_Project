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

print("เริ่มทดสอบ Servo... (กด Ctrl+C เพื่อหยุด)")

try:
    while True:
        print("Set to 90")
        servo.angle = 90
        sleep(1)

        print("Set to 0")
        servo.angle = 0
        sleep(1)

        print("Set to -90")
        servo.angle = -90
        sleep(1)

except KeyboardInterrupt:
    print("\nหยุดการทำงาน")
    servo.detach() # คลายล็อคเซอร์โว
