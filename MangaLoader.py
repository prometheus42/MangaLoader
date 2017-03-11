#!/usr/bin/python3

import os
import sys
import time
import logging
import logging.handlers
from os.path import expanduser
from optparse import OptionParser

from src import MangaBase
from src.plugins import MangaFoxPlugin, MangaParkPlugin


APP_NAME = 'MangaLoader'
APP_VERSION = 'v0.2'


# -------------------------------------------------------------------------------------------------
#  logging
# -------------------------------------------------------------------------------------------------

def create_logger():
    """Creates logger for this application."""
    log_format = '%(asctime)-23s [%(levelname)8s] %(name)-15s %(message)s (%(filename)s:%(lineno)s)'
    log_level = logging.DEBUG
    log_filename = os.path.join(expanduser("~"), '.MangaLoader', 'mangaloader.log')

    global logger
    logger = logging.getLogger('MangaLoader')
    logger.setLevel(log_level)

    # add logging to screen
    log_to_screen = logging.StreamHandler(sys.stdout)
    log_to_screen.setLevel(logging.INFO)
    logger.addHandler(log_to_screen)

    # add logging to file
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    log_to_file = logging.handlers.RotatingFileHandler(log_filename, maxBytes=262144, backupCount=5)
    log_to_file.setLevel(log_level)
    log_to_file.setFormatter(logging.Formatter(log_format))
    logger.addHandler(log_to_file)
    return logger


# -------------------------------------------------------------------------------------------------
#  <module>
# -------------------------------------------------------------------------------------------------

# test with:
#  python3 MangaLoader.py -m MangaFox -n Claymore -c 14-20 -o /home/markus/Desktop/
#  python3 MangaLoader.py -m MangaPark -n "Fairy Tail" -c 9 -o .


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
                      help='specify the used module (currently supported: MangaFox, MangaPark)')
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

    if options.version is not None:
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

    chapter = []
    if options.chapter is not None:
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

    if not options.module.lower() in ('mangafox', 'mangapark'):
        logger.error('Unknown module.')
        parser.print_usage()
        sys.exit()

    logger.debug('options parse done')

    #####
    # Start actual manga load with specified parameter & arguments.
    #####

    start_time = time.time()
    logger.debug('start time: %.2f s' % start_time)

    manga_name = options.name
    dest_dir = options.output
    do_zip = options.zip is not None

    logger.info('loading plugin')
    if options.module.lower() == 'mangafox':
        plugin = MangaFoxPlugin.MangaFoxPlugin()
        logger.debug('using MangaFox plugin')
    elif options.module.lower() == 'mangapark':
        plugin = MangaParkPlugin.MangaParkPlugin()
        logger.debug('using MangaPark plugin')
    else:
        plugin = MangaFoxPlugin.MangaFoxPlugin()
        logger.warning('using MangaFox plugin because no plugin was given')

    logger.info('loading Loader')
    loader = MangaBase.Loader(plugin, dest_dir)

    logger.info('loading chapters ' + str(chapter))
    manga = loader.get_manga_by_name(manga_name)
    # TODO: Check whether manga with given name exists.
    chapter_list = loader.get_all_chapters(manga)
    for no in chapter:
        # find chapter object
        current_chapter = None
        for c in chapter_list:
            if c.chapterNo == no:
                current_chapter = c
                break
        if current_chapter:
            loader.handle_chapter(current_chapter)
            if do_zip:
                loader.zip_chapter(manga, current_chapter)
        else:
            logger.error('Could not find object for chapter {}.'.format(no))

    end_time = time.time()
    logger.debug('end time: %.2f s' % end_time)
    logger.info('elapsed time: %.2f s' % (end_time - start_time))
    print(('Elapsed Time: %.2f s' % (end_time - start_time)))

    logger.info('MangaLoader done')


if __name__ == '__main__':
    logger = create_logger()
    logger.info('Starting {}...'.format(APP_NAME))
    try:
        parse_and_load()
    except KeyboardInterrupt:
        logger.warning('Quit program!')
