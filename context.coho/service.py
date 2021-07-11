# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon

properties = [
    "context.coho.quickResume",
    "context.coho.shuffle",
    "context.coho.playFromRandomPoint",
    "context.coho.rescrape",
    "context.coho.sourceSelect",
    "context.coho.findSimilar",
    "context.coho.browseShow",
    "context.coho.browseSeason",
    "context.coho.traktManager",
]


class PropertiesUpdater(xbmc.Monitor):
    def __init__(self):
        super(PropertiesUpdater, self).__init__()
        self.addon = xbmcaddon.Addon()
        self._update_window_properties()

    def __del__(self):
        del self.addon

    def onSettingsChanged(self):
        self._update_window_properties()

    def _update_window_properties(self):
        for prop in properties:
            setting = self.addon.getSetting(prop)
            if setting == "false":
                xbmc.executebuiltin("SetProperty({},{},home)".format(prop, setting))
            else:
                xbmc.executebuiltin("ClearProperty({},home)".format(prop))
            xbmc.log(
                "Context menu item {}: {}".format(
                    "disabled" if setting == "false" else "enabled", prop
                )
            )


xbmc.log("context.coho service: starting", xbmc.LOGINFO)

try:
    # start monitoring settings changes events
    properties_monitor = PropertiesUpdater()

    # wait until abort is requested
    properties_monitor.waitForAbort()
except Exception as e:
    xbmc.log("context.coho service: error - {}".format(e), xbmc.LOGERROR)
finally:
    del properties_monitor

xbmc.log("context.coho service: stopped", xbmc.LOGINFO)
