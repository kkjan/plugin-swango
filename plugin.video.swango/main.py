import sys
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
from urlparse import urlparse
from urlparse import parse_qsl
from uuid import getnode as get_mac
import swango

params = False
_addon = xbmcaddon.Addon('plugin.video.swango')
_scriptname_=_addon.getAddonInfo('name')
# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])


_first_error_ = (_addon.getSetting('first_error') == "true")
_send_errors_ = (_addon.getSetting('send_errors') == "true")
_username_ = _addon.getSetting("username")
_password_ = _addon.getSetting("password")
_device_token_ = _addon.getSetting("device_token")
_device_type_code_ = _addon.getSetting("device_type_code")
_device_model_ = _addon.getSetting("device_model")
_device_name_ = _addon.getSetting("device_name")
_device_serial_number_ = _addon.getSetting("device_serial_number")
_epgdays_ = int(_addon.getSetting("epgdays"))
_epgpath_ = _addon.getSetting("epgpath")
_playlistpath_ = _addon.getSetting("playlistpath")


###############################################################################
#     Remote debbuging
###############################################################################
REMOTE_DBG = False
# append pydev remote debugger
if REMOTE_DBG:
    try:
        sys.path.append(os.environ['HOME']+r'/.xbmc/system/python/Lib/pysrc')
        sys.path.append(os.environ['APPDATA']+r'/Kodi/system/python/Lib/pysrc')
        import pydevd
        pydevd.settrace('libreelec.local', port=5678, stdoutToServer=True, stderrToServer=True)
    except ImportError:
        sys.stderr.write("Error: Could not load pysrc!")
        sys.exit(1)


###############################################################################


##############################################################################
#     First running
###############################################################################

# First run
if not (_addon.getSetting("settings_init_done") == 'true'):
    DEFAULT_SETTING_VALUES = { 'send_errors' : 'false' }
    for setting in DEFAULT_SETTING_VALUES.keys():
        val = _addon.getSetting(setting)
        if not val:
            _addon.setSetting(setting, DEFAULT_SETTING_VALUES[setting])
    _addon.setSetting("settings_init_done", "true")

###############################################################################




###############################################################################
# log settings
###############################################################################
def log(msg, level=xbmc.LOGDEBUG):
    if type(msg).__name__=='unicode':
        msg = msg.encode('utf-8')
    xbmc.log("[%s] %s"%(_scriptname_,msg.__str__()), level)

def logDbg(msg):
    log(msg,level=xbmc.LOGDEBUG)

def logErr(msg):
    log(msg,level=xbmc.LOGERROR)
###############################################################################

def notify(self, text, error=False):
    icon = 'DefaultIconError.png' if error else ''
    try:
        xbmc.executebuiltin('Notification("%s","%s",5000,%s)' % (self._addon.getAddonInfo('name').encode("utf-8"), text, icon))
    except NameError as e:
        xbmc.executebuiltin('Notification("%s","%s",5000,%s)' % (self._addon.getAddonInfo('name'), text, icon))


def reload_settings():
    #_addon.openSettings()
    try:
        global _first_error_
        _first_error_ = (_addon.getSetting('first_error') == "true")
        global _send_errors_
        _send_errors_ = (_addon.getSetting('send_errors') == "true")
        global _username_
        _username_ = _addon.getSetting("username")
        global _password_
        _password_ = _addon.getSetting("password")
        global _device_token_
        _device_token_ = _addon.getSetting("device_token")
        global _device_type_code_
        _device_type_code_ = _addon.getSetting("device_type_code")
        global _device_model_
        _device_model_ = _addon.getSetting("device_model")
        global _device_name_
        _device_name_ = _addon.getSetting("device_name")
        global _device_serial_number_
        _device_serial_number_ = _addon.getSetting("device_serial_number")
        global _epgdays_
        _epgdays_ = int(_addon.getSetting("epgdays"))
        global _epgpath_
        _epgpath_ = _addon.getSetting("epgpath")
        global _playlistpath_
        _playlistpath_ = _addon.getSetting("playlistpath")
        
        if _swango.logdevicestartup() ==True:
            _swango.generateplaylist(_playlistpath_)
            _swango.generateepg(_epgdays_,_epgpath_)
        else:
            token=_swango.pairingdevice()
            if _swango.logdevicestartup() ==True:  
                _addon.setSetting('device_token',token)
                _swango.generateplaylist(_playlistpath_)
                _swango.generateepg(_epgdays_,_epgpath_) 
        logDbg("Playlist and EPG Updated -main.py")

    except swango.ToManyDeviceError():
        notify("To many device in SWAN Go service registered",True)
    except swango.PairingError():
        notify("Pairing device error",True)
    except swango.AuthenticationError():
        notify("Authentication error. Check Username and password in settings",True)



def list_channels():
    xbmc.log("Reading channels ...", level=xbmc.LOGNOTICE)
    xbmcplugin.setPluginCategory(_handle, 'TV')
    xbmcplugin.setContent(_handle, 'videos')
    for channel in _swango.getchannels():
        list_item = xbmcgui.ListItem(label=channel['name'])
        list_item.setArt({'thumb': channel['tvg-logo'],
                        'icon': channel['tvg-logo']})
        list_item.setInfo('video', {'title': channel['name'],
                                    'genre': channel['name'],
                                    'mediatype': 'video'})
        url = '{0}?action=play&id={1}'.format(_url, channel['id_epg'])
        logDbg("list channels: "+url)
        list_item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def play_video(id):
    """
    Play a video by the provided path.
    :param path: Fully-qualified video URL
    :type path: str
    """
    # Create a playable item with a path to play.
    logDbg("play_video: "+str(id))
    url = _swango.get_stream(int(id))

    log('Playing channel ...')
    log(str(url))
    play_item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


    # based on example from https://forum.kodi.tv/showthread.php?tid=330507
    # play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
    # play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
    # play_item.setMimeType('application/dash+xml')
    # play_item.setContentLookup(False)

    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring
    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    log('Executing SWANGO plugin ...', level=xbmc.LOGNOTICE)
    params = dict(parse_qsl(paramstring))
    logDbg(paramstring)
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['id'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        #list_categories()
        #list_videos('Cars')
        list_channels()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring

    _swango=swango.SWANGO(_username_, _password_,_device_token_,_device_type_code_,_device_model_,_device_name_,_device_serial_number_)
    router(sys.argv[2][1:])

