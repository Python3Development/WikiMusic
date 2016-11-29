import os
from PyQt5 import QtGui

from PyQt5 import QtWidgets, QtCore

from wikimusic import dialog
from wikimusic import network
from wikimusic import util


class MetaMusicListView(QtWidgets.QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = list()
        self.__layout()
        self.setWidgetResizable(True)

    # region Setup
    def __layout(self):
        parent = QtWidgets.QWidget(self)
        parent.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.setWidget(parent)
        self.list = QtWidgets.QVBoxLayout(parent)

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
        self.items.append(view)
        self.list.addWidget(view)

    def clear(self):
        self.items.clear()
        self.__layout()

    # endregion

    # region Helpers
    def __line(self):
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.list.addWidget(line)

    # endregion
    pass


class MetaMusicListItem(QtWidgets.QWidget):
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

        grid_layout = QtWidgets.QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        self.frame.setLayout(grid_layout)

        # Image
        self.cover_label = QtWidgets.QLabel(self)
        self.cover_label.setFixedSize(80, 80)
        self.cover_label.setScaledContents(True)
        self.cover_label.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.cover_label.customContextMenuRequested.connect(self.__handle_cover_context_menu)
        grid_layout.addWidget(self.cover_label, 0, 0, 3, 1)

        # Info
        self.artist_input = QtWidgets.QLineEdit(self)
        self.artist_input.setFixedWidth(200)
        self.artist_input.editingFinished.connect(self.__handle_artist_input_finished)
        grid_layout.addWidget(self.artist_input, 0, 1)

        separator = QtWidgets.QLabel('-', self)
        separator.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        grid_layout.addWidget(separator, 0, 2)

        self.title_input = QtWidgets.QLineEdit(self)
        self.title_input.setFixedWidth(200)
        self.title_input.editingFinished.connect(self.__handle_title_input_finished)
        grid_layout.addWidget(self.title_input, 0, 3)

        self.genre_input = QtWidgets.QLineEdit(self)
        self.genre_input.setFixedWidth(150)
        self.genre_input.editingFinished.connect(self.__handle_genre_input_finished)
        grid_layout.addWidget(self.genre_input, 1, 1)

        self.year_input = QtWidgets.QLineEdit(self)
        self.year_input.setFixedWidth(30)
        self.year_input.editingFinished.connect(self.__handle_year_input_finished)
        grid_layout.addWidget(self.year_input, 2, 1)

        layout.addWidget(self.frame)

    def __setup(self):
        if self.__model:
            self.checkbox_file.setText(os.path.basename(self.__model.file))
            m, s = divmod(self.__model.length, 60)
            self.time_label.setText('({:.0f}:{:02.0f})'.format(m, s))

            if self.__model.cover:
                self.cover_label.setPixmap(util.byte_image(self.__model.cover.data))
                self.cover_label.setToolTip('<img src="data:image/png;base64,{}">'
                                            .format(util.base64_byte_image(self.__model.cover.data)))
            else:
                self.cover_label.setPixmap(util.image('cover.png'))

            self.__default_line_edit(self.artist_input, self.__model.artist or 'Artist')
            self.__default_line_edit(self.title_input, self.__model.title or 'Title')
            self.__default_line_edit(self.genre_input, self.__model.genres or 'Genre')
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
    # endregion

    # region Helper
    def __populate(self):
        if self.__model:
            self.__load_cover(self.__model.cover)
            self.artist_input.setText(self.__model.artist)
            self.title_input.setText(self.__model.title)
            self.genre_input.setText(', '.join(self.__model.genres) if self.__model.genres else None)
            self.year_input.setText(self.__model.release)

    def __load_cover(self, cover):
        if cover:
            self.cover_label.setPixmap(util.byte_image(self.__model.cover.data))
            self.cover_label.setToolTip('<img src="data:image/png;base64,{}">'
                                        .format(util.base64_byte_image(self.__model.cover.data)))
        else:
            self.cover_label.setPixmap(util.image('cover.png'))

    def __default_line_edit(self, line_edit, value):
        line_edit.setPlaceholderText(value)
        line_edit.setToolTip(value)

    # endregion

    # region Handlers
    def __handle_cover_context_menu(self, point):
        menu = QtWidgets.QMenu()
        menu.addAction('Set', self.__handle_show_input_popup)
        if self.__model.cover:
            menu.addAction('Clear', self.__handle_clear_cover)
        menu.exec_(self.mapToGlobal(point))

    def __handle_show_input_popup(self):
        d = dialog.UrlImageDialog()
        if d.exec_():
            if d.cover:
                self.__model.cover = d.cover
                self.__load_cover(d.cover)

    def __handle_clear_cover(self):
        self.__model.cover = None
        self.__load_cover(None)

    def __handle_checkbox_state_change(self, state):
        self.frame.setHidden(state == QtCore.Qt.Unchecked)

    def __handle_artist_input_finished(self):
        self.__model.artist = self.artist_input.text()

    def __handle_title_input_finished(self):
        self.__model.title = self.title_input.text()

    def __handle_genre_input_finished(self):
        self.__model.genres = self.genre_input.text().split(', ') if self.genre_input.text() else None

    def __handle_year_input_finished(self):
        value = self.year_input.text()
        if len(value) == 4 and util.is_int(value):
            self.__model.release = value
        else:
            self.year_input.setText(self.__model.release)
    # endregion
    pass
