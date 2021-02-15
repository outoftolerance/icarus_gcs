from PyQt5 import Qt, QtCore
import json

class MapWrapper(Qt.QObject):
    @QtCore.pyqtSlot(result=str)
    def get_config(self):
        return json.dumps(self._config)

    def __init__(self, webengine, config):
        super(MapWrapper, self).__init__()

        self._webengine = webengine
        self._config = config

    def map_center_update(self, center):
        self._webengine.page().runJavaScript("mapCenterUpdate(" + json.dumps(center) + ")")

    def device_update(self, devices):
        self._webengine.page().runJavaScript("icarusDeviceUpdate(" + json.dumps(devices) + ")")

    def trail_update(self, trails):
        self._webengine.page().runJavaScript("icarusTrailUpdate(" + json.dumps(trails) + ")")

    def event_marker_add(self, event):
        self._webengine.page().runJavaScript("icarusEventMarkerAdd(" + json.dumps(event) + ")")
