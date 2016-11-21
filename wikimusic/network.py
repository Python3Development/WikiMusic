import urllib.request
import urllib.error
import urllib.parse
import wikipedia
from bs4 import BeautifulSoup
from wikimusic import model, util


def request_wiki_page(song):
    try:
        return wikipedia.page(title=song.title)
    except wikipedia.exceptions.DisambiguationError as e:
        # Fallback 1: <title> (<artist>)
        fallback_1 = [s for s in e.options if song.main_artist in s]
        if len(fallback_1) == 1:
            extended_title = fallback_1[0].replace('\"', '')
            return wikipedia.page(extended_title)
        else:
            # Fallback 2: <title> (song)
            fallback_2 = [s for s in e.options if '(song)' in s]
            if len(fallback_2) == 1:
                extended_title = fallback_2[0].replace('\"', '')
                return wikipedia.page(extended_title)
    except wikipedia.exceptions.PageError:
        return


def request_wiki_page_extended(song):
    try:
        title = '{} ({})'.format(song.title, song.main_artist)
        return wikipedia.page(title=title)
    except wikipedia.exceptions.DisambiguationError as e:
        # Fallback : <title> (song)
        fallback = [s for s in e.options if '(song)' in s]
        if len(fallback) == 1:
            extended_title = fallback[0].replace('\"', '')
            return wikipedia.page(extended_title)
    except wikipedia.exceptions.PageError:
        return


def scrape_metadata(song, wikipage):
    html = wikipage.html()
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', 'infobox vevent')
    if not table:
        # Wrong page
        return False
    rows = table.findAll('tr')
    for row in rows:
        header = row.find('th')
        if header:
            if header.text == 'Released':
                data = row.find('td')
                if data:
                    song.release = util.extract_year(data.text)
            elif header.text == 'Genre':
                data = row.find('td')
                if data:
                    song.genres = util.clean_genres([a.text for a in data.findAll('a')])
    img = table.find('img')
    if img:
        img_url = 'https:{}'.format(img.get('src'))
        response = http_request(img_url)
        if response:
            song.cover = model.Cover(response.read(), response.info().get('Content-Type'))
    return True


# region Helper
def http_request(request):
    try:
        return urllib.request.urlopen(request)
    except urllib.error.URLError as e:
        print(e)


def build_request(url, headers=None):
    return urllib.request.Request(url=url, headers=headers)
# endregion
