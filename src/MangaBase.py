#!/usr/bin/python3

import logging
import mimetypes
import os
import pickle
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

import requests

from src.data import Manga, Chapter, Image
from src import MangaZipper


logger = logging.getLogger('MangaLoader.MangaBase')

MAX_DOWNLOAD_WORKER = 1
MANGA_LIST_FILE_PREFIX = 'Manga'
MANGA_LIST_FILE_SUFFIX = '.dat'


# -------------------------------------------------------------------------------------------------
#  ImageStoreManager class
# -------------------------------------------------------------------------------------------------
class ImageStoreManager(object):

    def __init__(self, base_dir):
        self.base_dir = base_dir

    def get_manga_dir(self, manga):
        return os.path.join(self.base_dir, manga.name)

    def get_chapter_dir(self, chapter):
        return os.path.join(self.get_manga_dir(chapter.manga), '{name} {no:03d}'.format(name=chapter.manga, no=chapter.chapterNo))

    def get_image_path(self, image, include_extension=False):
        """
        Builds the path to save the downloaded image to. If the keyword parameter
        include_extension is False, the resulting image path contains no file
        extension and it can be added later depending on the header information
        of the HTTP response.
        """
        if include_extension:
            image_extension = '.' + os.path.splitext(image.imageUrl)
        else:
            image_extension = ''
        return os.path.join(self.get_chapter_dir(image.chapter),
                            '{ImageNo:03d}{Ext}'.format(ImageNo=image.imageNo,Ext=image_extension))

    def find_next_image(self, start_with_manga, start_with_chapter):
        """
        Finds path of the next image that should be shown. After a given
        chapter of a series is finished, the next image is automatically from
        the following chapter.
        """
        # TODO: Implement reversing direction to get to previous image.
        while True:
            chapter_path = self.get_chapter_dir(start_with_chapter)
            # TODO: Check whether to filter for file type/extension.
            for path, dirs, files in os.walk(chapter_path):
                for f in sorted(files):
                    path = os.path.abspath(os.path.join(chapter_path, f))
                    yield path
            # TODO: Handle this better!!!
            start_with_chapter.chapterNo += 1

    def do_image_already_exists(self, image):
        """
        Checks whether a given image is already present in the image store.
        """
        return os.path.exists(self.get_image_path(image, include_extension=True))


# -------------------------------------------------------------------------------------------------
#  Loader class
# -------------------------------------------------------------------------------------------------
class Loader(object):

    def __init__(self, loader_plugin, store_directory, pickle_data=True):
        self.loader_plugin = loader_plugin
        self.__store_directory = store_directory
        self.pickle_data = pickle_data
        self.image_store_manager = ImageStoreManager(store_directory)
        self.manga_list = None
        self.manga_list_filename = '{}-{}{}'.format(MANGA_LIST_FILE_PREFIX, loader_plugin.__class__.__name__, MANGA_LIST_FILE_SUFFIX)
        if pickle_data:
            self._load_manga_list()

    @property
    def store_directory(self):
        return self.__store_directory

    @store_directory.setter
    def store_directory(self, value):
        self.__store_directory = value
        self.image_store_manager.base_dir = value

    def _load_manga_list(self):
        try:
            with open(self.manga_list_filename, 'rb') as f:
                self.manga_list = pickle.load(f)
            return self.manga_list
        except OSError:
            logger.info('No manga list file found.')
        except EOFError:
            logger.error('Manga list file ended unexpectedly.')

    def _save_manga_list(self):
        """
        Save current manga list to file. The list will be pickled with the
        highest available protocol the python version supports.
        """
        logger.info('Saving manga list to file.')
        error = False
        with open(self.manga_list_filename, 'wb') as f:
            # pickle the manga list using the highest protocol available
            try:
                pickle.dump(self.manga_list, f) #, pickle.HIGHEST_PROTOCOL
            except RecursionError as e:
                error = True
        if error:
            os.remove(self.manga_list_filename)

    def get_all_mangas(self, update=False):
        if update:
            self.manga_list = self.loader_plugin.load_manga_list()
            # FIXME: Problem with circular dependencies between Manga and Chapter!
            if self.pickle_data:
                self._save_manga_list()
        else:
            if not self.manga_list:
                self.manga_list = self._load_manga_list()
                if not self.manga_list:
                    self.manga_list = self.get_all_mangas(update=True)
        return self.manga_list

    def get_manga_by_name(self, manga_name):
        """
        Returns a manga object containing a reference to the page of the manga
        with the given name. If no manga with the given name is found, None is
        returned.
        """
        logger.debug('Getting Manga object for given name: {}'.format(manga_name))
        self.get_all_mangas()
        for manga in self.manga_list:
            if manga.name == manga_name:
                return manga
        return None

    def get_all_chapters(self, chosen_manga):
        return self.loader_plugin.load_chapter_list(chosen_manga)

    def parse_chapter_for_manga(self, manga=None, chapter_no=None, image_no=None, load_images=True, update=False):
        """
        Parses pages for given manga and extracts links to all images for all
        chapters that are given as parameters. The parameter load_images decides
        if image URLs are extracted.
        """
        manga_name = '' if manga is None else manga.name
        # FIXME: Handle None for manga parameter.
        logger.debug('parse_manga({}, {}, {})'.format(str(manga_name), str(chapter_no), str(image_no)))
        logger.debug('parsing manga ' + str(manga))
        self.plugin.load_chapter_list(manga)
        if load_images:
            self._parse_images_for_chapter(manga, chapter_no, image_no)
        return manga

    def _parse_images_for_chapter(self, manga, chapter_no, image_no):
        for chapter in manga.chapterlist:
            if chapter_no is None or chapter.number == chapter_no or chapter.number in chapter_no:
                logger.debug('parsing image list for ' + str(chapter))
                self.plugin.load_images_for_chapter(chapter)
                for image in chapter.imagelist:
                    if image_no is None or image.number == image_no or image.number in image_no:
                        logger.debug('parsing image url ' + str(image))
                        self.plugin.load_image_url(image)

    def handle(self, manga, chapter_list):
        if manga is None:
            raise RuntimeError('Parameter Manga is None.')

        logger.debug('handle({}, {})'.format(str(manga.name), str(chapter_list)))
        self.parse_chapter_for_manga(manga, chapter_list)
        for chapter_no in chapter_list:
            chapter = manga.get_chapter(chapter_no)
            if chapter is None:
                # FIXME: Do we want the program to exit if a wrong chapter no is given?
                raise RuntimeError('Unable to retrieve chapter ' + str(chapter_no) + ' for manga ' + str(manga))
            for image in chapter.imagelist:
                if image is None:
                    raise RuntimeError('Unable to retrieve image for chapter ' + str(chapter))
                self.load_image(image)

    def zip(self, manga, chapter_list):
        if manga is None:
            raise RuntimeError('Parameter Manga is None.')

        logger.debug('zip({}, {})'.format(str(manga.name), str(chapter_list)))
        self.parse_chapter_for_manga(manga, chapter_list)

        for chapter_no in chapter_list:
            chapter = manga.get_chapter(chapter_no)
            if chapter is None:
                # FIXME: Do we want the program to exit if a wrong chapter no is given?
                raise RuntimeError('Unable to retrieve chapter ' + str(chapter_no) + ' for manga ' + str(manga))
            manga_dir = self.image_store_manager.get_manga_dir(manga)
            chapter_dir = self.image_store_manager.get_chapter_dir(chapter)
            MangaZipper.create_zip(chapter_dir, manga_dir)
            logger.info('cbz: "' + str(chapter) + '"')

    def load_chapter(self, chapter):
        list_of_futures = list()
        with ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKER) as executor:
            for image in chapter.imagelist:
                f = executor.submit(self.load_image, image)
                list_of_futures.append(f)
        return all(list_of_futures)

    def load_image(self, image):
        # calculate destination path and call store_file_on_disk()
        if not self.store_file_on_disk(image.image_url, self.image_store_manager.get_image_path(image)):
            return False
        logger.info('load: "' + str(image) + '"')
        return True

    def store_file_on_disk(self, source, dest):
        # create directories first
        try:
            os.makedirs(dest[0 : dest.rfind('/')])
        except OSError:
            pass
        # open source url and copy to destination file; retry 5 times
        # TODO: Check how to implement retry counter with requests library.
        tries = 1
        while True:
            import urllib
            try:
                r = requests.get(source, stream=True)
                # get file extension for content type
                content_type = r.headers['content-type']
                extension = mimetypes.guess_extension(content_type)
                # alternatively use urllib to parse url to get extension
                parsed = urlparse(source)
                root, ext = os.path.splitext(parsed.path)
                if extension != ext:
                    logger.warning('File extension unclear: {} <-> {}'.format(extension, ext))
                if extension is None:
                    extension = '.jpeg'
                    logger.warning('Could not guess file extension, using jpeg.')
                # save data to file if status code 200 was returned
                if r.status_code == 200:
                    with open('{}{}'.format(dest,extension), 'wb') as f:
                        # write chunks of default size (128 byte)
                        for chunk in r:
                            f.write(chunk)
                self.loader_plugin.postprocess_image(dest)
                return True
            except urllib.error.URLError:
                logger.warning('failed to load "' + str(source) + '" (' + str(tries) + ')')
                if tries >= 5:
                    logger.error('failed to load "' + str(source) + '"')
                    return False
            tries += 1

    ############# following are the old methods of this class ##################

    def handleChapter2(self, chapter):
        logger.debug('handleChapter({})'.format(chapter))
        if not self.parseChapter(chapter):
            return False
        if not self.loadChapter(chapter):
            return False
        return True

    def handleChapter(self, name, chapterNo):
        logger.debug('handleChapter({}, {})'.format(name, chapterNo))
        chapter = Chapter(Manga(name), chapterNo)
        if not self.parseChapter(chapter):
            return False
        if not self.loadChapter(chapter):
            return False
        return True

    def handleImage(self, name, chapterNo, imageNo):
        logger.debug('handleChapter({}, {}, {})'.format(name, chapterNo, imageNo))
        image = Image(Chapter(Manga(name), chapterNo), imageNo)
        if not self.parseImage(image):
            return False
        if not self.loadImage(image):
            return False
        return True

    def zipChapter(self, name, chapterNo):
        logger.debug('zipChapter({}, {})'.format(name, chapterNo))
        manga = Manga(name)
        chapter = Chapter(manga, chapterNo)
        if MangaZipper.create_zip(self.image_store_manager.get_chapter_dir(chapter), self.image_store_manager.get_manga_dir(manga)):
            logger.info('cbz: "' + str(chapter) + '"')
            return True
        return False

    def zipChapter2(self, manga, chapter):
        logger.debug('zipChapter({}, {})'.format(manga.name, chapter.chapterNo))
        if MangaZipper.create_zip(self.image_store_manager.get_chapter_dir(chapter), self.image_store_manager.get_manga_dir(manga)):
            logger.info('cbz: "' + str(chapter) + '"')
            return True
        return False

    def parseManga(self, manga):
        return_value = False
        # FIXME Do NOT use maximum number of chapters because "One Piece" :-)
        for i in range(1, 1000):
            chapter = Chapter(manga, i)
            if not self.parseChapter(chapter):
                break
            manga.addChapter(chapter)
            return_value = True
        return return_value

    def parseChapter(self, chapter):
        return_value = False
        for i in range(1,1000):
            image = Image(chapter, i)
            if not self.parseImage(image):
                break
            chapter.add_image(image)
            return_value = True
        return return_value

    def parseImage(self, image):
        if self.loader_plugin is None:
            return False
        if not self.loader_plugin.load_image_url(image):
            return False

        logger.info('parse: "' + str(image) + '"')
        return True

    def loadManga(self, manga):
        for chapter in manga.chapterList:
            if not self.loadChapter(chapter):
                return False
        return True

    def loadChapter(self, chapter):
        for image in chapter.image_list:
            self.loadImage(image)
        return True
        ######
        list_of_futures = list()
        # context manager cleans up automatically after all threads have executed 
        with ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKER) as executor:
            for image in chapter.imageList:
                f = executor.submit(self.loadImage, image)
                list_of_futures.append(f)
        return True

    def loadImage(self, image):
        # calculate destination path and call store_file_on_disk()
        if not self.store_file_on_disk(image.url, self.image_store_manager.get_image_path(image)):
            return False
        logger.info('load: "{}"'.format(image))
        return True


# -------------------------------------------------------------------------------------------------
#  <module>
# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    print('No test implemented!')
