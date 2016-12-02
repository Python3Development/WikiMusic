import os
import sys
from queue import Queue
from time import time
from PyQt5 import QtCore, QtWidgets
from wikimusic import resources, util, view, model, dialog, thread, debug, async

# debug.enable()


class Window(QtWidgets.QMainWindow):
    q = Queue()
    threads = [thread.CollectorThread() for _ in range(10)]

    def __init__(self):
        super().__init__()
        self.__setup()
        self.__menu()
        self.__layout()
        self.setWindowTitle('WikiMusic')
        self.setWindowIcon(util.icon('app.png'))
        self.resize(800, 600)

    # region Setup
    def __setup(self):
        self.tasks = 0
        self.is_running = False
        self.start = None
        self.dir = None
        self.mp3_files = None

        self.t = QtCore.QThread()
        self.writer = async.Writer()
        self.t.started.connect(self.writer.write)
        self.writer.moveToThread(self.t)
        self.writer.update.connect(lambda: self.__handle_progress_update(1))
        self.writer.finished.connect(self.__handle_write_complete)

    def __menu(self):
        # Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.setFont(util.font(size=7))

        # Menu Bar
        menu_bar = self.menuBar()

        # Menu Actions
        action_import = QtWidgets.QAction(util.icon('file.png'), '&Import Files', self)
        action_import.setShortcut('Ctrl+I')
        action_import.triggered.connect(self.__handle_import)

        action_import_folder = QtWidgets.QAction(util.icon('folder.png'), '&Import Folder', self)
        action_import_folder.setShortcut('Ctrl+Shift+I')
        action_import_folder.triggered.connect(self.__handle_import_folder)

        action_quit = QtWidgets.QAction(util.icon('close.png'), '&Exit', self)
        action_quit.setShortcut('Shift+F4')
        action_quit.triggered.connect(QtWidgets.qApp.quit)

        # Menu
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(action_import)
        file_menu.addAction(action_import_folder)
        file_menu.addSeparator()
        file_menu.addAction(action_quit)

        # NOTE Debug
        if debug.DEBUG:
            menu_bar.addAction('1', lambda: self.__import_folder(
                "C:\\Users\\Maikel\\Documents\\GitHub\\WikiMusic\\test\\data\\Music_1"))
            menu_bar.addAction('10', lambda: self.__import_folder(
                "C:\\Users\\Maikel\\Documents\\GitHub\\WikiMusic\\test\\data\\Music_10"))
            menu_bar.addAction('50', lambda: self.__import_folder(
                "C:\\Users\\Maikel\\Documents\\GitHub\\WikiMusic\\test\\data\\Music_50"))

    def __layout(self):
        parent = QtWidgets.QWidget(self)
        self.setCentralWidget(parent)

        # List
        self.list_view = view.MetaMusicListView(parent)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(QtCore.Qt.AlignCenter)

        # Buttons
        action_layout = QtWidgets.QHBoxLayout()
        action_layout.addSpacerItem(util.spacer())
        collect_button = QtWidgets.QPushButton('Collect All', parent)
        collect_button.clicked.connect(lambda: self.__execute(self.list_view.selection))
        action_layout.addWidget(collect_button)
        self.save_button = QtWidgets.QPushButton('Save', parent)
        self.save_button.clicked.connect(lambda: self.__save(self.list_view.selection))
        action_layout.addWidget(self.save_button)

        # Root Layout
        root_layout = QtWidgets.QVBoxLayout(parent)
        root_layout.addWidget(self.list_view)
        root_layout.addWidget(self.progress_bar)
        root_layout.addLayout(action_layout)

    # endregion

    # region Content Methods
    def __import_folder(self, d):
        if d and os.path.exists(d) and not self.is_running:
            self.dir = d
            self.mp3_files = util.extract_mp3(d)
            if self.mp3_files:
                self.__populate()
            else:
                dialog.alert(self, 'Not found', 'No MP3 files found')

    def __import(self, files):
        if files:
            self.mp3_files = files
            self.__populate()

    def __populate(self):
        self.list_view.clear()
        d = dialog.ProgressDialog(parent=self, title='Importing', range_=len(self.mp3_files))
        for mp3 in self.mp3_files:
            d.setLabelText(os.path.basename(mp3))
            self.list_view.add(model.Song(mp3))
            d.increment()
        self.status_bar.showMessage('Loaded {} item(s)'.format(len(self.mp3_files)))

    # endregion

    # region Handlers
    def __handle_import(self):
        files_filter = QtWidgets.QFileDialog.getOpenFileNames(parent=self, filter='Audio (*.mp3)')
        self.__import(files_filter[0])

    def __handle_import_folder(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(parent=self)
        self.__import_folder(d)

    def __handle_progress_update(self, value):
        self.progress_bar.setValue(self.progress_bar.value() + value)

    def __handle_status_update(self, item, status):
        item.update_status(status)

    def __handle_write_complete(self, write_count, fail_count, runtime):
        self.t.quit()
        self.status_bar.showMessage(
            '{} item(s) saved successfully, {} failed ({:.2f}s)'.format(write_count, fail_count, runtime))
    # endregion

    # region Script
    def __execute(self, items):
        if items and not self.is_running:
            self.status_bar.showMessage('Collecting data')
            self.start = time()
            self.is_running = True
            self.tasks = len(items)
            self.save_button.setDisabled(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setRange(0, self.tasks * thread.CollectorThread.MAX)

            for t in self.threads:
                if not t.isRunning():
                    t.q = self.q
                    t.collected.connect(self.__finish_collect)
                    t.status_update.connect(self.__handle_status_update)
                    t.global_progress_update.connect(self.__handle_progress_update)
                    t.daemon = True
                    t.start()

            for item in items:
                self.q.put(item)

    def __finish_collect(self, item, collected):
        self.tasks -= 1
        if collected:
            item.update()
        if self.tasks == 0:
            self.is_running = False
            self.save_button.setDisabled(False)
            self.status_bar.showMessage('Done in {:.2f}s'.format(time() - self.start))

    def __save(self, items):
        if not self.is_running and not self.t.isRunning():
            self.progress_bar.setValue(0)
            self.progress_bar.setRange(0, len(items))
            self.writer.items = [i.model for i in items]
            self.t.start()
    # endregion

    pass


# region Exception Hook
sys._hook = sys.excepthook

def hook(exctype, value, traceback):
    print(exctype, value, traceback)
    sys._hook(exctype, value, traceback)
    sys.exit(1)

sys.excepthook = hook
# endregion


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()
    try:
        sys.exit(app.exec_())
    except:
        pass
