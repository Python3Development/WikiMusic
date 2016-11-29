import os
import sys
from queue import Queue
from time import time
from PyQt5 import QtCore, QtWidgets
from wikimusic import resources, util, view, model, dialog, thread


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

    def __menu(self):
        # Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.setFont(util.font(size=7))

        # Menu Bar
        menu_bar = self.menuBar()

        # Menu Actions
        action_import = QtWidgets.QAction(util.icon('folder.png'), '&Import', self)
        action_import.setShortcut('Ctrl+I')
        action_import.triggered.connect(lambda: self.__import(QtWidgets.QFileDialog.getExistingDirectory(parent=self)))

        action_quit = QtWidgets.QAction(util.icon('close.png'), '&Exit', self)
        action_quit.setShortcut('Shift+F4')
        action_quit.triggered.connect(QtWidgets.qApp.quit)

        # Menu
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(action_import)
        file_menu.addAction(action_import)
        file_menu.addSeparator()
        file_menu.addAction(action_quit)

        # menu_bar.addAction('DEBUG', lambda: self.__import("C:\\Users\\Maikel\\Documents\\GitHub\\WikiMusic\\test\\data\\Music"))

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
        self.save_button.setDisabled(True)
        action_layout.addWidget(self.save_button)

        # Root Layout
        root_layout = QtWidgets.QVBoxLayout(parent)
        root_layout.addWidget(self.list_view)
        root_layout.addWidget(self.progress_bar)
        root_layout.addLayout(action_layout)
    # endregion

    # region Content Methods
    def __import(self, d):
        if d and os.path.exists(d) and not self.is_running:
            self.dir = d
            self.mp3_files = util.extract_mp3(d)
            if self.mp3_files:
                self.__populate()
            else:
                dialog.alert(self, 'Not found', 'No MP3 files found')

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
    def __handle_progress_update(self, value):
        self.progress_bar.setValue(self.progress_bar.value() + value)
    # endregion

    # region Script
    def __execute(self, items):
        if items and not self.is_running:
            self.status_bar.showMessage('Collecting data')
            self.start = time()
            self.is_running = True
            self.tasks = len(items)
            self.progress_bar.setValue(0)
            self.progress_bar.setRange(0, self.tasks * 4)

            for t in self.threads:
                if not t.isRunning():
                    t.q = self.q
                    t.collected.connect(self.__finish_collect)
                    t.progress_update.connect(self.__handle_progress_update)
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
            self.status_bar.showMessage('Done in {:.2f}s'.format(time() - self.start))

    def __save(self, items):
        saved = 0
        for item in items:
            if item.model.save():
                saved += 1
        if saved > 0:
            self.status_bar.showMessage('{} item(s) saved successfully, {} failed'.format(saved, len(items) - saved))
    # endregion

    pass

# region Exception Hook
# Back up the reference to the exceptionhook
sys._excepthook = sys.excepthook

def my_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)

# Set the exception hook to our wrapping function
sys.excepthook = my_exception_hook
# endregion


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()
    try:
        sys.exit(app.exec_())
    except:
        pass