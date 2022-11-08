"""
Módolo para puente H L298N
	acepta speed entre -100 y 100. (0 es stop)
ejemplo de uso:

from dc_motor import DCMotor       
frequency = 15000       
pin1 = 12    
pin2 = 14     
enable = 27  
motor = DCMotor(pin1, pin2, enable)      
while True:
    vel = int(input('vel.: '))
    motor.run(vel)

"""
from machine import Pin, PWM

class DCMotor:      
  def __init__(self, pin1, pin2, enable_pin, min_duty=800, max_duty=1023):
        self.pin1 = Pin(pin1, Pin.OUT)
        self.pin2 = Pin(pin2, Pin.OUT)
        self.enable_pin = PWM(Pin(enable_pin), 15000)
        self.min_duty = min_duty
        self.max_duty = max_duty

  def run(self,speed):
      if speed >0:		# Forward
          self.pin1.value(0)
          self.pin2.value(1)
      elif speed <0:		# Backward
          self.pin1.value(1)
          self.pin2.value(0)
      else:		# Stop
          self.pin1.value(0)
          self.pin2.value(0)
          
      self.enable_pin.duty(self.duty_cycle(abs(speed)))
    
 
  def duty_cycle(self, speed):
   if speed > 100:
        return self.max_duty
   else:
    return int(self.min_duty + (self.max_duty - self.min_duty)*((speed-1)/(100-1)))
