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


class Writer(QtCore.QObject):
    update = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal(int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = None

    def write(self):
        start = time()
        complete = 0
        for item in self.items:
            if item.save():
                complete += 1
            self.update.emit()
        self.finished.emit(complete, len(self.items) - complete, time() - start)
