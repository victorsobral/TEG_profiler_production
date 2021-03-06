from os import listdir
from os.path import isfile, join
import requests
import json
import time
import csv

storage_path = '/home/pi/Desktop/shared/data'

server_address = "???.???.??.?:??" # format is IP:port 

with open("/home/pi/Desktop/Application_info.txt") as json_appInfo:
	APP_INFO = json.load(json_appInfo)

APP_ID = APP_INFO["APP_ID"]

filename_list = [f for f in listdir(storage_path) if isfile(join(storage_path, f))]

filename_list.sort()

with open('/home/pi/Desktop/shared/TEG_local_storage_list.txt', 'w') as file:
	csvwriter = csv.writer(file)
	for row in filename_list:
		csvwriter.writerow([row])

with open('/home/pi/Desktop/shared/TEG_local_storage_list.txt') as txt_file:
	r=requests.post("http://"+server_address+"/upload", files={'upload':txt_file}, headers={'APP_ID':APP_ID})
	time.sleep(0.2)

for filename in filename_list:
	with open(join(storage_path, filename)) as csv_file:
		r=requests.post("http://"+server_address+"/upload", files={'upload':csv_file}, headers={'APP_ID':APP_ID})
		time.sleep(0.2)



