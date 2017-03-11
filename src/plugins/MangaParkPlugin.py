#!/usr/bin/python3

import logging
import urllib.parse

from bs4 import BeautifulSoup

import src.PluginBase as PluginBase
from data import Manga, Chapter, Image
from src.MangaBase import Chapter
from src.MangaBase import Image
from src.helper import memoized
from src.PluginBase import load_url

# -------------------------------------------------------------------------------------------------
#  logging
# -------------------------------------------------------------------------------------------------

logger = logging.getLogger('MangaLoader.MangaParkPlugin')

BASE_URL = 'http://mangapark.me/'
MANGA_LIST_URL = BASE_URL + 'genre/'


# -------------------------------------------------------------------------------------------------
#  Plugin class
# -------------------------------------------------------------------------------------------------
class MangaParkPlugin(PluginBase.PluginBase):

    def __init__(self):
        self.__domain = BASE_URL
        self.__list_of_found_chapter_URLs = {}
        self.__last_found_image_URL = ''

    @memoized
    def load_manga_list(self):
        response = load_url(MANGA_LIST_URL)
        return self._parse_manga_list(response)
    
    def _parse_manga_list(self, data):
        doc = BeautifulSoup(data, 'html.parser')
        result = []
        for div in doc.find_all('div', class_='item'):
            for a in div.find_all('a', class_='cover'):
                manga = Manga(a['title'])
                manga.url = urllib.parse.urljoin(BASE_URL, a['href'])
                manga.cover_url = a.find('img')['src']
                result.append(manga)
        return result
    
    @memoized
    def load_chapter_list(self, manga):
        response = load_url(manga.url)
        chapter_list = self._parse_chapter_list(manga, response)
        for chapter in chapter_list:
            manga.add_chapter(chapter)
        return chapter_list
    
    def _parse_chapter_list(self, manga, data):
        doc = BeautifulSoup(data, 'html.parser')
        result = []
        for div in doc.find_all('div', id='list'):
            for span in div.find_all('span'):
                a = span.find('a')
                begin_chapter_title = span.text.find(':') + 2
                chapter_title = span.text[begin_chapter_title:]
                if not a:
                    continue
                try:
                    begin_no = a.string.find('ch.') + 3
                    no = int(a.string[begin_no:])
                except:
                    logger.error('Error while converting chapter number: {}'.format(a.string))
                    no = 0
                chapter = Chapter(manga, no)
                chapter.url = urllib.parse.urljoin(BASE_URL, a['href'])
                chapter.title = chapter_title
                result.append(chapter)
        return result

    def load_image_url(self, image):
        list_of_images = self.load_images_for_chapter(image.chapter)
        for i in list_of_images:
            if i.imageNo == image.imageNo:
                image.url = i.url
                return True
        return False

    @memoized
    def load_images_for_chapter(self, chapter):
        response = load_url(chapter.url)
        image_list = self._parse_image_list(chapter, response)
        for image in image_list:
            chapter.add_image(image)
        return image_list
    
    def _parse_image_list(self, chapter, data):
        doc = BeautifulSoup(data, 'html.parser')
        list_of_images = []
        outer_div = doc.find('div', class_='board')
        inner_div = outer_div.find('div', class_='info')
        for div in inner_div.find_all('div'):
            if 'Pages:' in div.find('p').find('span').text:
                for a in div.find('p').find_all('a'):
                    image = Image(chapter, int(a.string))
                    image.url = self.__parse_image_page(urllib.parse.urljoin(BASE_URL, a['href']))
                    list_of_images.append(image)
                break
        return list_of_images

    def __parse_image_page(self, page_url):
        response = load_url(page_url)
        doc = BeautifulSoup(response, 'html.parser')
        image = doc.find('a', class_='img-link').find('img')
        # no = image['rel']
        url = image['src']
        return url

    def postprocess_image(self, filename):
        pass


# -------------------------------------------------------------------------------------------------
#  <module>
# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    print('No test implemented!')
