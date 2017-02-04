#!/usr/bin/python3

import os
import logging
import xml.etree.ElementTree as ET

# -------------------------------------------------------------------------------------------------
#  logging
# -------------------------------------------------------------------------------------------------

logger = logging.getLogger('MangaLoader.CometGenerator')

# -------------------------------------------------------------------------------------------------
#  comet functions
#  see http://www.denvog.com/comet/comet-specification/
# -------------------------------------------------------------------------------------------------
def create_comet(manga_dir, chapter):
    global logger
    logger.debug('create_comet(' + str(manga_dir) + ', ' + str(chapter) + ')')
    
    if not os.path.exists(manga_dir):
        raise RuntimeError('Unable to create comet file, because the manga folder is missing')
    
    comet_file = manga_dir + '/' + 'comet.xml'
    logger.debug('create comet file "{}"...'.format(str(comet_file)))
    
    root = ET.Element('comet')
    root.attrib['xmlns:comet'] = 'http://www.denvog.com/comet/'
    root.attrib['xmlns:xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'
    root.attrib['xsi:schemaLocation'] = 'http://www.denvog.com http://www.denvog.com/comet/comet.xsd'
    
    title = ""
    if chapter.manga is not None:
        ET.SubElement(root, 'series').text = chapter.manga.name
        title = title + str(chapter.manga.name) + ' ' + str(chapter.number)
    if chapter.title:
        title = title + ' - ' + str(chapter.title)
    if title:
        ET.SubElement(root, 'title').text = title
    
    ET.SubElement(root, 'issue').text = str(chapter.number)
    # ET.SubElement(root, 'volume').text = ''
    ET.SubElement(root, 'language').text = 'ja'
    ET.SubElement(root, 'pages').text = str(len(chapter.imagelist))
    ET.SubElement(root, 'readingDirection').text = 'rtl'
    
    tree = ET.ElementTree(root)
    tree.write(comet_file, encoding='UTF-8', xml_declaration=True)

# -------------------------------------------------------------------------------------------------
#  <module>
# -------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    print('No test implemented!')
