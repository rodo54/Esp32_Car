'''
Control Remoto para ESP32
    version 1.0
    usando BLE Nordic UART Service (NUS).
    y aplicación BlueFruit
    by R. Leibner: rleibner@gmail.com
    Basado en https://github.com/micropython/micropython/blob/master/examples/bluetooth/ble_uart_peripheral.py
'''

import bluetooth, time, machine
from struct import unpack
from ble_advertising import advertising_payload
from micropython import const
from machine import Pin, PWM, ADC
from servo import Servo
from dc_motor import DCMotor

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)

# org.bluetooth.characteristic.gap.appearance.xml
_ADV_APPEARANCE_GENERIC_COMPUTER = const(128)

class BLEUART:
    def __init__(self, ble, name="Car-ESP32", rxbuf=100):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._tx_handle, self._rx_handle),) = self._ble.gatts_register_services((_UART_SERVICE,))
        # Increase the size of the rx buffer and enable append mode.
        self._ble.gatts_set_buffer(self._rx_handle, rxbuf, True)
        self._connections = set()
        self._rx_buffer = bytearray()
        self._handler = None
        # Optionally add services=[_UART_UUID], but this is likely to make the payload too large.
        self._payload = advertising_payload(name=name, appearance=_ADV_APPEARANCE_GENERIC_COMPUTER)
        self._advertise()

    def irq(self, handler):
        self._handler = handler

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            print('connected')
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
            print('bye')
            exit()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if conn_handle in self._connections and value_handle == self._rx_handle:
                self._rx_buffer += self._ble.gatts_read(self._rx_handle)
                if self._handler:
                    self._handler()

    def read(self, sz=None):
        if not sz:
            sz = len(self._rx_buffer)
        result = self._rx_buffer[0:sz]
        self._rx_buffer = self._rx_buffer[sz:]
        return result

    def write(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._tx_handle, data)

    def close(self):
        for conn_handle in self._connections:
            self._ble.gap_disconnect(conn_handle)
        self._connections.clear()

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

class Car:
# '''
# A simple class for controlling a SG90 servo and a PWM motor.
# Args:
#     servo: a Servo instance.
#     motor: a DCMotor instance.
#     light: a machine.Pin (out)
# '''
    def __init__(self, servo, motor, light):
        self.servo = servo
        self.motor = motor
        self.light = light
        self.speed = 0
        self.angle = servoCenter
        self.msg = ''
        
    def update(self, dSpeed, dSteer, bttn):
        if bttn != None: self.cmd(bttn)
        else:
            if dSpeed == 0: # decrement
                if self.speed >0: self.speed -= max(0, 1+self.speed //10)
                else: self.speed -= min(0, self.speed //10)
            elif dSpeed == 1:
                self.speed *= -1	# Break
                time.sleep(0.1)
                self.speed = 0
                
            else:   self.speed += dSpeed
            
            if dSteer == 0 and self.speed != 0 : # decrement
                adif = self.angle - servoCenter
                if adif >0: self.angle -= min(adif, 1+(adif* abs(self.speed))//1000)
                else: self.angle += min(abs(adif), 1+(abs(adif* self.speed))//1000)
            else:   self.angle += dSteer
        # limits:
        if self.speed > 100: self.speed = 100
        if self.speed < -100: self.speed = -100
        if self.angle > servoCenter+servoFull: self.angle = servoCenter+servoFull
        if self.angle < servoCenter-servoFull: self.angle = servoCenter-servoFull

        self.servo.angle(self.angle)
        time.sleep(0.05)
        self.motor.run(self.speed)
        l = 'L' if self.light.value() else ''
        self.msg = 'Vel.: %d   Dir.: %d°  %s'%(self.speed, self.angle-servoCenter, l)


    def cmd(self, bttn):
        if bttn == '1': self.speed = 0
        elif bttn == '2': self.angle = servoCenter
        elif bttn == '3':
            self.speed = 0
            self.angle = servoCenter
        else:
            if self.light.value(): self.light.off()
            else: self.light.on()
            time.sleep(.1)
            
        
        
def sign(x):
    return 1 if x>0 else -1
    
def exit(s='disconnected'):
    global running
    print(s)
    running = False
    
def run():
    global bttn
    ble = bluetooth.BLE()
    uart = BLEUART(ble)
    myServo = Servo(Pin(23))
    myMotor = DCMotor(14, 12, 27)
    light = Pin(22, Pin.OUT)
    car = Car(myServo, myMotor, light )
    bat = ADC(Pin(36))
    bat.atten(ADC.ATTN_11DB)       #Full range: 3.3v
    bat.width(9)

    myServo.angle(120)	# ready !
    time.sleep(1)
    myServo.angle(90)
    
    def on_rx():
        global dSpeed, dSteer, bttn, z0
        data = uart.read()
        accelThres = 2
        bttn = None
        ''' Acelerómetro '''
        if chr(data[0])=="!" and chr(data[1])=="A" :
            z = unpack('<f', data[10:14])[0]	# Speed axis
            y = unpack('<f', data[6:10])[0] # Steer axis
            if z0 == None: z0 = z
            z -= z0
            dSpeed = 0 if abs(z) < accelThres else 2 * sign(z)
            dSteer = 0 if abs(y) < accelThres else 2 * sign(y)
            bttn = None

        ''' Control Pad '''
        if chr(data[0])=="!" and chr(data[1])=="B" :
            if data.decode()[2]=='5': dSpeed = 2 * int(data.decode()[3])
            elif data.decode()[2]=='6': dSpeed = -2 * int(data.decode()[3])
            elif data.decode()[2]=='7': dSteer = -2 * int(data.decode()[3])
            elif data.decode()[2]=='8': dSteer = 2 * int(data.decode()[3])
            else:
                bttn = str(data.decode()[2])
                
        if car.speed!=0 and dSpeed!=0 and sign(dSpeed)!=sign(car.speed): dSpeed = 1	# Break

    uart.irq(handler=on_rx)
    
    while running:
        V = bat.read()
        time.sleep(.05)
        V *= .02699115 # resist. divisor: 33K + 10K
        Vrel = max(V*23.8 -200, 0)
        Bat = 'Bat.:' if V>8.4 else 'LOW Bat.'
        try:
            uart.write('\n%s\n%s %.1f V  (%d %%)'%(car.msg, Bat, V, Vrel))
        except KeyboardInterrupt:
            pass
        
                    
        car.update(dSpeed, dSteer, bttn)
        bttn = None
        
    car.update(0,0,'3')	# STOP !
    uart.close()

bttn = '4'
servoCenter = 95	# Calibrate using steer_calibrate.py !!
servoFull = 55	# Calibrate using steer_calibrate.py !!
running = True
z0 = None
dSpeed = 0
dSteer = 0

run()



