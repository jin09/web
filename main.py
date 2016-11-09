#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
import logging
import requests
import webapp2
import jinja2
import os
from google.appengine.ext import db
import requests_toolbelt.adapters.appengine

# Use the App Engine Requests adapter. This makes sure that Requests uses
# URLFetch.


requests_toolbelt.adapters.appengine.monkeypatch()

jinja_env = jinja2.Environment(autoescape=True,
                               loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class Token(db.Model):
    token = db.StringProperty(required=True)


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Hello world!')


class RegisterHandler(Handler):
    def post(self):
        token = self.request.get("token")
        all_saved_tokens = db.GqlQuery("select * from Token")
        boolean = False
        for i in all_saved_tokens:
            if i.token == token:
                boolean = True
                break

        if not boolean:
            t = Token(token=str(token))
            t.put()
            logging.error("Token inserted succesfully !! :D===" + str(token))
            self.response.out.write("Token inserted succesfully !! :D--     "+str(token))
        else:
            logging.error("Token already exists!!")
            self.response.out.write("Token already exists!! ")


class SendHandler(Handler):
    def get(self):
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
        }
        headers = {"Content-Type": "application/json",
                   "Authorization": "key=AIzaSyCtgWcLXQadrtVjB_Dp_wWhzQhiK1FHd4c"}
        token_list = []
        all_data = db.GqlQuery("select * from Token")
        for i in all_data:
            token_list.append(i.token)
        #self.response.out.write(str(token_list))
        body["registration_ids"] = token_list
        logging.error(json.dumps(body))
        x = requests.post(url, data=json.dumps(body), headers=headers)
        self.response.out.write(str(x.text))

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/register', RegisterHandler),
    ('/send', SendHandler)
], debug=True)
