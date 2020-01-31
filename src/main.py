#Author: Krzysztof Brzozowski

from machine import Pin, I2C, deepsleep, RTC
import machine
from BME280 import *
from APIrequests import *
from backup import *

import time

from ubinascii import hexlify as hex
import network


API_url = 'Your API url'
AUTH_TOKEN = 'Your API token'
BACKUP_FOLDER = 'backup_logs'
SSID = 'Your SSID'
PASSWD = 'Your PASSWD'

WLAN_ITERS = 40       # Iterations for wifi connection try. 
WLAN_CONN_SLEEP = 200 # Time sleep for wifi connection.

TIME_DEEP_SLEEP = 5
DEEP_SLEEP_CORRECTION_TIME_MS = 8000

TIME_DEEP_SLEEP_S = TIME_DEEP_SLEEP * 60
TIME_DEEP_SLEEP_MS = (TIME_DEEP_SLEEP * 60 * 1000) + DEEP_SLEEP_CORRECTION_TIME_MS


CORRECTION_TIME_S = int((WLAN_ITERS * WLAN_CONN_SLEEP) / 1000)

i2c = I2C(scl=Pin(5), sda=Pin(4), freq=10000)
bme280 = BME280(i2c=i2c)

wlan = network.WLAN(network.STA_IF)
adc = machine.ADC(0)
rtc = RTC()


def sync_time(server_time):
    try:
        rtc.datetime(server_time)
        return True
    except:
        return False
        
        
def custom_map(val, in_min, in_max, out_min, out_max):
    return round((val - in_min) * (out_max - out_min) / (in_max - in_min) + out_min, 2)

      
def deep_sleep(msecs):
  rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
  rtc.alarm(rtc.ALARM0, msecs)
  deepsleep()
  

def mean(data):
    if iter(data) is data:
        data = list(data)
    return sum(data)/len(data)


def get_measurement():
    readings = {'temperature': [], 'humidity': [], 'pressure': []}
    for n in range(4):
        for k, v in bme280.values.items():
            readings[k].append(v)   
        time.sleep_ms(100)
  
    return {k: round(mean(v[1:]), 2) for k, v in readings.items()}


def do_connect(ssid, pwd, hard_reset=True):
    if not pwd or not ssid :
        wlan.active(False)
        return None

    for t in range(0, WLAN_ITERS):
        if wlan.isconnected():
            return wlan
        print('attempting to connect to WiFi: {}'.format(t))

        if t == int(WLAN_ITERS) / 2 and hard_reset:
            wlan.active(True)
            wlan.connect(ssid, pwd)
            print('rst')
            
            
        time.sleep_ms(WLAN_CONN_SLEEP)
        
    return None


def blink(amount, time_ms):
    led = Pin(2, Pin.OUT)
    for i in range(amount):
        led.value(False)
        time.sleep_ms(time_ms)
        led.value(True)
        time.sleep_ms(time_ms)


# MAIN
charging = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
if not charging.value():
    deep_sleep(TIME_DEEP_SLEEP_MS)
    
api = APIRequests(API_url=API_url, auth_token=AUTH_TOKEN)
backup = Backup(BACKUP_FOLDER, API_url, AUTH_TOKEN, TIME_DEEP_SLEEP_S, CORRECTION_TIME_S)

do_connect(SSID, PASSWD)

voltage = custom_map(adc.read(), 0, 1024, 0, 4.2)
data = get_measurement()
data.update({'mac_address': hex(network.WLAN().config('mac'),':').decode(), 'adc': voltage})



# Send data directy to server.
try:
    if wlan.isconnected():
        sync = sync_time(api.get_server_time())
        print(sync)
        backup.send_backup(sync)
        api.post(data)
        print('sent to server')
        
    # Write data to internal memory if there is no WLAN connection.
    else:
        backup.write_backup(data)
        blink(4, 35)
        print('wrote to internal memory')

       
except Exception as e:
    blink(8, 35)
    backup.write_backup(data)
    print(e)


deep_sleep(TIME_DEEP_SLEEP_MS)


