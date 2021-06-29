################################################
#
# TEG profiler script (cloud+local)
#
# University of Virginia
# Author: Victor Ariel Leal Sobral
#
################################################

import board
import digitalio

import os
import threading
import csv

import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

from adafruit_bus_device.i2c_device import I2CDevice

import mcp9600

import time
from datetime import datetime
import paho.mqtt.client as mqtt
import json
import logging
#import math


###########
#MQTT functions

# # Uncoment to print MQTT log details
# def on_log(client, userdata, level, buf):
#     print("<< log: "+buf+" >>")

# # Uncoment to print sent message details
# def on_message(client, userdata, message):
#     print("\nmessage received: ", str(message.payload.decode("utf-8")))
#     print("message topic = ", message.topic)
#     print("message qos = ", message.qos)
#     print("message retain flag = ", message.retain)
    
def on_connect(client, userdata, flags, rc):
    if rc ==0:
        print("Successfully connected")
        logging.info("[MQTT]: Successfully connected at "+str(datetime.utcnow().isoformat()))
    else:
        print("Bad connection, returned code = ", rc)
        logging.error("[MQTT]: Bad connection, returned code = "+str(rc)+" at "+str(datetime.utcnow().isoformat()))

def on_disconnect(client, userdata, flags, rc=0):
    print("Disconnected, result code = ", str(rc))
    logging.info("[MQTT]: Disconnected, result code = " +str(rc)+" at "+str(datetime.utcnow().isoformat()))




###########
# MQTT publishing function

def cloud_upload(APP_ID,BROKER_ADDRESS,SAMPLING_PERIOD, message, data_list):

    # Standard message with fields expected by the MQTT broker
    message = {
       "app_id":APP_ID,
       "counter": 0,
       "payload_fields":{

         "voltage_chan_OFF":{
             "displayName":"High Impedance",
             "unit":"V",
             "value":-999.99
          },

         "voltage_chan_0":{
             "displayName":"Channel 0",
             "unit":"V",
             "value":-999.99
          },

         "voltage_chan_1":{
             "displayName":"Channel 1",
             "unit":"V",
             "value":-999.99
          },

         "voltage_chan_2":{
             "displayName":"Channel 2",
             "unit":"V",
             "value":-999.99
          },

         "voltage_chan_3":{
             "displayName":"Channel 3",
             "unit":"V",
             "value":-999.99
          },

          "temperature_amb":{
             "displayName":"Ambient temperature",
             "unit":"°C",
             "value":-999.99
          },

          "temperature_hot":{
             "displayName":"Hot side temperature",
             "unit":"°C",
             "value":-999.99
          }

       },
       "metadata":{
          "time":"2020-12-01T12:00:00.000000000Z"
       }
    }

 
    client = mqtt.Client(APP_ID) # Creates a new MQTT client instance
    # client.on_log = on_log
    # client.on_message = on_message
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    # client.reconnect_delay_set(min_delay=10, max_delay=120)

    client.connect(BROKER_ADDRESS) # Connects to MQTT broker
    # time.sleep(2)

    client.loop_start()
    # time.sleep(1)

    client.subscribe("linklab/teg_eh_profiler", qos=0) # Subscribes to linklab/teg_eh_profiler topic
    # time.sleep(2)

    for COUNTER in range(len(data_list)):

        message['metadata']['time'] = data_list[COUNTER][0]
        message['payload_fields']['voltage_chan_OFF']['value'] = data_list[COUNTER][1]
        message['payload_fields']['voltage_chan_0']['value'] = data_list[COUNTER][2]
        message['payload_fields']['voltage_chan_1']['value'] = data_list[COUNTER][3]
        message['payload_fields']['voltage_chan_2']['value'] = data_list[COUNTER][4]
        message['payload_fields']['voltage_chan_3']['value'] = data_list[COUNTER][5]   
        message['payload_fields']['temperature_amb']['value'] = data_list[COUNTER][6]
        message['payload_fields']['temperature_hot']['value'] = data_list[COUNTER][7]        
        message['counter'] = COUNTER

        client.publish("linklab/teg_eh_profiler",json.dumps(message),qos=0)
        time.sleep(0.2)
        print(datetime.utcnow())


    client.loop_stop()


###########
# CSV writing function

def file_writer(file_name, directory, header, data_list):
    with open(directory+'/'+file_name, 'w') as file:
        csvwriter = csv.writer(file, delimiter = ',')
        csvwriter.writerow(header)
        for row in data_list:
            csvwriter.writerow(row)


###########
# Logging file configurations

logging.basicConfig(filename ='/home/pi/Desktop/shared/TEG_profiler.log', level=logging.INFO) # formating log file
logging.info('===================================================================')
logging.info('[Events]: TEG profiler cloud script started at '+str(datetime.utcnow().isoformat()))


###########
# Local data storage configurations

directory = '/home/pi/Desktop/shared/data'

if not os.path.exists(directory):
    os.makedirs(directory)

batch_size = 1800 # Equivalent of 15 minutes at sampling rate of 0.5 Hz
header = ['Timestamp', 'voltage_chan_OFF', 'voltage_chan_0', 'voltage_chan_1', 'voltage_chan_2', 'voltage_chan_3', 'temperature_amb', 'temperature_hot']
data_list = [[None]*8 for i in range(batch_size)] # creates a buffer for all variables with given batch size


###########
# Profiler configuration settings

# Reads application info file with application ID and MQTT borker address
try:
    print("Reading application info file...")
    with open("/home/pi/Desktop/Application_info.txt") as json_appInfo:
        APP_INFO = json.load(json_appInfo)
        
except Exception as e:
    print("Application info file could not be loaded")
    logging.error("[FileIO]: Application info file could not be loaded")
    logging.error("[FileIO]: "+e)
    raise

BROKER_ADDRESS = '34.230.161.172' # APP_INFO["BROKER_ADDRESS"] # IP address of the MQTT broker
APP_ID = APP_INFO["APP_ID"] # how this application will be identified in the cloud database
SAMPLING_PERIOD = 0.5 # in seconds (max 0.1)





##########
# Main code

# # Uncoment to start script after pushing GPIO17 button
# button = digitalio.DigitalInOut(board.D17)
# button.direction = digitalio.Direction.INPUT
# 
# print("press button to start...")
# 
# while True:
#     if button.value == False:
#         break
#


print("Starting I2C devices...")
try:
    i2c = board.I2C()
    logging.info("[I2C]: raspberry pi board I2C interface was sucesfully initialized")
except Exception as e: 
    logging.error("[I2C]: raspberry pi board I2C interface initialization error")
    logging.error("[I2C]: "+e) 
    
    
try: 
    pca = I2CDevice(i2c, 0x41) # creates the PCA GPIO controller at address 0x41 
    pca.write(bytes([0x03,0x00]))# configure GPIO as output
    logging.info("[I2C]: PCA GPIO controller was sucesfully initialized and configured")
except Exception as e: 
    logging.error("[I2C]: PCA GPIO controller initialization error")
    logging.error("[I2C]: "+e)    


try: 
    ads = ADS.ADS1015(i2c) # creates the ADS analog to digital converter at default address (0x48)
    ads.gain = 8 # configures PGA gain to 8, resulting on range of +-0.512V (valid configurations: 2/3, 1, 2, 4, 8, 16) 
    ads.mode = ADS.Mode.CONTINUOUS # converts at max speed, reads most recent conversion through I2C
    chan = AnalogIn(ads, ADS.P0) # configures ADS to read analog values from channel 0
    logging.info("[I2C]: ADS analog to digital converter was sucesfully initialized and configured")
except Exception as e: 
    logging.error("[I2C]: ADS analog to digital converter initialization error")
    logging.error("[I2C]: "+e) 


try:
    mcp = mcp9600.MCP9600(i2c_addr=0x60) # creates the MCP thermocouple amplifier at address 0x60, default config for K-type thermocouple
    logging.info("[I2C]: MCP thermocouple amplifier was sucesfully initialized and configured")
except Exception as e:
    logging.error("[I2C]: ADS analog to digital converter initialization error")
    logging.error("[I2C]: "+e) 


# Configuring interruption button on GPIO 17 (hold for 1 SAMPLE_PERIOD to stop)
button = digitalio.DigitalInOut(board.D17)
button.direction = digitalio.Direction.INPUT

COUNTER = 0

print("Starting acquisition...")
while True:
    
    timestamp = datetime.utcnow()
    
    try: 
        pca.write(bytes([0x01,0x00])) # set all transistor switches off
        time.sleep(0.010)
        data_list[COUNTER][1] = chan.voltage # read TEG open circuit voltage
        time.sleep(0.005)
        
        pca.write(bytes([0x01,0x01])) # open only channel zero switch (0.1 ohm channel)
        time.sleep(0.010)
        data_list[COUNTER][2] = chan.voltage # read TEG output voltage
        time.sleep(0.005)
        
        pca.write(bytes([0x01,0x02])) # open only channel one switch (0.47 ohm channel)
        time.sleep(0.010)
        data_list[COUNTER][3] = chan.voltage # read TEG output voltage
        time.sleep(0.005)
        
        pca.write(bytes([0x01,0x04])) # open only channel two switch (1.5 ohm channel)
        time.sleep(0.010)
        data_list[COUNTER][4] = chan.voltage # read TEG output voltage
        time.sleep(0.005)
        
        pca.write(bytes([0x01,0x08])) # open only channel three switch (4.7 ohm channel)
        time.sleep(0.010)
        data_list[COUNTER][5] = chan.voltage # read TEG output voltage
           
    except Exception as e:
        logging.error("[I2C]: TEG I-V curve scan failed at COUNTER = "+str(COUNTER)+", timestamp = "+str(datetime.utcnow().isoformat()))
        logging.error("[I2C]: "+e)  
   
   
    try: 
        data_list[COUNTER][6] = float(mcp.get_cold_junction_temperature()) # measure ambient temperature (cold junction)
        
        data_list[COUNTER][7] = float(mcp.get_hot_junction_temperature()) # measure probe temperature (hot junction)

    except Exception as e:
        logging.error("[I2C]: MCP thermocouple amplifier measurements have failed at COUNTER = "+str(COUNTER)+", timestamp = "+str(datetime.utcnow().isoformat()))
        logging.error("[I2C]: "+e) 


    data_list[COUNTER][0] = timestamp.isoformat()+'Z'
    
    COUNTER += 1
    

    if COUNTER == batch_size:
        file_name = timestamp.strftime('%Y%m%d_%H_%M')+'.csv'
        file_write_thread = threading.Thread(target=file_writer, args = (file_name, directory, header, data_list))
        file_write_thread.start()

        cloud_upload_thread = threading.Thread(target=cloud_upload, args = (APP_ID,BROKER_ADDRESS,SAMPLING_PERIOD, message, data_list))
        cloud_upload_thread.start()
        
        COUNTER = 0

        print(str(batch_size)+" messages sucessfully transmitted and locally stored")
        logging.info("[Events]: "+str(batch_size)+" messages sucessfully transmitted and locally stored at "+str(timestamp))
        
    
    # Hold button on GPIO17 to exit script
    if button.value == False:
        break
       
    delay = (datetime.utcnow() - timestamp).microseconds
    # print(max(SAMPLING_PERIOD - delay*(10**-6),0.01))
    time.sleep(max(SAMPLING_PERIOD - delay*(10**-6),0.01))

print("TEG profiler cloud script interrupted")    
logging.info('[Events]: TEG profiler cloud script interrupted at '+str(datetime.utcnow().isoformat()))    
print("data acquisition complete")





    


