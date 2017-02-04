#!/usr/bin/python3

import re
import logging
from PIL import Image

from bs4 import BeautifulSoup

import src.PluginBase as PluginBase
from src.MangaBase import Manga
from src.MangaBase import Chapter
from src.helper import memoized

# -------------------------------------------------------------------------------------------------
#  logging
# -------------------------------------------------------------------------------------------------

logger = logging.getLogger('MangaLoader.MangaFoxPlugin')

BASE_URL = 'http://mangafox.me/'
MANGA_LIST_URL = BASE_URL + 'manga/'

# -------------------------------------------------------------------------------------------------
#  Plugin class
# -------------------------------------------------------------------------------------------------
class MangaFoxPlugin(PluginBase.PluginBase):

    def __init__(self):
        self.__domain = BASE_URL
        self.__list_of_found_chapter_URLs = {}
        self.__last_found_image_URL = ''
    
    @memoized
    def get_manga_list(self):
        response = load_url(MANGA_LIST_URL)
        return self._parse_manga_list(response)
    
    def _parse_manga_list(self, data):
        doc = BeautifulSoup(data, 'html.parser')
        
        result = []
        for div in doc.find_all('div', class_='manga_list'):
            for li in div.find_all('li'):
                for a in li.find_all('a'):
                    if a.string and a['class'] != 'top':
                        manga = Manga(a.string)
                        manga.url = a['href']
                        result.append(manga)
        return result
    
    @memoized
    def load_chapter_list(self, manga):
        response = load_url(manga.url)
        for chapter in self._parse_chapter_list(response):
            manga.add_chapter(chapter)
    
    def _parse_chapter_list(self, data):
        doc = BeautifulSoup(data, 'html.parser')
        result = []
        for div in doc.find_all('div', id='chapters'):
            for ul in div.find_all('ul', class_='chlist'):
                for li in ul.find_all('li'):
                    inner_div = li.find('div')
                    a = inner_div.find('a', class_='tips')
                    span = inner_div.find('span', class_='title nowrap')
                    
                    words = a.string.split()
                    number_string = words[len(words)-1]
                    if number_string.isdigit(): # ignore 'half' chapters
                        chapter = Chapter(int(number_string))
                        chapter.url = a['href']
                        if span != None:
                            chapter.title = span.string
                        result.append(chapter)
        return result
    
    @memoized
    def load_image_list(self, chapter):
        response = load_url(chapter.url)
        for image in self._parse_image_list(chapter.url, response):
            chapter.add_image(image)
    
    def _parse_image_list(self, url, data):
        doc = BeautifulSoup(data, 'html.parser')
        result = []
        
        div = doc.find('div', class_='r m')
        
        options = []
        select = div.find('select', class_='m')
        for option in select.find_all():
            value = option['value']
            if value is not None and value.isdigit():
                options.append(int(value))#
        
        base_url = url.rsplit('/',1)[0] + '/'
        
        for option in options:
            if option > 0:
                image = Image(option)
                image.url = base_url + str(option) + '.html'
                result.append(image)
        
        return result
    
    @memoized
    def load_image_url(self, image):
        response = load_url(image.url)
        image.image_url = self._parse_image_url(response)
    
    def _parse_image_url(self, data):
        doc = BeautifulSoup(data, 'html.parser')
        
        #head = doc.head
        #meta = head.find('meta', property='og:image')
        #return meta['content']
        
        outer_div = doc.find('div', id='viewer')
        inner_div = outer_div.find('div', class_='read_img')
        img = inner_div.find('img', id='image')
        return img['src']
    
    
    ############# following are the old methods of this class ##################
    
    
    def getImage(self, image):
        """
        Gets the URL for an image by parsing the site. Does not download
        the image file itself!
        
        :param image: Image object containing a valid URL to the chapters
                      first page.
        """
        if image.chapter.chapterURL:
            chapterURL = image.chapter.chapterURL
        else:
            chapterURL = self.__find_URL_for_chapter(image.chapter)
        url = chapterURL.replace('1.html', '{}.html'.format(image.imageNo))

        if not url:
            logger.warning('Could not find wanted image. ')
            return False

        result = PluginBase.loadURL(url)
        if result is None:
            return False

        logger.debug('Start parsing...')
        soup = BeautifulSoup(result, 'html.parser')
        # TODO: Check whether to use find_all() instead of find().
        found_tag = soup.find('img', id='image')
        if found_tag == None:
            logger.info('No image found in MangaFox site, maybe the chapter is not available.')
            return False
        else:
            url = found_tag['src']

        # check if this time the same URL was found as last time, because
        # MangaFox shows last image of chapter when the given image number is
        # too high
        # TODO: Fix this by determine how many chapters there are!
        if self.__last_found_image_URL == url:
            return False

        image.imageUrl = url
        self.__last_found_image_URL = url
        logger.debug('URL for image found: {}'.format(url))
        return True

    def getListOfChapters(self, manga):
        """Gets list of all chapters currently available for a given manga.

        :param manga: describing the manga for which chapters should be found
                      including its name and the link of the main site
        :return: a list of chapters with all necessary information like their URLs
        """
        url = manga.mangaURL
        result = PluginBase.loadURL(url)
        #if result is None:
        #    return []
        logger.info('Looking for chapters of manga "{}" ({}).'.format(manga.name, manga.mangaURL))
        list_of_chapters = []
        soup = BeautifulSoup(result, 'html.parser')
        for ul in soup.findAll('ul', class_='chlist'):
            for a in ul.findAll('a', class_='tips'):
                link = a['href']
                text = a.get_text()
                try:
                    number = int(text.rsplit(None, 1)[-1])
                except ValueError:
                    logger.error('Could not parse chapter number!')
                    number = 0
                title_tag = a.find_next_sibling('span', class_='title')
                if title_tag:
                    title = title_tag.get_text()
                else:
                    title = ''
                # create Chapter object
                chapter = Chapter(manga.name, number)
                chapter.chapterURL = link
                chapter.text = text
                chapter.title = title
                list_of_chapters.append(chapter)
        logger.info('Found {} chapters.'.format(len(list_of_chapters)))
        return list_of_chapters

    @memoized
    def __find_URL_for_chapter(self, chapter):
        """Finds the base URL for a given chapter of a specific manga. The
        chapter and manga is descripted by the parameter "chapter". If it does
        not contain a valid URL for the manga itself it guesses based on the
        mangas name.

        :param chapter: object containing all available information about the
                        chapter and manga that should be found.
        :return: the URL of the first page of a given chapter
        """
        logger.debug('Looking for chapter URL...')
        # check if URL for manga was stored in chapter
        if not chapter.manga.mangaURL:
            # make a best guess for the URL of the given manga
            chapter.manga.mangaURL = 'http://mangafox.me/manga/' + self.__getInternalName(chapter.manga.name)
        found_chapter = None
        for x in self.getListOfChapters(chapter.manga):
            # look for chapter that has the same name as the wanted one
            if str(chapter) == str(x):
                found_chapter = x
                break
        if found_chapter == None:
            logger.debug('No chapter URL found!')
            return ''
        else:
            logger.debug('Found chapter URL: {}.'.format(found_chapter.chapterURL))
            return found_chapter.chapterURL

    def getListOfMangas(self):
        url = '/'.join((self.__domain, 'manga'))
        result = PluginBase.loadURL(url)
        #if result is None:
        #    return []
        print('Finding mangas...')
        logger.debug('Finding mangas...')
        
        # define function to classify if HTML tag contains a manga series
        def is_manga_tag(css_class):
            return css_class is not None and 'series_preview' in css_class
        
        list_of_all_mangas = []
        soup = BeautifulSoup(result, 'html.parser')
        for div in soup.findAll('div', class_='manga_list'):
            for a in div.findAll('a', class_=is_manga_tag):
                link = a['href']
                is_open = 'manga_open' in a['class']
                name = a.get_text()
                # create Manga object
                m = Manga(name)
                m.mangaURL = link
                m.is_open = is_open
                list_of_all_mangas.append(m)        
        print('Found {} mangas on site!'.format(len(list_of_all_mangas)))
        return list_of_all_mangas


    def postprocessImage(self, filename):
        logger.debug('Cropping image file to delete ads.')
        #image = Image.open(filename)
        #w, h = image.size
        #image.crop((0, 0, w, h-30)).save(filename)

    def __getInternalName(self, name):
        internalName = name
        internalName = str.lower(internalName)
        internalName = str.replace(internalName, ' ', '_')
        return internalName


# -------------------------------------------------------------------------------------------------
#  <module>
# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    plugin = MangaFoxPlugin()
    
    print('testing MangaFoxPlugin._parse_manga_list()')
    response = open('../../testdata/MangaFox/manga_list.htm', encoding='UTF-8')
    manga_list = plugin._parse_manga_list(response)
    assert(len(manga_list) == 16340)
    print('test successful')
    
    print('######################################################################')
    
    print('testing MangaFoxPlugin._parse_chapter_list()')
    response = open('../../testdata/MangaFox/chapter_list.htm', encoding='UTF-8')
    chapter_list = plugin._parse_chapter_list('', response)
    assert(len(chapter_list) == 821)
    print('test successful')
    
    print('######################################################################')
    
    print('testing MangaFoxPlugin._parse_image_list()')
    response = open('../../testdata/MangaFox/image.htm', encoding='UTF-8')
    image_list = plugin._parse_image_list(response)
    assert(len(image_list) == 17)
    print('test successful')
    
    print('######################################################################')
    
    print('testing MangaFoxPlugin._parse_image_url()')
    response = open('../../testdata/MangaFox/image.htm', encoding='UTF-8')
    url = plugin._parse_image_url(response)
    assert(url == 'image-Dateien/t001.jpg')
    print('test successful')
