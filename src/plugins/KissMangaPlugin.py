#!/usr/bin/python3

import re
import logging

import src.PluginBase as PluginBase
from src.PluginBase import find_re_in_site
from src.MangaBase import Manga
from src.MangaBase import Chapter
from src.helper import memoized

# -------------------------------------------------------------------------------------------------
#  logging
# -------------------------------------------------------------------------------------------------

logger = logging.getLogger('MangaLoader.KissMangaPlugin')

BASE_URL = 'http://kissmanga.com/'


# -------------------------------------------------------------------------------------------------
#  Plugin class
# -------------------------------------------------------------------------------------------------
class KissMangaPlugin(PluginBase.PluginBase):
    """
    
    Searchfield on webpage:
       
    POST http://kissmanga.com/Search/SearchSuggest
    type=Manga&keyword=Dragon
    type=AuthorArtist&keyword=???

    List of all mangas:
    
    http://kissmanga.com/MangaList?c=0
    http://kissmanga.com/MangaList?c=a
    ...
    http://kissmanga.com/MangaList?c=z

    """

    def __init__(self):
        self.__domain = BASE_URL
        self.__list_of_found_chapter_URLs = {}
        self.__last_found_image_URL = ''

    def getImage(self, image):
        logger.debug('Start parsing...')
        #parser = PluginBase.ParserBase(('div', 'class', 'read_img'), ('img', 'src'))
        #parser.feed(result)
        #logger.debug('imageUrl found: {}'.format(parser.targetValue))
        #return True

    def getListOfChapters(self, manga):
        url = manga.mangaURL
        result = PluginBase.loadURL(url, evaluateJS=True)
        if result is None:
            return ()
        parser = PluginBase.ParserBase(('table', 'class', 'listing'), ('a', 'href'))
        parser.feed(result)
        if parser.targetCount > 1:
            for x, y in zip(parser.targetData, parser.targetValues):
                print(x, y)
        return ()

    def getListOfMangas(self):
        url = '/'.join((self.__domain, 'MangaList?c=a'))
        result = PluginBase.loadURL(url, evaluateJS=True)
        if result is None:
            return ()
        print('Finding mangas...')
        logger.debug('Finding mangas...')
        parser = PluginBase.ParserBase(('table', 'class', 'listing'), ('a', 'href'))
        parser.feed(result)
        print('Found {} mangas on site!'.format(parser.targetCount))
        list_of_all_mangas = []
        if parser.targetCount > 1:
            for name, link in zip(parser.targetData, parser.targetValues):
                m = Manga(name)
                m.mangaURL = link
                print(m, m.mangaURL)
                list_of_all_mangas.append(m)
        else:
            m = Manga('One Piece')
            m.mangaURL = 'http://kissmanga.com/Manga/One-Piece'
            list_of_all_mangas.append(m)
            m = Manga('Coppelion')
            m.mangaURL = 'http://kissmanga.com/Manga/Coppelion'
            list_of_all_mangas.append(m)
            logger.warning('No mangas found on site.')
        return list_of_all_mangas

    def postprocessImage(self, filename):
        logger.debug('Postprocess image files...')

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
