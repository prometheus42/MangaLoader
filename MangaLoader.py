#!/usr/bin/python3

import os
import sys
import time
import logging
import logging.handlers
from os.path import expanduser
from optparse import OptionParser

from src import MangaBase
from src.plugins import MangaFoxPlugin


APP_NAME = 'MangaLoader'
APP_VERSION = 'v0.2'


# -------------------------------------------------------------------------------------------------
#  logging
# -------------------------------------------------------------------------------------------------

def create_logger():
    """Creates logger for this application."""
    LOG_FORMAT = '%(asctime)-23s [%(levelname)8s] %(name)-15s %(message)s (%(filename)s:%(lineno)s)'
    LOG_LEVEL = logging.DEBUG
    LOG_FILENAME = os.path.join(expanduser("~"), '.MangaLoader', 'mangaloader.log')

    logger = logging.getLogger('MangaLoader')
    logger.setLevel(LOG_LEVEL)

    # add logging to screen
    log_to_screen = logging.StreamHandler(sys.stdout)
    log_to_screen.setLevel(LOG_LEVEL)
    logger.addHandler(log_to_screen)

    # add logging to file
    os.makedirs(os.path.dirname(LOG_FILENAME), exist_ok=True)
    log_to_file = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                                       maxBytes=262144,
                                                       backupCount=5)
    log_to_file.setLevel(LOG_LEVEL)
    log_to_file.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(log_to_file)

    return logger


# -------------------------------------------------------------------------------------------------
#  <module>
# -------------------------------------------------------------------------------------------------

# test with:
#  python MangaLoader.py --MangaReader -n Claymore -r 14 20 -o /home/markus/Desktop/New Mangas


def parse_and_load():

    #####
    # Specify options and parse arguments.
    #####

    logger.info('MangaLoader started')

    logger.debug('starting to parse options and args')

    usage = 'usage: %prog [options]'
    parser = OptionParser(usage)
    parser.add_option('--version',
                    action='store_true',
                    dest='version',
                    help='show version information')
    parser.add_option('-m',
                    action='store',
                    dest='module',
                    help='specify the used module (currently supported: MangaFox)')
    parser.add_option('-z',
                    action='store_true',
                    dest='zip',
                    help='create cbz files')
    parser.add_option('-n',
                    action='store',
                    type='string',
                    dest='name',
                    metavar='NAME',
                    help='name of the manga')
    parser.add_option('-c',
                    action='store',
                    type='string',
                    dest='chapter',
                    metavar='CHAPTER(S)',
                    help='single or range of chapters (e.g. 1, 42-80)')
    parser.add_option('-o',
                    action='store',
                    type='string',
                    dest='output',
                    metavar='DEST_DIR',
                    help='destination directory')

    (options, args) = parser.parse_args()

    if options.version != None:
        print('{} {}'.format(APP_NAME, APP_VERSION))
        sys.exit()

    if options.module is None:
        logger.error('Missing module.')
        parser.print_usage()
        sys.exit()

    if options.name is None:
        logger.error('Missing manga name.')
        parser.print_usage()
        sys.exit()

    if options.output is None:
        logger.error('Missing destination folder.')
        parser.print_usage()
        sys.exit()

    chapter = None
    if options.chapter != None:
        if options.chapter.isdigit():
            chapter = [int(options.chapter)]
        else:
            try:
                parts = options.chapter.split('-')
                chapter = range(int(parts[0]), int(parts[1]) + 1)
            except ValueError:
                logger.error('Invalid chapter range.')
                parser.print_usage()
                sys.exit()

    if options.module.lower() == 'mangafox':
        pass
    else:
        logger.error('Unknown module.')
        parser.print_usage()
        sys.exit()

    logger.debug('options parse done')


    #####
    # Start actual manga load with specified parameter & arguments.
    #####

    start_time = time.time()
    logger.debug('start time: %.2f s' % (start_time))

    mangaName = options.name
    destDir = options.output

    doZip = options.zip != None

    logger.info('loading plugin')
    if options.module.lower() == 'mangafox':
        plugin = MangaFoxPlugin.MangaFoxPlugin()
        logger.debug('using MangaFox plugin')

    logger.info('loading Loader')
    loader = MangaBase.Loader(plugin, destDir)

    logger.info('loading chapters ' + str(chapter))
    ########
    #loader.handle(loader.get_manga_for_name(mangaName), chapter)
    #if doZip:
    #    loader.zip(loader.get_manga_for_name(mangaName), chapter)
    ########
    for c in chapter:
        loader.handleChapter(mangaName, c)
        if doZip:
            loader.zipChapter(mangaName, c)
    ########

    end_time = time.time()
    logger.debug('end time: %.2f s' % (end_time))
    logger.info('elapsed time: %.2f s' % (end_time - start_time))
    print(('Elapsed Time: %.2f s' % (end_time - start_time)))

    logger.info('MangaLoader done')


if __name__ == '__main__':
    global logger
    logger = create_logger()
    logger.info('Starting {}...'.format(APP_NAME))
    try:
        parse_and_load()
    except KeyboardInterrupt:
        logger.warn('Quit program!')
