#!/usr/bin/python3

import logging
import urllib

from bs4 import BeautifulSoup

import src.PluginBase as PluginBase
from src.data import Manga, Chapter, Image
from src.helper import memoized


logger = logging.getLogger('MangaLoader.MangaFoxPlugin')

BASE_URL = 'http://mangafox.me/'
MANGA_LIST_URL = BASE_URL + 'manga/'


# -------------------------------------------------------------------------------------------------
#  MangaFoxPlugin class
# -------------------------------------------------------------------------------------------------
class MangaFoxPlugin(PluginBase.PluginBase):

    def __init__(self):
        pass

    @memoized
    def load_manga_list(self):
        loaded_manga_list = PluginBase.load_url(MANGA_LIST_URL)
        return self._parse_manga_list(loaded_manga_list)
    
    @staticmethod
    def _parse_manga_list(data):
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
        chapter_list = self._parse_chapter_list(manga, response)
        for chapter in chapter_list:
            manga.add_chapter(chapter)
        return chapter_list
    
    @staticmethod
    def _parse_chapter_list(manga, data):
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
                        chapter = Chapter(manga, int(number_string))
                        chapter.url = a['href']
                        chapter.text = a.get_text()
                        if span is not None:
                            chapter.title = span.string
                        list_of_chapters.append(chapter)
        return list_of_chapters
    
    @memoized
    def load_images_for_chapter(self, chapter):
        response = PluginBase.load_url(chapter.url)
        image_list = self._parse_image_list(chapter, response)
        for image in image_list:
            chapter.add_image(image)
        return image_list
    
    def _parse_image_list(self, chapter, data):
        result = []
        options = []
        doc = BeautifulSoup(data, 'html.parser')
        div = doc.find('div', class_='r m')
        select = div.find('select', class_='m')
        for option in select.find_all():
            value = option['value']
            if value is not None and value.isdigit():
                options.append(int(value))

        base_url = chapter.url.rsplit('/',1)[0] + '/'
        for option in options:
            if option > 0:
                image = Image(chapter, option)
                image.url = self._parse_image_page(urllib.parse.urljoin(base_url, '{}.html'.format(option)))
                result.append(image)
        return result
    
    @memoized
    def load_image_url(self, image):
        list_of_images = self.load_images_for_chapter(image.chapter)
        for i in list_of_images:
            if i.imageNo == image.imageNo:
                image.url = i.url
                return True
        return False

    @staticmethod
    def _parse_image_page(page_url):
        data = PluginBase.load_url(page_url)
        doc = BeautifulSoup(data, 'html.parser')
        outer_div = doc.find('div', id='viewer')
        inner_div = outer_div.find('div', class_='read_img')
        img = inner_div.find('img', id='image')
        return img['src']

    def postprocess_image(self, filename):
        logger.debug('Cropping image file to delete ads.')
        # image = PIL.Image.open(filename)
        # w, h = image.size
        # image.crop((0, 0, w, h-30)).save(filename)


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
