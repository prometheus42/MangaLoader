
import logging

logger = logging.getLogger('MangaLoader.data')


# -------------------------------------------------------------------------------------------------
#  Manga class
# -------------------------------------------------------------------------------------------------
class Manga(object):

    def __init__(self, name):
        self.name = name
        self.chapter_list = []
        self.url = ''
        self.internalName = ''
        self.cover_url = ''
        self.is_open = None

    def __str__(self):
        return str(self.name)

    def add_chapter(self, chapter):
        chapter.manga = self
        self.chapter_list.append(chapter)

    def get_chapter(self, number):
        for chapter in self.chapter_list:
            if chapter.chapterNo == number:
                return chapter
        return None

    def get_chapters(self, numbers):
        result = []
        for chapter in self.chapter_list:
            if chapter.chapterNo == numbers or chapter.chapterNo in numbers:
                result.append(chapter)
        return result


# -------------------------------------------------------------------------------------------------
#  Chapter class
# -------------------------------------------------------------------------------------------------
class Chapter(object):

    def __init__(self, manga, chapter_no):
        self.manga = manga
        self.chapterNo = chapter_no
        self.chapterTitle = ''
        self.url = ''
        self.image_list = []
        self.text = ''
        self.title = ''

    def __str__(self):
        if self.manga is not None:
            return str(self.manga) + ' ' + str(self.chapterNo)
        else:
            return str(self.chapterNo)

    def add_image(self, image):
        image.chapter = self
        self.image_list.append(image)

    def get_image(self, number):
        for image in self.image_list:
            if image.imageNo == number:
                return image
        return None

    def get_images(self, numbers):
        result = []
        for image in self.image_list:
            if image.imageNo == numbers or image.imageNo in numbers:
                result.append(image)
        return result


# -------------------------------------------------------------------------------------------------
#  Image class
# -------------------------------------------------------------------------------------------------
class Image(object):

    def __init__(self, chapter, image_no):
        self.chapter = chapter
        self.imageNo = image_no
        self.url = None

    def __str__(self):
        if self.chapter is not None:
            return str(self.chapter) + ' - ' + str(self.imageNo)
        else:
            return str(self.imageNo)
