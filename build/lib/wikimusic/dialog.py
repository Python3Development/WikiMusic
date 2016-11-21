from PyQt5 import QtWidgets, QtCore


class ProgressDialog(QtWidgets.QProgressDialog):
    #TODO handle cancel

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


def alert(parent, title, message):
    QtWidgets.QMessageBox.warning(parent, title, message)
