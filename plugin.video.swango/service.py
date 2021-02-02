import sys
import datetime
import os
import time
import requests
import swango
import xbmc
import xbmcaddon



class swangoMonitor(xbmc.Monitor):
    _addon = None
    _next_update = 0
    _scriptname = None

    def __init__(self):
        xbmc.Monitor.__init__(self)
        self._addon = xbmcaddon.Addon()
        self._scriptname = self._addon.getAddonInfo('name')
        ts = self._addon.getSetting('next_update')
        self._next_update = datetime.datetime.now() if ts == '' else datetime.datetime.fromtimestamp(float(ts))
        self.logDbg("Get settings next_update")
    
    def __del__(self):
        self.log('service destroyed')

    ###############################################################################
    def log(self, msg, level=xbmc.LOGDEBUG):
        if type(msg).__name__=='unicode':
            msg = msg.encode('utf-8')
        xbmc.log("[%s] %s"%(self._scriptname,msg.__str__()), level)

    def logDbg(self,msg):
        self.log(msg,level=xbmc.LOGDEBUG)

    def logErr(self,msg):
        self.log(msg,level=xbmc.LOGERROR)
    ###############################################################################

    def notify(self, text, error=False):
        icon = 'DefaultIconError.png' if error else ''
        try:
            xbmc.executebuiltin('Notification("%s","%s",5000,%s)' % (self._addon.getAddonInfo('name').encode("utf-8"), text, icon))
        except NameError as e:
            xbmc.executebuiltin('Notification("%s","%s",5000,%s)' % (self._addon.getAddonInfo('name'), text, icon))

    def onSettingsChanged(self):
        self._addon = xbmcaddon.Addon()  # refresh for updated settings!
        if not self.abortRequested():
            try:
                res = self.update(True)
                if res != -1:
                    self.notify("Playlist and EPG XML actualised. Setting aplied",False)
            except swango.SwangoException as e:
                self.notify("Unexpected Error", True)

    def schedule_next(self, seconds):
        dt = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        self.log('Next update %s' % dt)
        self._next_update = dt

    def update(self):
        result =-1
        try:
            
            self.log('Update playlist and epg started')
            _username_ = self._addon.getSetting("username")
            _password_ = self._addon.getSetting("password")
            _device_token_ = self._addon.getSetting("device_token")
            _device_type_code_ = self._addon.getSetting("device_type_code")
            _device_model_ = self._addon.getSetting("device_model")
            _device_name_ = self._addon.getSetting("device_name")
            _device_serial_number_ = self._addon.getSetting("device_serial_number")
            _epgdays_ = int(self._addon.getSetting("epgdays"))
            _epgpath_ = self._addon.getSetting("epgpath")
            _playlistpath_ = self._addon.getSetting("playlistpath")
            _swango_=swango.SWANGO(_username_, _password_,_device_token_,_device_type_code_,_device_model_,_device_name_,_device_serial_number_)
            _swango_.device_token=_device_token_
            if _swango_.logdevicestartup() ==True:
                if _swango_.generateplaylist(_playlistpath_) and _swango_.generateepg(_epgdays_,_epgpath_):
                    result=1
            else:
                token=_token=_swango_.pairingdevice()
                if _swango_.logdevicestartup() ==True:
                    self._addon.setSetting("device_token",token)
                    if _swango_.generateplaylist(_playlistpath_) and _swango_.generateepg(_epgdays_,_epgpath_):
                        result=1  
        except swango.ToManyDeviceError():
            self.notify("To many device in SWAN Go service registered",True)
        except swango.PairingError():
            self.notify("Pairing device error",True)
        except swango.AuthenticationError():
            self.notify("Authentication error. Check Username and password in settings",True)

        self.log('Update playlist and epg ended')
        self.notify("Playlist and EPG xml successfully updated -service",False)
        return result

    def tick(self):
        if datetime.datetime.now() > self._next_update:
            try:
                self.schedule_next(12 * 60 * 60)
                self.update()
            except requests.exceptions.ConnectionError:
                self.schedule_next(60)
                self.log('Can''t update, no internet connection')
                pass
            except swango.SwangoException as e:
                self.notify("Unexpected error", True)

    def save(self):
        self._addon.setSetting('next_update', str(time.mktime(self._next_update.timetuple())))
        self.log('Saving next update %s' % self._next_update)


if __name__ == '__main__':
    monitor = swangoMonitor()
    while not monitor.abortRequested():
        if monitor.waitForAbort(10):
            monitor.save()
            break
        monitor.tick()
