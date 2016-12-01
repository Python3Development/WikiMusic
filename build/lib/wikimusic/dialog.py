from PyQt5 import QtGui, QtWidgets, QtCore
from wikimusic import network


class ProgressDialog(QtWidgets.QProgressDialog):
    # TODO handle cancel

    def __init__(self, title, range_=0, parent=None):
        super().__init__(parent)
        self.__layout()
        self.range = range_
        self.setFixedSize(360, 90)
        self.setWindowTitle(title)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

    # region Setup
    def __layout(self):
        self.label = QtWidgets.QLabel(self)
        self.setLabel(self.label)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setAlignment(QtCore.Qt.AlignCenter)
        self.setBar(self.progress_bar)

    # endregion

    # region Properties
    @property
    def range(self):
        return self.maximum()

    @range.setter
    def range(self, value):
        self.setRange(0, value)
        self.setValue(0)

    # endregion

    # region Methods
    def increment(self):
        self.setValue(self.value() + 1)

    # endregion
    pass


class UrlImageDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cover = None
        self.__layout()
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Popup)
        self.setFixedSize(200, 20)

    def __layout(self):
        self.url_input = QtWidgets.QLineEdit(self)
        self.url_input.setFixedSize(200, 20)
        self.url_input.editingFinished.connect(self.__handle_edit_finished)

    def __handle_edit_finished(self):
        url = self.url_input.text()
        if url:
            self.cover = network.download_cover(url)
        self.accept()

    def showEvent(self, event):
        self.url_input.setFocus()
        geom = self.frameGeometry()
        geom.moveBottomLeft(QtGui.QCursor.pos())
        self.setGeometry(geom)
        super().showEvent(event)


def alert(parent, title, message):
    QtWidgets.QMessageBox.warning(parent, title, message)
