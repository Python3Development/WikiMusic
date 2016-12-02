import urllib.request
import urllib.error
import urllib.parse
import warnings
import wikipedia
from bs4 import BeautifulSoup
from wikimusic import model, util, debug

# Suppress warnings that come with wikipedia library
warnings.filterwarnings("ignore")

THRESHOLD = 0.75


def request_wiki_page(title):
    try:
        return [wikipedia.page(title=title)]
    except wikipedia.exceptions.DisambiguationError as e:
        return e.options
    except wikipedia.exceptions.PageError:
        return


def similarity_threshold_filter(options, find):
    debug.log('\n#### FILTER ####\n')
    for o in options:
        c = util.parenthesis_content(o)
        if c:
            debug.log('{} --> {}'.format(o, c))
            for s in c.split(' '):
                r = util.similarity(s, find)
                debug.log('  {}: {:.2f}'.format(s, r))
                if r >= THRESHOLD:
                    try:
                        return wikipedia.page(title=o.translate({ord(i): None for i in '"?!'}))
                    except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
                        debug.log("[EXCEPTION] Filtered page ({})".format(o))
                        return


def perfect_match_filter(options, find):
    matches = [o for o in options if find in o]
    if len(matches) == 1:
        try:
            return wikipedia.page(title=matches[0].translate({ord(i): None for i in '"?!'}))
        except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
            debug.log("[EXCEPTION] Filtered page ({})".format(matches[0]))
            return


def scrape_metadata(song, wikipage):
    html = wikipage.html()
    soup = BeautifulSoup(html, 'html.parser')

    table = soup.find('table', 'infobox vevent')
    if not table:
        # Wrong page
        return False

    found = 0
    rows = table.findAll('tr')
    for row in rows:
        if found == 3:
            break
        header = row.find('th')
        if header:
            if 'album' in header.text:
                found += 1
                i = row.find('i')
                if i:
                    a = i.find('a')
                    if a:
                        song.album = a.text
                    elif i.text:
                        song.album = i.text
            elif header.text == 'Released':
                found += 1
                data = row.find('td')
                if data:
                    song.release = util.extract_year(data.text)
            elif header.text == 'Genre':
                found += 1
                data = row.find('td')
                if data:
                    song.genres = util.clean_genres([a.text for a in data.findAll('a')])

    img = table.find('img')
    if img:
        song.cover = download_cover('https:{}'.format(img.get('src')))

    return True


def download_cover(url):
    response = http_request(url)
    if response:
        mime = response.info().get('Content-Type')
        if 'image' in mime:
            return model.Cover(response.read(), mime)


# region Helper
def http_request(request):
    try:
        return urllib.request.urlopen(request)
    except ValueError:
        pass
    except urllib.error.URLError as e:
        print(e)


def build_request(url, headers=None):
    return urllib.request.Request(url=url, headers=headers)

# endregion
