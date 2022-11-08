from machine import PWM
import math

# originally by Radomir Dopieralski http://sheep.art.pl
# from https://bitbucket.org/thesheep/micropython-servo

class Servo:
    """
    A simple class for controlling hobby servos.
    Args:
        pin (machine.Pin): The pin where servo is connected. Must support PWM.
        freq (int): The frequency of the signal, in hertz.
        min_us (int): The minimum signal length supported by the servo.
        max_us (int): The maximum signal length supported by the servo.
        maxangle (int): The angle between the minimum and maximum positions.
    """
    def __init__(self, pin, freq=50, min_us=400, max_us=2500, maxangle=180):
        self.min_us = min_us
        self.max_us = max_us
        self.us = 0
        self.freq = freq
        self.maxangle = maxangle
        self.actual = 0
        self.pwm = PWM(pin, freq=freq, duty=0)

    def write_us(self, us):
        """Set the signal to be ``us`` microseconds long. Zero disables it."""
        if us == 0:
            self.pwm.duty(0)
            return
        us = min(self.max_us, max(self.min_us, us))
        duty = us * 1024 * self.freq // 1000000
        self.pwm.duty(duty)

    def write_angle(self, degrees=None, radians=None):
        """Move to the specified angle in ``degrees`` or ``radians``."""
        if degrees is None:
            degrees = math.degrees(radians)
        degrees = degrees % 360
        total_range = self.max_us - self.min_us
        us = self.min_us + total_range * degrees // self.maxangle
        self.write_us(us)
    def angle(self, degrees=None):
        """Move to the specified angle in ``degrees`` If None, returns actual."""
        if degrees is None: return self.actual
        self.actual = degrees
        degrees = degrees % 360
        total_range = self.max_us - self.min_us
        us = self.min_us + total_range * degrees // self.maxangle
        self.write_us(us)