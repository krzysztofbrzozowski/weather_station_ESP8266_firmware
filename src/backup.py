#Author: Krzysztof Brzozowski

from APIrequests import *
from machine import RTC
import os
import ujson
import network

class Backup:
    def __init__(self, backup_folder, API_url, AUTH_TOKEN, deep_sleep_t, correction_t):         
        self.backup_folder = backup_folder
        self.rtc = RTC()
        self.api = APIRequests(API_url=API_url, auth_token=AUTH_TOKEN)
        self.wlan = network.WLAN(network.STA_IF)
        self.deep_sleep_t = deep_sleep_t
        self.correction_t = correction_t
        if not self.backup_folder in os.listdir():
            os.mkdir(self.backup_folder)
        
        
    def get_rtc_datetime(self, usage=None):
        rtc_dt = self.rtc.datetime()
        if usage == 'timestamp':
            return '{}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}'.format(rtc_dt[0], rtc_dt[1], rtc_dt[2], rtc_dt[4], rtc_dt[5], rtc_dt[6])
        return 'D{}-{:02d}-{:02d}T{:02d}_{:02d}_{:02d}'.format(rtc_dt[0], rtc_dt[1], rtc_dt[2], rtc_dt[4], rtc_dt[5], rtc_dt[6])
    
    def get_timedelta(self, delta):
        return self.api.get('timedelta/{}'.format(delta))['timestamp']

    def write_backup(self, data):      
        data.update({'timestamp': self.get_rtc_datetime('timestamp')})
        with open('{}/{}.txt'.format(self.backup_folder, self.get_rtc_datetime()), 'a') as file:
            ujson.dump(data, file)
           
    def get_backup_list(self):
        return True if self.backup_folder in os.listdir() and os.listdir(self.backup_folder) else False
  
    def send_backup(self, sync):
        if self.get_backup_list():
            for idx, n in enumerate(reversed(os.listdir(self.backup_folder))):
                try:
                    if self.wlan.isconnected() and sync:
                        with open('{}/{}'.format(self.backup_folder, n)) as json_file:
                            data = ujson.load(json_file)
                            timedelta = self.get_timedelta(((idx + 1) * self.deep_sleep_t) + (self.correction_t * idx))
                            data['timestamp'] = timedelta
                            self.api.post(data)
                            os.remove('{}/{}'.format(self.backup_folder, n))
                            print('backup sent')
                    else:
                        return
                    
                except:
                    pass