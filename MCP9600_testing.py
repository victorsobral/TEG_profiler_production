import mcp9600
import time

m = mcp9600.MCP9600(i2c_addr=0x60)
time.sleep(2)

for i in range(10):
	print("\nAmbient temperature: %0.1f C" % m.get_cold_junction_temperature())
	print("Thermocouple temperature: %0.1f C" % m.get_hot_junction_temperature())
	time.sleep(1)

