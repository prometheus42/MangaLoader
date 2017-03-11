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
        loaded_manga_list = PluginBase.load_url(MANGA_LIST_URL)
        return self._parse_manga_list(loaded_manga_list)
    
    def _parse_manga_list(self, data):
        doc = BeautifulSoup(data, 'html.parser')
        list_of_mangas = []
        for div in doc.find_all('div', class_='manga_list'):
            for li in div.find_all('li'):
                for a in li.find_all('a'):
                    if a.string and a['class'] != 'top':
                        manga = Manga(a.string)
                        manga.url = a['href']
                        is_open = 'manga_open' in a['class']
                        manga.is_open = is_open
                        list_of_mangas.append(manga)
        return list_of_mangas
    
    @memoized
    def load_chapter_list(self, manga):
        response = PluginBase.load_url(manga.url)
        chapter_list = self._parse_chapter_list(response)
        for chapter in chapter_list:
            manga.add_chapter(chapter)
        return chapter_list
    
    def _parse_chapter_list(self, data):
        doc = BeautifulSoup(data, 'html.parser')
        list_of_chapters = []
        for div in doc.find_all('div', id='chapters'):
            for ul in div.find_all('ul', class_='chlist'):
                for li in ul.find_all('li'):
                    inner_div = li.find('div')
                    a = inner_div.find('a', class_='tips')
                    span = inner_div.find('span', class_='title nowrap')
                    
                    words = a.string.split()
                    number_string = words[len(words)-1]
                    if number_string.isdigit():  # ignore 'half' chapters
                        chapter = Chapter(int(number_string))
                        chapter.url = a['href']
                        chapter.text = a.get_text()
                        if span is not None:
                            chapter.title = span.string
                        list_of_chapters.append(chapter)
        return list_of_chapters
    
    @memoized
    def load_image_list(self, chapter):
        response = PluginBase.load_url(chapter.url)
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
        response = PluginBase.load_url(image.url)
        image.image_url = self._parse_image_url(response)
    
    def _parse_image_url(self, data):
        doc = BeautifulSoup(data, 'html.parser')
        
        # head = doc.head
        # meta = head.find('meta', property='og:image')
        # return meta['content']
        
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

        result = PluginBase.load_url(url)
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

    def postprocess_image(self, filename):
        logger.debug('Cropping image file to delete ads.')
        # image = Image.open(filename)
        # w, h = image.size
        # image.crop((0, 0, w, h-30)).save(filename)

    def __get_internal_name(self, name):
        internal_name = name
        internal_name = str.lower(internal_name)
        internal_name = str.replace(internal_name, ' ', '_')
        return internal_name


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
