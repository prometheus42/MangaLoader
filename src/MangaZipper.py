#!/usr/bin/python3

import os
import zipfile
import logging


logger = logging.getLogger('MangaLoader.MangaZipper')


# -------------------------------------------------------------------------------------------------
#  zipper functions
# -------------------------------------------------------------------------------------------------
def create_zip(manga_dir, dest_dir):
    global logger
    logger.debug('create_zip({}, {})'.format(manga_dir, dest_dir))

    if not os.path.exists(manga_dir) or not os.path.isdir(manga_dir):
        return False

    name = os.path.basename(os.path.normpath(manga_dir))
    zip_file_name = name + '.cbz'
    logger.debug('create cbz file "{}"...'.format(zip_file_name))
    with zipfile.ZipFile(os.path.join(dest_dir, zip_file_name), 'w') as cbzFile:
        for f in os.listdir(manga_dir):
            # TODO check file extension
            #  fileName, fileExtension = os.path.splitext(f)
            logger.debug('add file "{}" to cbz file "{}".'.format(f, zip_file_name))
            file_in_filesystem = os.path.join(manga_dir, f)
            # TODO: Check whether it is necessary to encode file_in_zipfile as ASCII (xxx.encode('ascii'))
            file_in_zipfile = os.path.join(name, os.path.basename(f))
            cbzFile.write(file_in_filesystem, file_in_zipfile, zipfile.ZIP_DEFLATED)

    return True

# -------------------------------------------------------------------------------------------------
#  <module>
# -------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    print('No test implemented!')
