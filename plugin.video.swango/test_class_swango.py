#!/usr/bin/env python
# -*- coding: utf-8 -*-

import swango

import codecs
 
_username_="601793"
_password_="7bPXcwSAD"
_device_token_="c7dc840ce19376d1d638b94ed9eb99bf" 
_device_type_code_="ANDROID_4_4PLUS"
_device_model_="Huawei"
_device_name_="HUAWEI SCL-L21"
_device_serial_number_="3MSDU16203000998"
_epgdays_=3
_epgpath_ = "epginfo.xml"
_playlistpath_ ="swan_playlist.m3u"

# Ziskane pomocou authenticate metody

_swango_ = swango.SWANGO(_username_, _password_,_device_token_,_device_type_code_,_device_model_,_device_name_,_device_serial_number_)
try:
    _swango_.device_token=_device_token_
    if _swango_.logdevicestartup() ==True:
        _swango_.generateplaylist(_playlistpath_)
        _swango_.generateepg(_epgdays_,_epgpath_)
    else:
        _swango_.pairingdevice()
        if _swango_.logdevicestartup() ==True:
            _swango_.generateplaylist(_playlistpath_)
            _swango_.generateepg(_epgdays_,_epgpath_)

except swango.ToManyDeviceError:
    print("To many device in SWAN Go service registered")
except swango.PairingError:
    print("Pairing device error")
except swango.AuthenticationError as e:
    print("Authentication error. Check Username and password in settings: " + e.detail['error'])
#ret=_swango_.live_channels()
#_swango_.generateplaylist()

