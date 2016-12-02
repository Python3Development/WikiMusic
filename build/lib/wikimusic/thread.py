from PyQt5 import QtCore
from wikimusic import network, view


class CollectorThread(QtCore.QThread):
    # region Constants
    MAX = 10
    # endregion

    # region Signals
    collected = QtCore.pyqtSignal(view.MetaMusicListItem, bool)
    status_update = QtCore.pyqtSignal(view.MetaMusicListItem, str)
    global_progress_update = QtCore.pyqtSignal(int)
    # endregion

    def __init__(self):
        super().__init__()
        self.q = None
        self.__i = 0

    def run(self):
        if self.q:
            while True:
                item = self.q.get()
                self.process(item)
                self.q.task_done()

    # region Main Execution
    def process(self, item):
        self.send(item, 'Page Request')
        complete = self.process_request(item)
        self.i = self.MAX/2
        if complete:
            self.i = self.MAX
            self.send(item, "<font color='green'>Success</font>")
            self.collected.emit(item, True)
            return

        self.send(item, 'Page Request')
        complete = self.process_request(item, True)
        self.i = self.MAX
        self.send(item, "<font color='green'>Success</font>" if complete else "<font color='red'>Failure</font>")
        self.collected.emit(item, complete)

    def process_request(self, item, fallback=False):
        song = item.model
        title = '{} ({})'.format(song.title, song.main_artist) if fallback else song.title
        pages = network.request_wiki_page(title)
        self.i += 1
        if pages:
            if len(pages) == 1:
                self.send(item, 'Scraping')
                scrape = network.scrape_metadata(song, pages[0])
                self.i += 1
                return scrape
            else:
                self.send(item, 'Filter (artist)')
                page = network.similarity_threshold_filter(pages, song.main_artist)
                self.i += 1
                if page:
                    self.send(item, 'Scraping')
                    scrape = network.scrape_metadata(song, page)
                    self.i += 1
                    if not scrape:
                        self.send(item, 'Filter (song)')
                        page = network.perfect_match_filter(pages, '(song)')
                        self.i += 1
                        if page:
                            self.send(item, 'Scraping')
                            scrape = network.scrape_metadata(song, page)
                            self.i += 1
                            return scrape
                    return scrape
                else:
                    self.send(item, 'Filter (song)')
                    page = network.perfect_match_filter(pages, '(song)')
                    self.i += 1
                    if page:
                        self.send(item, 'Scraping')
                        scrape = network.scrape_metadata(song, page)
                        self.i += 1
                        return scrape
        return False
    # endregion

    # region Properties
    @property
    def i(self):
        return self.__i

    @i.setter
    def i(self, value):
        self.global_progress_update.emit(value - self.__i)
        self.__i = value % self.MAX
    # endregion

    # region Helpers
    def send(self, item, status):
        self.status_update.emit(item, status)
    # endregion

    pass
