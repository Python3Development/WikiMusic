import os
import glob
import base64
import re

from PyQt5 import QtWidgets, QtGui, QtCore


# Image
def icon(name):
    return QtGui.QIcon(':/img/{}'.format(name))


def image(name):
    return QtGui.QPixmap(':/img/{}'.format(name))


def byte_image(data):
    img = QtGui.QPixmap()
    if img.loadFromData(data):
        return img


def base64_byte_image(data):
    return bytes(base64.b64encode(data)).decode()


# File
def file_exists(file):
    return file and os.path.exists(file)


def file_name(file):
    return os.path.splitext(os.path.basename(file))[0]


def extract_mp3(path):
    os.chdir(path)
    return glob.glob("*.mp3")


# String
def extract_artist_title(file):
    return [s.strip() for s in file_name(file).split(' - ')]


def clean_genres(genres):
    return [g.title() for g in genres if not re.match(r'\[[^)]*\]', g)]


def extract_year(data):
    return re.findall(r'\d{4}', data)[0]


def is_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


# Font
def font(size=None, bold=False):
    f = QtGui.QFont()
    if size:
        f.setPointSize(size)
    f.setBold(bold)
    return f


# GUI
def spacer():
    return QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)


