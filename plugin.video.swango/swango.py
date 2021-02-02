#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Wrapper pre SWAN Go
"""

import httplib
import urllib
import json
import requests
import certifi
import datetime
import time
from xml.dom import minidom 
import os  
import codecs
__author__ = "janschml"
__license__ = "MIT"
__version__ = "0.1.0"
__email__ = "ja.schm@gmail.com"


_COMMON_HEADERS = { "User-Agent" :	"okhttp/3.12.1",
                    "Connection": "Keep-Alive"}



class SwangoException(BaseException):
    def __init__(self, detail={}):
        self.detail = detail

class ChannelIsNotBroadcastingError(BaseException):
    pass

class PairingError(BaseException):
    def __init__(self, detail={}):
        self.detail = detail
    pass

class ToManyDeviceError(BaseException):
    def __init__(self, detail={}):
        self.detail = detail
    pass

class AuthenticationError(BaseException):
    def __init__(self, detail={}):
        self.detail = detail
    pass

class SWANGO:

    def __init__(self,username =None,password=None,device_token=None, device_type_code = None, model=None,name=None, serial_number=None):
        self.username = username
        self.password = password
        self._live_channels = {}
        self.device_token = device_token
        self.subscription_code = None
        self.locality = None
        self.offer = None
        self.device_type_code = device_type_code
        self.model = model
        self.name = name
        self.serial_number = serial_number
        self.epgids=[]
        self.channels=[]

    def logdevicestartup(self):
        headers = _COMMON_HEADERS
        headers["Content-Type"] = "application/json;charset=utf-8"
        data = {'device_token' : self.device_token,
                'application': "3.1.12",
                'firmware': "22" }
        req = requests.post('https://backoffice.swan.4net.tv/api/device/logDeviceStart', json=data,headers=headers)
        j=req.json()
        return j['success']
        
 
    def pairingdevice(self):
        result=-1
        if not self.username or not self.password:
            raise AuthenticationError()
        headers = _COMMON_HEADERS
        headers["Content-Type"] = "application/json;charset=utf-8"
        data = {  'login' : self.username,
                'password' : self.password,
                'id_brand' : 1}
        
                    #Pairing device
        req = requests.post('https://backoffice.swan.4net.tv/api/device/pairDeviceByLogin', json=data,headers=headers)
        j = req.json()
        print(j)
        
        if "validation_errors" in j['message'] and j['success']==False:
            raise ToManyDeviceError({'error' : j['message']['validation_errors'][0]})
        elif j['success']==False:
            print(j['message'])
            raise AuthenticationError({'error' : str(j['message'])})
        elif j['success']==True:
            self.device_token=j['token']
            data = {'device_token' : self.device_token,
                    'device_type_code' : self.device_type_code,
                    'model' : self.model,
                    'name' : self.name,
                    'serial_number' : self.serial_number }
                        
            req = requests.post('https://backoffice.swan.4net.tv/api/device/completeDevicePairing', json=data,headers=headers)
            return self.device_token
        else:
            raise PairingError({'error' : j['message']})

        
     

    def get_devicesetting(self):
        headers = _COMMON_HEADERS
        headers["Content-Type"] = "application/json;charset=utf-8"
        data = {'device_token' : self.device_token}
        req = requests.post('https://backoffice.swan.4net.tv/api/getDeviceSettings/', json=data, headers=headers)
        j = req.json()
        self._device_settings=j
        return self._device_settings

        
    def get_stream(self, ch_id):
        channels=self.getchannels()
        for ch in  channels:
            if ch_id == ch['id_epg']:
                return ch['content_source']

    def getchannels(self):
        ch =list()
        headers = _COMMON_HEADERS
        headers["Content-Type"] = "application/json;charset=utf-8"
        data = {'device_token' : self.device_token}
        req = requests.post('https://backoffice.swan.4net.tv/api/device/getSources', json=data, headers=headers)
        j = req.json()

        for channel in j['channels']:
            ch ={ 'name' : channel['name'],
                'id_epg' : channel['id_epg'],
                'tvg-name' : channel['name'].replace(" ","_"),
                'tvg-logo' : "https://epg.swan.4net.tv/files/channel_logos/"+str(channel['id'])+".png",
                'content_source' :  channel['content_sources'][0]['stream_profile_urls']['adaptive'] }
            self.channels.append(ch)
            
        
        return self.channels

    def generateplaylist(self, playlistpath):
        channels = self.getchannels()
        with codecs.open(playlistpath , 'w',encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for channel in channels:
                # for tvheadend
                # strtmp="#EXTINF:-1 tvg-id=\""+str(channel['id_epg'])+"\" tvg-logo=\"https://epg.swan.4net.tv/files/channel_logos/"+str(channel['id'])+".png\" channel=\""+channel['name']+" tvg-name=\""+channel['name']+"\","+channel['name']+"\npipe:///storage/.kodi/addons/tools.ffmpeg-tools/bin/ffmpeg -fflags +genpts -i \""+channel['content_sources'][0]['stream_profile_urls']['adaptive']+"\" -vcodec copy -acodec copy -f mpegts  -mpegts_service_type digital_tv -metadata service_provider="+str(channel['id'])+" -metadata service_name= pipe:1"

                # for IPTV Simple client
                strtmp="#EXTINF:-1 tvg-id=\""+str(channel['id_epg'])+"\" tvg-name=\""+channel['tvg-name']+"\" tvg-logo=\""+channel['tvg-logo']+"\", "+channel['name']+"\n"+channel['content_source']
        
                f.write("%s\n" % strtmp)
        return 1

    def generateepg(self,days,epgpath):
        guide = minidom.Document() 
        tv = guide.createElement('tv') 
        
        #Get channels
        channels = self.getchannels()

        for chnl in channels:
            channel=guide.createElement('channel')
            channel.setAttribute('id',str(chnl['id_epg']))

            display_name=guide.createElement('display-name')
            display_name.setAttribute('lang','sk')
            display_name.appendChild(guide.createTextNode(chnl['name']))
            channel.appendChild(display_name)

            icon=guide.createElement('icon')
            icon.setAttribute('src',chnl['tvg-logo'])
            channel.appendChild(icon)

            tv.appendChild(channel)
          
        epg=""
        for epgid in self.epgids:
            epg+=str(epgid)+","
        epg=epg[:-1]     
        today=datetime.datetime.now().replace(hour=23,minute=0,second=0,microsecond=0)
        #today.replace(tzinfo='timezone.utc').astimezone(tz=None)
        fromdat=today-datetime.timedelta(days=1)
        todat=today+datetime.timedelta(days=days)
        fromdt=int((fromdat-datetime.datetime(1970,1,1)).total_seconds())
        todt=int((todat-datetime.datetime(1970,1,1)).total_seconds())
        
        headers = _COMMON_HEADERS
        headers["Content-Type"] = "application/json;charset=utf-8"
        data={"epg_id":epg,
            "from":str(fromdt),
            "to":str(todt),
            "lng" :"slk",
             }

        req = requests.get('https://epg.swan.4net.tv/export/broadcast', params=data, headers=headers)
        j = req.json()

        #with open('epg.json') as json_file:
        #    j = json.load(json_file)

        tz=time.timezone
        m, s = divmod(tz, 60)
        h, m = divmod(m, 60)
        if tz >=0:
            timez="+"+'{0:02d}'.format(h)+'{0:02d}'.format(m)
        else:
            timez='{0:03d}'.format(h)+'{0:02d}'.format(m)

        for prg in j['broadcasts']:
            programme=guide.createElement('programme')
            programme.setAttribute('channel',str(prg['epg_id']))
            startdt=datetime.datetime.utcfromtimestamp(prg['startTimestamp']+tz)
            programme.setAttribute('start',str(startdt.strftime("%Y%m%d%H%M%S " ))+timez)
            stopdt=datetime.datetime.utcfromtimestamp(prg['endTimestamp']+tz)
            programme.setAttribute('stop',str(stopdt.strftime("%Y%m%d%H%M%S "))+timez)
            
            
            title=guide.createElement('title')
            title.setAttribute('lang','sk')
            title.appendChild(guide.createTextNode(prg['name']))
            programme.appendChild(title)

            desc=guide.createElement('desc')
            desc.setAttribute('lang','sk')
            if 'description' in prg:
                desc.appendChild(guide.createTextNode(prg['description']))
            else:
                desc.appendChild(guide.createTextNode(" "))
            programme.appendChild(desc)
            

            dat=guide.createElement('year')
            if 'year' in prg:
                dat.appendChild(guide.createTextNode(str(prg['year'])))
            else:
                dat.appendChild(guide.createTextNode(" "))
            programme.appendChild(dat)
            

            category=guide.createElement('category')
            category.setAttribute('lang','sk')
            if 'genre' in prg:
                category.appendChild(guide.createTextNode(prg['genre']))
            elif 'format' in prg:
                category.appendChild(guide.createTextNode(prg['format']))
            else:
                category.appendChild(guide.createTextNode(" "))
            programme.appendChild(category)

            icon=guide.createElement('icon')
            if 'thumbnailUrl300' in prg:
                icon.setAttribute('src',str(j['image_server'])+str(prg['thumbnailUrl300']))
            programme.appendChild(icon)
            

            tv.appendChild(programme)

        guide.appendChild(tv) 

        xml_str = guide.toprettyxml(indent ="\t", encoding="utf-8")  
        #guide.toprettyxml(encoding="utf-8")

        with codecs.open(epgpath, "wb") as f: 
            f.write(xml_str)  
        return 1