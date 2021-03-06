import os
import glob
import base64
import re
import difflib
from PyQt5 import QtCore

from PyQt5 import QtWidgets, QtGui


# Image
def icon(name):
    return QtGui.QIcon(':/img/{}'.format(name))


def image(name):
    return QtGui.QPixmap(':/img/{}'.format(name))


def byte_image(data):
    img = QtGui.QPixmap()
    if img.loadFromData(data):
        return img


def base64_encoded_bytes(data):
    return bytes(base64.b64encode(data)).decode()


def image_to_bytes(img):
    if img:
        arr = QtCore.QByteArray()
        buf = QtCore.QBuffer(arr)
        buf.open(QtCore.QIODevice.WriteOnly)
        img.save(buf, 'PNG')
        print(arr)
        return arr.data()

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
    match = re.findall(r'\d{4}', data)
    if len(match) > 0:
        return match[0]


def is_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def similarity(value, value2):
    return difflib.SequenceMatcher(lambda x: x == ' ', value, value2).ratio()


def parenthesis_content(s):
    match = re.search(r'\((.*)\)', s)
    return match.group(1) if match else None


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
