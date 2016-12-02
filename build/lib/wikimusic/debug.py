DEBUG = False


def enable(e):
    global DEBUG
    DEBUG = e


def log(text):
    if DEBUG:
        print(text)
