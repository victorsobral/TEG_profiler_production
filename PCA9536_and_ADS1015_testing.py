import board
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from adafruit_bus_device.i2c_device import I2CDevice
import time

i2c = board.I2C()

pca = I2CDevice(i2c, 0x41)
with pca:
    pca.write(bytes([0x03,0x00]))
    time.sleep(0.1)
    pca.write(bytes([0x01,0x00]))
    time.sleep(0.1)


ads = ADS.ADS1015(i2c)
ads.gain = 8

chan = AnalogIn(ads, ADS.P0)





    
for i in range(10):
    print("%.4f volts" % chan.voltage)
    time.sleep(1)

