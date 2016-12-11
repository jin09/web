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
import urllib2
import requests
import webapp2
import jinja2
import os
from google.appengine.ext import db
import requests_toolbelt.adapters.appengine
from operator import itemgetter

# Use the App Engine Requests adapter. This makes sure that Requests uses
# URLFetch.


requests_toolbelt.adapters.appengine.monkeypatch()

jinja_env = jinja2.Environment(autoescape=True,
                               loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))


vendor_pass = "$108vendor$"

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


class RequestNew(db.Model):
    type = db.StringProperty(required=True)
    injured = db.StringProperty(required=True)
    latitude = db.StringProperty(required=True)
    longitude = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    phone = db.StringProperty(required=True)
    sms_number = db.StringProperty(required=True)
    pending = db.StringProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)
    address = db.StringProperty(required=True)


class MainHandler(Handler):
    def get(self):
        all_data = db.GqlQuery("select * from RequestNew order by date desc")
        self.render("front.html", all_data=all_data)

    def post(self):
        phone = self.request.get("search")
        all_data = db.GqlQuery("select * from RequestNew order by date desc")
        self.render("search.html", all_data=all_data, phone=phone)


def get_address_from_coordinates(lat, lon):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json?sensor=true&key=AIzaSyCYm1G4k9BaFfR7SodrKld5edoZehubg9M&latlng="
    url = base_url + str(lat) + "," + str(lon)
    logging.error(" in function  "+url)
    response = None
    try:
        response = urllib2.urlopen(url).read()
        logging.error(" in function  "+response)
        dictionary = json.loads(response)
        results = dictionary["results"]
        first_dict = results[0]
        formatted_address = first_dict["formatted_address"]
        logging.error(" in function  "+formatted_address)
        return formatted_address
    except:
        return "could not connect to google maps api"


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
            self.response.out.write("Token inserted succesfully !! :D--     " + str(token))
        else:
            logging.error("Token already exists!!")
            self.response.out.write("Token already exists!! ")


class SendHandler(Handler):
    def get(self):
        url = 'https://fcm.googleapis.com/fcm/send'
        body = {
            "message": "yolo"
        }
        headers = {"Content-Type": "application/json",
                   "Authorization": "key=AIzaSyCtgWcLXQadrtVjB_Dp_wWhzQhiK1FHd4c"}
        token_list = []
        all_data = db.GqlQuery("select * from Token")
        for i in all_data:
            token_list.append(i.token)
        # self.response.out.write(str(token_list))
        body["registration_ids"] = token_list
        logging.error(json.dumps(body))
        x = requests.post(url, data=json.dumps(body), headers=headers)
        self.response.out.write(str(x.text))


class SendRequestHandler(Handler):
    def get(self):
        type = self.request.get("type")
        injured = self.request.get("injured")
        lattitude = self.request.get("latitude")
        longitude = self.request.get("longitude")
        logging.error("inside send receiver handler   " + lattitude)
        logging.error("inside send receiver handler   " + longitude)
        name = self.request.get("name")
        phone = self.request.get("phone")
        smsnumber = "[NO]--[DIRECT]"
        pending = "1"
        address = get_address_from_coordinates(lattitude, longitude)
        logging.error("inside send handler   "+address)
        # self.response.out.write(type+injured+lattitude+longitude+name+phone)
        log_message = ""
        all_request = db.GqlQuery("select * from RequestNew")
        found = False
        for i in all_request:
            if i.phone == phone:
                i.delete()
                updated_request = RequestNew(type=type,
                                             injured=injured,
                                             latitude=lattitude,
                                             longitude=longitude,
                                             name=name,
                                             phone=phone,
                                             pending=pending,
                                             sms_number=smsnumber,
                                             address=address
                                             )
                updated_request.put()
                found = True
                log_message = "duplicate message found" + '\n' + type + '\n' + injured + \
                              '\n' + lattitude + '\n' + longitude + '\n' + name + '\n' + phone + '\n' + pending + '\n' \
                              + smsnumber
                break

        if not found:
            request = RequestNew(type=type,
                                 injured=injured,
                                 latitude=lattitude,
                                 longitude=longitude,
                                 name=name,
                                 phone=phone,
                                 pending=pending,
                                 sms_number=smsnumber,
                                 address=address
                                 )
            request.put()
            log_message = "new message" + '\n' + type + '\n' + injured + \
                          '\n' + lattitude + '\n' + longitude + '\n' + name + '\n' + phone + '\n' + pending + '\n' \
                          + smsnumber
        self.response.out.write(log_message)
        self.redirect('/send')


class SmsHandler(Handler):
    def get(self):
        type = self.request.get("type")
        injured = self.request.get("injured")
        lattitude = self.request.get("latitude")
        longitude = self.request.get("longitude")
        logging.error("inside sms receiver handler   " + lattitude)
        logging.error("inside sms receiver handler   " + longitude)
        name = self.request.get("name")
        phone = self.request.get("phone")
        sms_number = self.request.get("smsnumber")
        pending = "1"
        address = get_address_from_coordinates(lattitude, longitude)
        logging.error("inside sms receiver handler   " + address)
        log_message = ""
        all_request = db.GqlQuery("select * from RequestNew")
        found = False
        for i in all_request:
            if i.phone == phone:
                i.delete()
                updated_request = RequestNew(type=type,
                                             injured=injured,
                                             latitude=lattitude,
                                             longitude=longitude,
                                             name=name,
                                             phone=phone,
                                             pending=pending,
                                             sms_number=sms_number,
                                             address=address
                                             )
                updated_request.put()
                found = True
                log_message = "duplicate message/number found but updated" + '\n' + type + '\n' + injured + \
                              '\n' + lattitude + '\n' + longitude + '\n' + name + '\n' + phone + '\n' + pending + '\n' \
                              + sms_number
                break
        if not found:
            request = RequestNew(type=type,
                                 injured=injured,
                                 latitude=lattitude,
                                 longitude=longitude,
                                 name=name,
                                 phone=phone,
                                 pending=pending,
                                 sms_number=sms_number,
                                 address=address
                                 )
            request.put()
            log_message = "new message/number found--- INSERTED" + '\n' + type + '\n' + injured + \
                          '\n' + lattitude + '\n' + longitude + '\n' + name + '\n' + phone + '\n' + pending + '\n' \
                          + sms_number
        self.response.out.write(log_message)
        self.redirect('/send')


class JsonHandler(Handler):
    def get(self):
        all_requests = db.GqlQuery("select * from RequestNew order by date desc")
        list = []
        for i in all_requests:
            if i.pending == "1":
                inner_dict = {"type": i.type, "injured": i.injured, "latitude": i.latitude, "longitude": i.longitude,
                              "name": i.name, "phone": i.phone, "pending": i.pending, "smsnumber": i.sms_number,
                              "address": i.address}
                list.append(inner_dict)
        main_dict = {"list": list}
        json_text = json.dumps(main_dict)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_text)


class CompletedHandler(Handler):
    def get(self):
        phone = self.request.get("phone")
        all_requests = db.GqlQuery("select * from RequestNew")
        found = False
        for i in all_requests:
            if i.phone == phone:
                request = RequestNew(type=i.type,
                                     injured=i.injured,
                                     latitude=i.latitude,
                                     longitude=i.longitude,
                                     name=i.name,
                                     phone=i.phone,
                                     pending="0",
                                     sms_number=i.sms_number,
                                     address=i.address
                                     )
                i.delete()
                request.put()
                logging.error("Number found and request completed , database updated")
                self.response.out.write("Number found and request completed , database updated")
                found = True
                break
        if not found:
            logging.error("Number not found, Database intact")
            self.response.out.write("Number not found, Database intact")


class RegisteredPlacesHandler(Handler):
    def get(self):
        latitude = self.request.get("lat")
        longitude = self.request.get("lng")
        self.render("registeredplaces.html")


def get_time_and_seconds(user_lat, user_lng, des_lat, des_lng):
    link = "https://maps.googleapis.com/maps/api/distancematrix/json?units=metric&key=AIzaSyCs_p6e1Od8lpXiEnTa2H9QxkhLOZxmefQ&" \
           "origins=" + user_lat + "," + user_lng + "&destinations=" + des_lat + "," + des_lng
    x = requests.get(link).text
    # print(x)
    obj = json.loads(x)
    destination_list = obj["destination_addresses"]
    des_addr = destination_list[0]
    list = obj["rows"]
    # print(list)
    obj = list[0]
    # print(obj)
    list = obj["elements"]
    # print(list)
    obj = list[0]
    obj = obj["duration"]
    # print(obj)
    text = obj["text"]
    value = obj["value"]
    print(text)
    print(value)
    return text, value, des_addr


class RegisteredPlacesComputationHandler(Handler):
    def get(self):
        user_lat = self.request.get("lat")
        user_lng = self.request.get("lng")
        registered_json = """
            {"places": [{"lat": "13.020668", "lon": "80.22427", "name": "SAIDAPET GH"}, {"lat": "13.11083", "lon": "80.26087", "name": "VYASARPADI GANESH PURAM PHC"}, {"lat": "13.094067", "lon": "80.273587", "name": "SALT QUARTERS"}, {"lat": "13.098669", "lon": "80.215774", "name": "ICF POLICE STATION"}, {"lat": "12.985322", "lon": "80.223064", "name": "VELACHERRY CORPORATION OFFICE"}, {"lat": "13.067068", "lon": "80.207779", "name": "KOYAMBEDU SAF QUATRESS"}, {"lat": "13.125934", "lon": "80.286887", "name": "TONDIARPET CDH"}, {"lat": "13.007737", "lon": "80.22529", "name": "GOVERNOR HOUSE CHENNAI"}, {"lat": "13.060429", "lon": "80.278406", "name": "TRIPLICANE NEO 2"}, {"lat": "13.047168", "lon": "80.249103", "name": "DMS"}, {"lat": "13.086801", "lon": "80.285882", "name": "MADRAS HIGH COURT"}, {"lat": "13.072557", "lon": "80.258072", "name": "ICH-1 EGMORE"}, {"lat": "13.000132", "lon": "80.255865", "name": "ADAYAR CORP. HOSPITAL"}, {"lat": "13.067853", "lon": "80.251622", "name": "GREAMS ROAD"}, {"lat": "13.131869", "lon": "80.25854", "name": "M.K.B.NAGAR"}, {"lat": "13.085169", "lon": "80.187351", "name": "MOGAPAIR"}, {"lat": "13.060673", "lon": "80.278445", "name": "TRIPLICANE HEAD OFFICE"}, {"lat": "12.948692", "lon": "80.240877", "name": "OKKIYAM THURAIPAKKAM"}, {"lat": "13.098981", "lon": "80.230269", "name": "AYNAVARAM  PHC"}, {"lat": "13.077867", "lon": "80.218453", "name": "ANNA NAGAR SIDDHA HOSPITAL"}, {"lat": "13.115335", "lon": "80.223571", "name": "PERIYAR NAGAR PHERIPHERAL HOSPITAL"}, {"lat": "13.034898", "lon": "80.209654", "name": "K.K NAGAR PERIPHERAL HOSPITAL"}, {"lat": "13.070565", "lon": "80.275052", "name": "MULTI SPECIALITY HOSPITAL"}, {"lat": "13.061603", "lon": "80.263893", "name": "TAJ BUSINESS HOTELS MOUNT ROAD"}, {"lat": "13.051992", "lon": "80.21924", "name": "KODAMBAKKAM POWER HOUSE PHC"}, {"lat": "13.077175", "lon": "80.242515", "name": "CHETPET"}, {"lat": "13.022883", "lon": "80.276197", "name": "PATTINABAKKAM"}, {"lat": "13.034899", "lon": "80.229481", "name": "T NAGAR POLICE STATION"}, {"lat": "13.029442", "lon": "80.237528", "name": "NANDANAM FIRE STATION"}, {"lat": "12.92302", "lon": "80.154915", "name": "SEMBAKKAM MUNICIPAL CORPERATION"}, {"lat": "12.845603", "lon": "80.061915", "name": "GUDUVANCHERY NANDHIVARAM PHC"}, {"lat": "12.997492", "lon": "80.097677", "name": "KUNDRATHUR PHC"}, {"lat": "12.615018", "lon": "79.760659", "name": "UTHIRAMERUR GH "}, {"lat": "12.794392", "lon": "79.817221", "name": "WALAJABAD PHC"}, {"lat": "13.004615", "lon": "80.202773", "name": "ALANDHUR MUNICIPALITY OFFICE"}, {"lat": "12.877589", "lon": "79.614176", "name": "THIRUPPUKUZHI PHC"}, {"lat": "12.809957", "lon": "79.686388", "name": "STATE HIGHWAY"}, {"lat": "12.833595", "lon": "79.709855", "name": "KANCHEEPURAM GH Neo"}, {"lat": "12.834368", "lon": "79.70976", "name": "KANCHIPURAM GH"}, {"lat": "12.891923", "lon": "80.021643", "name": "PADAPPAI PHC"}, {"lat": "12.926172", "lon": "80.118104", "name": "TAMBARAM LOCAL TOWN"}, {"lat": "12.903152", "lon": "79.81691", "name": "PILLAICHATHIRAM PANCHAYAT OFFICE"}, {"lat": "12.676893", "lon": "79.979482", "name": "CHENGALPET GH-NEONATAL"}, {"lat": "12.446249", "lon": "80.00643", "name": "PAVUNCHUR PHC"}, {"lat": "12.802211", "lon": "80.025733", "name": "MARAIMALAINAGAR MUNICIPALITY OFFICE"}, {"lat": "12.789932", "lon": "80.220446", "name": "KELAMBAKKAM PHC"}, {"lat": "12.677661", "lon": "79.980298", "name": "CHENGALPATTU MEDICAL COLLEGE"}, {"lat": "12.509232", "lon": "79.89012", "name": "MADURANTHAGAM GH"}, {"lat": "12.900857", "lon": "80.231701", "name": "SHOLINGANALLUR PRATHYANKARA KOIL"}, {"lat": "12.904726", "lon": "80.104183", "name": "PERUNGALATHUR (PEERKANKARANAI PHC)"}, {"lat": "12.957002", "lon": "79.944256", "name": "SRIPERUMBUDHUR NH MAIN ROAD"}, {"lat": "12.442922", "lon": "80.107515", "name": "KOVATHUR PHC"}, {"lat": "12.833467", "lon": "79.702332", "name": "KANCHEEPURAM POLICE STATION"}, {"lat": "12.606604", "lon": "80.058647", "name": "THIRUKUZHUKUNDRAM GH"}, {"lat": "12.834021", "lon": "79.703053", "name": "KANCHEEPURAM BUS STAND"}, {"lat": "12.945503", "lon": "80.134294", "name": "CHROMPAT(GH)"}, {"lat": "12.434905", "lon": "79.832717", "name": "MELMARUVATHUR ROUND BUILDING"}, {"lat": "12.973237", "lon": "80.15228", "name": "PALLAVARAM"}, {"lat": "12.617849", "lon": "80.180872", "name": "MAMALLAPURAM GH"}, {"lat": "12.718989", "lon": "79.754219", "name": "MAAKARAL POLICE STATION"}, {"lat": "12.677661", "lon": "79.980298", "name": "CHENGALPET LOCAL TOWN"}, {"lat": "12.808312", "lon": "79.762636", "name": "AYYANPETTAI PHC"}, {"lat": "12.351933", "lon": "80.002639", "name": "CHEYYUR GH"}, {"lat": "12.915364", "lon": "80.192513", "name": "MEDAVAKKAM CORPORATION HOSPITAL"}, {"lat": "12.875354", "lon": "80.210862", "name": "SEMMANCHERRI PHC"}, {"lat": "13.123456", "lon": "80.123456", "name": "SPARE-7 KANCHEEPURAM"}, {"lat": "12.845475", "lon": "80.226272", "name": "NAVALUR POLICE STATION"}, {"lat": "12.761316", "lon": "80.001803", "name": "SINGAPERUMAL KOIL"}, {"lat": "12.959404", "lon": "79.67106", "name": "THIRUMALPUR-AGARAM"}, {"lat": "12.547648", "lon": "79.90617", "name": "KARUNKUZHI"}, {"lat": "12.951176", "lon": "80.249403", "name": "NEELANGARAI POLICE STATION"}, {"lat": "13.332584", "lon": "80.197446", "name": "CIFT - PONNERI GH"}, {"lat": "13.127687", "lon": "79.911139", "name": "THIRUVALLUR NEONATAL"}, {"lat": "13.074702", "lon": "80.020273", "name": "NEMAM PHC"}, {"lat": "13.172893", "lon": "79.502022", "name": "BEERAKUPPAM PHC"}, {"lat": "13.187743", "lon": "80.183995", "name": "RED HILLS(NARAVARIKUPPAM PHC"}, {"lat": "13.042721", "lon": "80.081489", "name": "NASARATHPETTAI PHC"}, {"lat": "13.177375", "lon": "79.614342", "name": "THIRUTHANI 2"}, {"lat": "13.109814", "lon": "80.182683", "name": "KORATTUR POLICE STATION"}, {"lat": "13.033565", "lon": "79.853364", "name": "MAPPEDU"}, {"lat": "13.311719", "lon": "80.043098", "name": "PERIYAPALAYAM PHC"}, {"lat": "13.363807", "lon": "80.138499", "name": "KAVARAPETTAI HSC"}, {"lat": "13.036972", "lon": "80.169948", "name": "VALASARAVAKKAM(PORUR PHC)"}, {"lat": "13.163235", "lon": "80.202121", "name": "PUZHAL"}, {"lat": "13.416322", "lon": "80.313849", "name": "PAZAVARKADU GH"}, {"lat": "13.049183", "lon": "80.107246", "name": "POONAMALLE MATERNITY CHC"}, {"lat": "13.282414", "lon": "79.48433", "name": "PODHADURPET AASHRAMAM"}, {"lat": "13.14473", "lon": "79.896709", "name": "THIRUVALLUR LOCAL TOWN"}, {"lat": "13.12788", "lon": "79.910833", "name": "THIRUVALLUR RTO OFFICE"}, {"lat": "13.20328", "lon": "80.173041", "name": "PADIYANALLUR PHC"}, {"lat": "13.416003", "lon": "80.129895", "name": "GUMMUDIPOONDI GH"}, {"lat": "13.144101", "lon": "80.21962", "name": "MADHAVARAM BYPASS"}, {"lat": "13.203878", "lon": "79.756185", "name": "KANAKAMACHATHRAM PHC"}, {"lat": "13.125187", "lon": "80.029698", "name": "THIRUNINDRAVUR PERURATCHI"}, {"lat": "13.174058", "lon": "79.619851", "name": "TIRUTANI GH"}, {"lat": "13.10629", "lon": "80.152779", "name": "AMBATTUR MUNICIPALITY OFFICE"}, {"lat": "13.277104", "lon": "80.261004", "name": "MEENJUR PHC"}, {"lat": "13.098665", "lon": "79.860955", "name": "KADAMBATTUR UNION OFFICE"}, {"lat": "13.333012", "lon": "79.898227", "name": "UTHUKOTTAI GH"}, {"lat": "13.213746", "lon": "80.320031", "name": "KATHIVAKKAM PHC"}, {"lat": "13.117327", "lon": "80.098025", "name": "AVADI PHC"}, {"lat": "13.128157", "lon": "79.911021", "name": "CIFT THIRUVALLUR GH"}, {"lat": "13.062914", "lon": "80.166322", "name": "MADHURAVAYIL MUNICIPALITY"}]}
            """
        x = json.loads(registered_json)
        list = x["places"]
        output_list = []
        for i in list:
            inner_dict = {}
            des_lat = i["lat"]
            des_lng = i["lon"]
            text, value, des_addr = get_time_and_seconds(user_lat, user_lng, des_lat, des_lng)
            inner_dict["name"] = i["name"]
            inner_dict["lat"] = des_lat
            inner_dict["lng"] = des_lng
            inner_dict["text"] = str(text)
            inner_dict["value"] = value
            inner_dict["addr"] = des_addr
            output_list.append(inner_dict)
        output_list = sorted(output_list, key=itemgetter("value"))
        output_dict = {"results": output_list}
        x = json.dumps(output_dict)
        self.response.out.write(x)


class ServiceCompleteHandler(Handler):
    def get(self):
        self.render("servicecomplete.html")

    def post(self):
        phone = self.request.get("phone")
        password = self.request.get("password")
        if password == vendor_pass:
            self.redirect("/requestcomplete?phone="+phone)
        else:
            self.response.out.write("Invalid Vendor Password!")


class PrivatePlacesHandler(Handler):
    def get(self):
        type = self.request.get("type")
        user_lat = self.request.get("lat")
        user_lng = self.request.get("lng")
        URL = ""
        if type == "MEDICAL EMERGENCY":
            URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?rankBy=distance&keyword=ambulance&key=AIzaSyD-Tp_QBh58mlcEmSaeD4ii48X5wHWU7sI&location="+user_lat+","+user_lng
        if type == "FIRE EMERGENCY":
            URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?rankBy=distance&keyword=fire%20station&key=AIzaSyD-Tp_QBh58mlcEmSaeD4ii48X5wHWU7sI&location="+user_lat+","+user_lng
        if type == "CRIME EMERGENCY":
            URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?rankBy=distance&keyword=police&key=AIzaSyD-Tp_QBh58mlcEmSaeD4ii48X5wHWU7sI&location="+user_lat+","+user_lng
        x = requests.get(URL)
        x = x.text
        x = json.loads(x)
        results = x["results"]
        final_list = []
        for i in results:
            inner_dict = {}
            usr_lat = str(user_lat)
            usr_lng = str(user_lng)
            lat = i["geometry"]["location"]["lat"]
            lng = i["geometry"]["location"]["lng"]
            placeID = i["place_id"]
            address = i["vicinity"]
            name = i["name"]
            place_details_url = "https://maps.googleapis.com/maps/api/place/details/json?key=AIzaSyD-Tp_QBh58mlcEmSaeD4ii48X5wHWU7sI&placeid="+placeID
            place_details = requests.get(place_details_url)
            place_details = json.loads(place_details.text)
            try:
                phone_number = place_details["result"]["international_phone_number"]
            except:
                phone_number = "Could not find!!"
            maps_distance_url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=metric&key=AIzaSyCs_p6e1Od8lpXiEnTa2H9QxkhLOZxmefQ&origins="+usr_lat+","+usr_lng+"&destinations="+str(lat)+","+str(lng)
            distance_details = requests.get(maps_distance_url)
            distance_details = json.loads(distance_details.text)
            rows = distance_details["rows"][0]
            text = rows["elements"][0]["duration"]["text"]
            value = rows["elements"][0]["duration"]["value"]
            inner_dict["lat"] = lat
            inner_dict["lng"] = lng
            inner_dict["name"] = name
            inner_dict["place_id"] = placeID
            inner_dict["addr"] = address
            inner_dict["phone"] = phone_number
            inner_dict["text"] = text
            inner_dict["value"] = value
            final_list.append(inner_dict)
        final_list = sorted(final_list, key=itemgetter("value"))
        output = {"result": final_list}
        json_string = json.dumps(output)
        self.response.out.write(json_string)


class SearchNearbyHandler(Handler):
    def get(self):
        self.render("googleplaces.html")


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/register', RegisterHandler),
    ('/send', SendHandler),
    ("/sendrequest", SendRequestHandler),
    ("/sendrequestsms", SmsHandler),
    ("/getjson", JsonHandler),
    ('/requestcomplete', CompletedHandler),
    ('/registeredplaces', RegisteredPlacesHandler),
    ('/registeredplacescompute', RegisteredPlacesComputationHandler),
    ('/vendorservicecomplete', ServiceCompleteHandler),
    ('/privateplaces', PrivatePlacesHandler),
    ("/searchnearby", SearchNearbyHandler)
], debug=True)
