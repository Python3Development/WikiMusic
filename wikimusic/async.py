from PyQt5 import QtCore
from time import time
from wikimusic import network


class Downloader(QtCore.QObject):
    finished = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.url = None
        self.cover = None

    def download(self):
        if self.url:
            self.cover = network.download_cover(self.url)
        self.finished.emit()
