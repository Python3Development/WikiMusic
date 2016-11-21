from PyQt5 import QtCore
from wikimusic import network, view


class CollectorThread(QtCore.QThread):
    collected = QtCore.pyqtSignal(view.MetaMusicListItem, bool)
    progress_update = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.q = None

    def run(self):
        if self.q:
            while True:
                item = self.q.get()
                self.__process(item)
                self.q.task_done()

    def __process(self, item):
        model = item.model
        page = network.request_wiki_page(model)
        if page:
            self.progress_update.emit(1)
            if not network.scrape_metadata(model, page):
                self.progress_update.emit(1)
                self.__reprocess(item)
            else:
                self.progress_update.emit(3)
                self.collected.emit(item, True)
        else:
            self.progress_update.emit(4)
            self.collected.emit(item, False)

    def __reprocess(self, item):
        model = item.model
        page = network.request_wiki_page_extended(model)
        if page:
            self.progress_update.emit(1)
            if not network.scrape_metadata(model, page):
                self.progress_update.emit(1)
                self.collected.emit(item, False)
            else:
                self.progress_update.emit(1)
                self.collected.emit(item, True)
        else:
            self.progress_update.emit(2)
            self.collected.emit(item, False)

