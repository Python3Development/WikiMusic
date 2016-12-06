import os
from PyQt5 import QtGui, QtWidgets, QtCore
from wikimusic import util, async


class VerticalLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(QtCore.Qt.AlignTop)
        self.setTextFormat(QtCore.Qt.RichText)
        self.setStyleSheet('color: gray;')

    @property
    def lines(self):
        return self.text()

    @lines.setter
    def lines(self, line):
        self.setText(line + '<br>')


class FloatingLineEdit(QtWidgets.QDialog):
    editingFinished = QtCore.pyqtSignal()

    def __init__(self, width=200, parent=None):
        super().__init__(parent)
        self.line_edit = QtWidgets.QLineEdit(self)
        self.line_edit.setFixedWidth(width)
        self.line_edit.returnPressed.connect(self.__handle_edit_finished)

        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Popup)
        self.setFixedSize(width, 20)

    def showEvent(self, event):
        self.line_edit.setFocus()
        geom = self.frameGeometry()
        geom.moveBottomLeft(QtGui.QCursor.pos())
        self.setGeometry(geom)
        super().showEvent(event)

    def __handle_edit_finished(self):
        self.editingFinished.emit()
        self.text = None
        self.accept()

    @property
    def text(self):
        return self.line_edit.text()

    @text.setter
    def text(self, value):
        self.line_edit.setText(value)


class CoverLabel(QtWidgets.QLabel):
    editingFinished = QtCore.pyqtSignal()

    def __init__(self, size, cover=None, parent=None):
        super().__init__(parent)
        self.__cover = cover
        self.__menu()
        self.__setup()
        self.setFixedSize(size, size)
        self.setScaledContents(True)
        self.setCover(cover)

    def __menu(self):
        self.menu = QtWidgets.QMenu(self)
        self.menu.addAction('New', lambda: self.floating_line_edit.show())
        self.menu.addAction('Clear', lambda: self.__handle_set_cover(None))

    def __setup(self):
        self.t = QtCore.QThread()
        self.downloader = async.Downloader()
        self.t.started.connect(self.downloader.download)
        self.downloader.moveToThread(self.t)
        self.downloader.finished.connect(self.__handle_download_complete)

        self.floating_line_edit = FloatingLineEdit(parent=self)
        self.floating_line_edit.editingFinished.connect(self.__handle_download_image)

    def contextMenuEvent(self, event):
        self.menu.exec_(self.mapToGlobal(event.pos()))

    def setCover(self, cover):
        self.__cover = cover
        if cover:
            self.setPixmap(util.byte_image(cover.data))
            self.setToolTip('<img src="data:image/png;base64,{}">'.format(util.base64_byte_image(cover.data)))
        else:
            self.setPixmap(util.image('cover.png'))

    def cover(self):
        return self.__cover

    def __handle_download_image(self):
        self.downloader.url = self.floating_line_edit.text
        if not self.t.isRunning():
            self.t.start()
        else:
            print('Running')

    def __handle_download_complete(self):
        self.t.quit()
        cover = self.downloader.cover
        if cover:
            self.__handle_set_cover(cover)

    def __handle_set_cover(self, cover):
        self.setCover(cover)
        self.editingFinished.emit()


class MetaMusicListView(QtWidgets.QScrollArea):
    selectionChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = list()
        self.__selected = 0
        self.__layout()
        self.setWidgetResizable(True)

    # region Setup
    def __layout(self):
        w = QtWidgets.QWidget(self)
        w.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.setWidget(w)
        self.list = QtWidgets.QVBoxLayout(w)

    # endregion

    # region Properties
    @property
    def selection(self):
        return [item for item in self.items if item.checked]

    # endregion

    # region Methods
    def add(self, item):
        if self.items:
            self.__line()
        view = MetaMusicListItem(item)
        view.selected.connect(self.__handle_selection_change)
        self.items.append(view)
        self.list.addWidget(view)
        self.__selected += 1

    def clear(self):
        self.items.clear()
        self.__selected = 0
        self.__layout()

    # endregion

    def __handle_selection_change(self, selected):
        if selected:
            self.__selected += 1
        else:
            self.__selected -= 1
        self.selectionChanged.emit(self.__selected)

    # region Helpers
    def __line(self):
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.list.addWidget(line)

    # endregion
    pass


class MetaMusicListItem(QtWidgets.QWidget):
    selected = QtCore.pyqtSignal(bool)

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.__model = model
        self.__layout()
        self.__setup()

    # region Setup
    def __layout(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 6)

        # Header (Checkbox, Filename, Time)
        header_layout = QtWidgets.QHBoxLayout()

        self.checkbox_file = QtWidgets.QCheckBox(self)
        self.checkbox_file.setFont(util.font(bold=True))
        self.checkbox_file.setChecked(True)
        self.checkbox_file.stateChanged.connect(self.__handle_checkbox_state_change)
        header_layout.addWidget(self.checkbox_file, alignment=QtCore.Qt.AlignVCenter)

        self.time_label = QtWidgets.QLabel(self)
        header_layout.addWidget(self.time_label, alignment=QtCore.Qt.AlignVCenter)

        header_layout.addSpacerItem(util.spacer())

        layout.addLayout(header_layout)

        # Content (Image / Artist - Title, Genre, Year)
        self.frame = QtWidgets.QFrame(self)
        self.frame.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        grid_layout = QtWidgets.QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        self.frame.setLayout(grid_layout)

        # Image
        self.cover_label = CoverLabel(size=100, parent=self)
        self.cover_label.editingFinished.connect(self.__handle_cover_edit_finished)
        grid_layout.addWidget(self.cover_label, 0, 0, 4, 1)

        # Info
        self.title_input = QtWidgets.QLineEdit(self)
        self.title_input.setFixedWidth(250)
        self.title_input.editingFinished.connect(self.__handle_title_edit_finished)
        grid_layout.addWidget(self.title_input, 0, 1, 1, 2)

        self.artist_input = QtWidgets.QLineEdit(self)
        self.artist_input.setFixedWidth(250)
        self.artist_input.editingFinished.connect(self.__handle_artist_edit_finished)
        grid_layout.addWidget(self.artist_input, 1, 1, 1, 2)

        self.album_input = QtWidgets.QLineEdit(self)
        self.album_input.setFixedWidth(250 - 30 - grid_layout.spacing())
        self.album_input.editingFinished.connect(self.__handle_album_edit_finished)
        grid_layout.addWidget(self.album_input, 2, 1)

        self.year_input = QtWidgets.QLineEdit(self)
        self.year_input.setFixedWidth(30)
        self.year_input.editingFinished.connect(self.__handle_year_edit_finished)
        grid_layout.addWidget(self.year_input, 2, 2)

        self.genre_input = QtWidgets.QLineEdit(self)
        self.genre_input.setFixedWidth(250)
        self.genre_input.editingFinished.connect(self.__handle_genre_edit_finished)
        grid_layout.addWidget(self.genre_input, 3, 1, 1, 2)

        # Status
        self.status_label = VerticalLabel(self)
        self.status_label.setFixedSize(75, 100)
        grid_layout.addWidget(self.status_label, 0, 3, 4, 1)

        layout.addWidget(self.frame)

    def __setup(self):
        if self.__model:
            self.checkbox_file.setText(os.path.basename(self.__model.file).replace('&', '&&'))
            m, s = divmod(self.__model.length, 60)
            self.time_label.setText('({:.0f}:{:02.0f})'.format(m, s))
            self.cover_label.setCover(self.__model.cover)
            self.__default_line_edit(self.artist_input, self.__model.artist or 'Artist')
            self.__default_line_edit(self.title_input, self.__model.title or 'Title')
            self.__default_line_edit(self.album_input, self.__model.album or 'Album')
            self.__default_line_edit(self.genre_input,
                                     ', '.join(self.__model.genres) if self.__model.genres else 'Genre')
            self.__default_line_edit(self.year_input, self.__model.release or 'Year')

            if not self.__model.artist or not self.__model.title:
                artist_title = util.extract_artist_title(self.__model.file)
                self.__model.artist = artist_title[0]
                self.artist_input.setText(self.__model.artist)
                if len(artist_title) > 1:
                    self.__model.title = artist_title[1]
                    self.title_input.setText(self.__model.title)

    # endregion

    # region Properties
    @property
    def model(self):
        return self.__model

    @model.setter
    def model(self, value):
        self.__model = value
        self.__populate()

    @property
    def checked(self):
        return self.checkbox_file.isChecked()

    # endregion

    # region Methods
    def update(self):
        self.__populate()

    def update_status(self, status):
        self.status_label.lines += status

    # endregion

    # region Helper
    def __populate(self):
        if self.__model:
            self.cover_label.setCover(self.__model.cover)
            self.artist_input.setText(self.__model.artist)
            self.title_input.setText(self.__model.title)
            self.album_input.setText(self.__model.album)
            self.genre_input.setText(', '.join(self.__model.genres) if self.__model.genres else None)
            self.year_input.setText(self.__model.release)

    def __default_line_edit(self, line_edit, value):
        line_edit.setPlaceholderText(value)
        line_edit.setToolTip(value)

    # endregion

    # region Handlers
    def __handle_checkbox_state_change(self, state):
        checked = state == QtCore.Qt.Checked
        self.frame.setHidden(not checked)
        self.selected.emit(checked)

    def __handle_cover_edit_finished(self):
        self.__model.cover = self.cover_label.cover()

    def __handle_artist_edit_finished(self):
        self.__model.artist = self.artist_input.text()

    def __handle_title_edit_finished(self):
        self.__model.title = self.title_input.text()

    def __handle_album_edit_finished(self):
        self.__model.album = self.album_input.text()

    def __handle_genre_edit_finished(self):
        self.__model.genres = self.genre_input.text().split(', ') if self.genre_input.text() else None

    def __handle_year_edit_finished(self):
        value = self.year_input.text()
        if len(value) == 4 and util.is_int(value):
            self.__model.release = value
        else:
            self.year_input.setText(None)

    # endregion
    pass
