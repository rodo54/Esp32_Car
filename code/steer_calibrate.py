import time
import machine
from servo import Servo

servo_pin = machine.Pin(23, mode=machine.Pin.OUT)
my_servo = Servo(servo_pin , min_us=500, max_us=2500, maxangle=180)


my_servo.angle(90)
while True:
    ang = int(input('ang.: '))
    my_servo.angle(ang)
