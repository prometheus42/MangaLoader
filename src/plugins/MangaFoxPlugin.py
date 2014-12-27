#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging

import src.PluginBase as PluginBase
from src.MangaBase import Manga

# -------------------------------------------------------------------------------------------------
#  logging
# -------------------------------------------------------------------------------------------------

logger = logging.getLogger('MangaReaderPlugin')

BASE_URL = "http://mangafox.me/"


# -------------------------------------------------------------------------------------------------
#  Plugin class
# -------------------------------------------------------------------------------------------------
class MangaFoxPlugin(PluginBase.PluginBase):

    def __init__(self):
        self.__domain = BASE_URL

    def getImage(self, image):
        global logger

        manga = image.chapter.manga
        chapter = image.chapter

        # http://mangafox.me/manga/coppelion/v19/c185/1.html
        url = self.__domain + "/" + self.__getInternalName(manga.name) + "/" + str(chapter.chapterNo) + "/" + str(image.imageNo)
        result = PluginBase.loadURL(url)

        if result is None:
            return False

        logger.debug("start parsing")
        parser = PluginBase.ParserBase(("div", "id", "imgholder"), ("img", "src"))
        parser.feed(result)

        logger.debug("targetCount = " + str(parser.targetCount))
        if parser.targetCount < 1:
            logger.info("No image found in MangaReader site, maybe the chapter is not available.")
            return False

        if parser.targetCount > 1:
            logger.warning(str(parser.targetCount) + " images found in MangaReader site, maybe the chapter is not available.")
            return False

        if parser.targetValue == "":
            logger.warning("No valid image url found in MangaReader site.")
            return False

        logger.debug("imageURL = " + str(parser.targetValue))
        image.imageUrl = parser.targetValue
        logger.debug("imageUrl found: " + parser.targetValue)
        return True


    def getListOfChapters(self, manga):
        raise NotImplementedError()

    def getListOfMangas(self):
        url = self.__domain + "/manga/"
        result = PluginBase.loadURL(url)
        if result is None:
            return False
        print("Finding mangas...")
        logger.debug("Finding mangas...")
        parser = PluginBase.ParserBase(("div", "class", "manga_list"), ("a", "href"))
        parser.feed(result)
        print("Found {} mangas on site!".format(parser.targetCount))
        if parser.targetCount > 1:
            list_of_all_mangas = list()
            for name, link in zip(parser.targetData, parser.targetValues):
                m = Manga(name)
                m.manga_url = link
                print(m)
                list_of_all_mangas.append(m)
        else:
            logger.warning('No mangas found on site.')

    def __getInternalName(self, name):
        internalName = name
        internalName = str.lower(internalName)
        internalName = str.replace(internalName, " ", "-")
        return internalName


# -------------------------------------------------------------------------------------------------
#  <module>
# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    print("no test implemented")
