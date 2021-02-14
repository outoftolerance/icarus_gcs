from PyQt5 import Qt, QtCore

class MapWrapper(Qt.QObject):
    @QtCore.pyqtSlot(result=list)
    def get_config(self):
        return self._config

    def __init__(self, config):
        super(MapWrapper, self).__init__()

        self._config = config