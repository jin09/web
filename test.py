import json
import logging

import requests
from google.appengine.api import urlfetch
import urllib2
import urllib

url = 'https://fcm.googleapis.com/fcm/send'
body = {
    "data": {
        "title": "data:mytitle",
        "body": "data:mybody",
        "url": "data:myurl"
    },
    "notification": {
        "title": "noti:My web app name",
        "body": "noti:message",
        "content_available": "noti:true"
    },
    "message": "yolo",
    "registration_ids": ["cJZhpjKP4-M:APA91bEzLLBDg87_7U3vfD3BBz9I4ykVJARejGn1HUADhAT3xSKDomSG53oEdI1_HeE3q1FEf4MrfOjt2rFF5ELta7W8mIceg-mUKT97w3W1cD30SdN1KULTPtXR_Uut5jl7ek80odg7"]
}
headers = {"Content-Type": "application/json",
           "Authorization": "key=AIzaSyCtgWcLXQadrtVjB_Dp_wWhzQhiK1FHd4c"}

logging.error(json.dumps(body))
x = requests.post(url, data=json.dumps(body), headers=headers)
print(str(x))