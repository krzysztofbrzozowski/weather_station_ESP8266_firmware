#Author: Krzysztof Brzozowski
 
import urequests
import ujson

class APIRequests:
    def __init__(self, API_url, auth_token):
        self.datetime = None
        self.auth_token = auth_token
        self.headers = {'Authorization': 'Token {}'.format(self.auth_token), 'Content-Type': 'application/json'}
        self.API_url = API_url
        self.request = None
        self.request_code = None
        
    def get_server_time(self):
        r = urequests.get(url='{}/timesync'.format(self.API_url))
        r_json = ujson.loads(r.text)
        r.close()
        return r_json['datetime_now']      
    
    def get(self, url):
        r = urequests.get(url='{}/{}'.format(self.API_url, url))
        r_json = ujson.loads(r.text)
        r.close
        return r_json
        
    def post(self, data):
        self.request = urequests.post(self.API_url, json=data, headers=self.headers)
        self.request_code = self.request.status_code
        self.request.close()
        return self.request_code