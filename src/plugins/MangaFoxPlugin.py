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


# -------------------------------------------------------------------------------------------------
#  Plugin class
# -------------------------------------------------------------------------------------------------
class MangaFoxPlugin(PluginBase.PluginBase):

    def __init__(self):
        self.__domain = BASE_URL
        self.__list_of_found_chapter_URLs = {}
        self.__last_found_image_URL = ''


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
                number = text.rsplit(None, 1)[-1]
                title = a.find_next_sibling('span', class_='title').get_text()
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
        print('Found {} mangas on site!'.format(parser.targetCount))
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
    print('no test implemented')
