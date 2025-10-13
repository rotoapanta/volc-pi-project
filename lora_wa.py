import serial

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
ser.write(b'Hola desde la Raspberry Pi\r\n')