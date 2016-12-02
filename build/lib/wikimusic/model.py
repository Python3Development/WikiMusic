import mutagen
from mutagen import mp3, id3
from wikimusic import util


class Song(object):
    def __init__(self, file):
        self.file = file
        self.artist = None
        self.title = None
        self.album = None
        self.release = None
        self.genres = None
        self.cover = None
        self.length = None
        self.__audio = mutagen.mp3.MP3(file, v2_version=3)
        self.__setup()

    def __setup(self):
        self.length = self.__audio.info.length
        if self.__audio.tags:
            tit2_frames = self.__audio.tags.getall('TIT2')
            if tit2_frames:
                self.title = tit2_frames[0].text[0]
            tpe1_frames = self.__audio.tags.getall('TPE1')
            if tpe1_frames:
                self.artist = tpe1_frames[0].text[0]
            talb_frames = self.__audio.tags.getall('TALB')
            if talb_frames:
                self.album = talb_frames[0].text[0]
            tcon_frames = self.__audio.tags.getall('TCON')
            if tcon_frames:
                self.genres = tcon_frames[0].text[0].split(', ')
            tyer_frames = self.__audio.tags.getall('TYER')
            if tyer_frames:
                self.release = tyer_frames[0].text[0]
            apic_frames = self.__audio.tags.getall('APIC')
            if apic_frames:
                frame = apic_frames[0]
                self.cover = Cover(frame.data, frame.mime)

    @property
    def main_artist(self):
        return self.artist.split('ft.')[0].strip()

    def save(self):
        try:
            # Add ID3 if it doesn't exist
            if not self.__audio.tags:
                self.__audio.add_tags()
            # Add all metadata
            if self.title:
                tit2 = mutagen.id3.TIT2(text=self.title)
                self.__audio.tags.add(tit2)
            if self.artist:
                tpe1 = mutagen.id3.TPE1(text=self.artist)
                self.__audio.tags.add(tpe1)
            if self.album:
                talb = mutagen.id3.TALB(text=self.album)
                self.__audio.tags.add(talb)
            if self.genres:
                tcon = mutagen.id3.TCON()
                tcon.genres = self.genres
                self.__audio.tags.add(tcon)
            if self.release:
                tyer = mutagen.id3.TYER(text=self.release)
                self.__audio.tags.add(tyer)
            if self.cover:
                apic = mutagen.id3.APIC(mime=self.cover.mime, data=self.cover.data)
                self.__audio.tags.add(apic)
            # Save the mp3 file
            self.__audio.save(v2_version=3, v23_sep=', ')
            return True
        except mutagen.MutagenError:
            return False

    def verbose_print(self):
        print('*****\n' + self.__audio.pprint())


class Cover(object):
    def __init__(self, data, mime):
        self.data = data
        self.mime = mime
