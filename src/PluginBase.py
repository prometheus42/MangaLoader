#!/usr/bin/python3

import urllib.request, urllib.parse, urllib.error
import re
import logging
import requests
from html.parser import HTMLParser

# -------------------------------------------------------------------------------------------------
#  logging
# -------------------------------------------------------------------------------------------------

logger = logging.getLogger('MangaLoader.PluginBase')


# -------------------------------------------------------------------------------------------------
#  PluginBase class
# -------------------------------------------------------------------------------------------------
class PluginBase(object):

    def load_image_url(self, image):
        """Gets an image URL for a specific manga from a specific chapter. The
        URL is stored in the given Image object.

        :return: true, when a valid image URL for wanted image could be found"""
        raise NotImplementedError()

    def load_images_for_chapter(self, chapter):
        """Creates Image objects for all individual images of a given chapter and stores the URLs for those images.

        :param chapter: chapter for which to load images
        :return: list of all images"""
        raise NotImplementedError()

    def load_chapter_list(self, manga):
        """Gets a list of all current chapters from a given manga.

        :param manga: identifier for a available manga on this site.
        :return: list of chapter objects for all chapters of this manga currently available at this site."""
        raise NotImplementedError()

    def load_manga_list(self):
        """Gets the current list of all available mangas from a given site."""
        raise NotImplementedError()

    def postprocess_image(self, filename):
        """Processes the loaded image of a manga page after it has been downloaded."""
        raise NotImplementedError()


# -------------------------------------------------------------------------------------------------
#  Parser class
# -------------------------------------------------------------------------------------------------
class ParserBase(HTMLParser):
    """Parses a given HTML site and seaches for a specified attribute of a
    given tag inside another specified tag. The outer tag is defined by tag
    name and attribute with its value.

    TODO: Extend to a list of (tags, attrib, value) tupel, to find a specific
    value? [("div", "id", "imgholder"), ("img", "src", xxx)]
    """

    def __init__(self, outer, inner):
        """Sets all internal variables."""
        HTMLParser.__init__(self)

        (outerTag, outerAttrib, outerValue) = outer
        (innerTag, innerAttrib) = inner

        self.__outerTag = outerTag
        self.__outerAttrib = outerAttrib
        self.__outerValue = outerValue
        self.__innerTag = innerTag
        self.__innerAttrib = innerAttrib

        self.__insideOuterTag = False
        self.__outerCount = 0

        self.targetValue = ''
        self.targetCount = 0
        self.targetValues = list()
        self.targetData = list()

    def handle_starttag(self, tag, attrs):
        """Searches for the outer tag and looks for the begin of the inner tag
        when inside the outer tag."""
        self.find_outer_tag_start(tag, attrs)
        if self.__insideOuterTag:
            self.increase_outer_count(tag)
            self.find_inner_tag(tag, attrs)

    def handle_data(self, data):
        """Handles data only inside the given outer tag and stores the data
        each time in the same variable to be read."""
        if self.__insideOuterTag:
            if not data.isspace():
                self.targetData.append(data)

    def handle_endtag(self, tag):
        """Decreases inner tag count when end tag was reached."""
        if self.__insideOuterTag:
            self.decrease_outer_count(tag)

    def find_outer_tag_start(self, tag, attrs):
        """Check whether the current tag is the outer tag to search for."""
        global logger

        if tag == self.__outerTag:
            # check attribute and its value only when they have been given...
            if self.__outerAttrib and self.__outerValue:
                for attr in attrs:
                    if (attr[0] == self.__outerAttrib) and (attr[1] == self.__outerValue):
                        self.__insideOuterTag = True
                        break
            # ...otherwise just do it!
            else:
                self.__insideOuterTag = True

    def increase_outer_count(self, tag):
        """Increases the current level of outer tags inside the outer tag."""
        if tag == self.__outerTag:
            self.__outerCount += 1

    def decrease_outer_count(self, tag):
        """Decreases the current level of outer tags inside the outer tag. If
        the count reaches zero, this is the outer end tag."""
        if tag == self.__outerTag:
            self.__outerCount -= 1
        if self.__outerCount == 0:
            self.__insideOuterTag = False

    def find_inner_tag(self, tag, attrs):
        """Check whether the current tag is the inner tag to search for."""
        global logger
        if self.__insideOuterTag:
            if tag == self.__innerTag:
                for attr in attrs:
                    if attr[0] == self.__innerAttrib:
                        self.targetValue = attr[1]
                        self.targetValues.append(attr[1])
                        self.targetCount += 1
                        break

    def error(self, message):
        logger.error('Error while parsing HTML: {}'.format(message))


# -------------------------------------------------------------------------------------------------
#  FindTagParser
# -------------------------------------------------------------------------------------------------
class FindTagParser(HTMLParser):
    """Finds a tag with a given attribute and its value."""

    def __init__(self, tag, attribute, value, result_tag):
        """Sets all internal variables."""
        HTMLParser.__init__(self)
        self.tag = tag
        self.attribute = attribute
        self.value = value
        self.result_tag = result_tag
        self.targetCount = 0
        self.targetValue = ''

    def handle_starttag(self, tag, attrs):
        if tag == self.tag:
            correct_tag = False
            for attribute in attrs:
                # check if attribute is correct
                if attribute[0] == self.attribute and attribute[1] == self.value:
                    correct_tag = True
            if correct_tag:
                # extract wanted information only when correct tag was found
                for attribute in attrs:
                    if attribute[0] == self.result_tag:
                        self.link = attribute[1]
                        self.targetCount += 1
                        self.targetValue = self.link

    def error(self, message):
        logger.error('Error while parsing HTML: {}'.format(message))


# -------------------------------------------------------------------------------------------------
#  find_re_in_site
# -------------------------------------------------------------------------------------------------
def find_re_in_site(url, regex):
    """Opens a site, downloads its content and check with a regular expression
    whether any matching string can be found.

    :param url: site URL to be scanned for matching strings
    :param regex: regular expression to be searched for
    """
    site = urllib.request.urlopen(url)
    content = site.read().decode(site.headers.get_content_charset())
    result_list = re.findall(regex, content)
    return result_list


# -------------------------------------------------------------------------------------------------
#  loadURL
# -------------------------------------------------------------------------------------------------
def load_url(url, max_try_count=5, evaluate_js=False):
    """Load content of a given URL and return the pages source.
    
    Sources:
     * http://stackoverflow.com/questions/8049520/web-scraping-javascript-page-with-python
    """
    global logger
    logger.debug('Start loading URL "{}".'.format(str(url)))

    agent_string = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0'

    if evaluate_js:
        # render web page in browser with JS and get result from there
        import dryscrape
        session = dryscrape.Session()
        session.visit(url)
        result = session.body()
        print(result)
        return result
    else:
        headers = {'User-Agent': agent_string}
        try:
            logger.debug('requesting: {}'.format(url))
            request = requests.get(url)
            if request.status_code == 200:
                result = request.text
                logger.debug('URL successfully loaded.')
            else:
                result = ''
                logger.warn('URL could not be loaded.')
            return result
        except requests.exceptions.ConnectionError:
            logger.warn('URL could not be loaded.')


# -------------------------------------------------------------------------------------------------
#  <module>
# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    print('No test implemented!')
