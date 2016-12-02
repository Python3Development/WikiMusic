DEBUG = False


def enable():
    global DEBUG
    DEBUG = True


def log(text):
    if DEBUG:
        print(text)
