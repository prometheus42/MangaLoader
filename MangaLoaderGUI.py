#!/usr/bin/python3

import os
import sys
import logging
import logging.handlers
from os.path import expanduser

from PyQt4 import QtGui

from gui import loader


APP_NAME = 'MangaLoaderGUI'
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
    log_to_screen.setLevel(logging.WARNING)
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

def startGUI():
    logger.info('MangaLoaderGUI started.')
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    main = QtGui.QMainWindow()
    main.setWindowTitle('MangaLoader')
    # create main window and show it
    loader_window = loader.LoaderWindow(main)
    main.setCentralWidget(loader_window)
    main.show()
    sys.exit(app.exec_())
    logger.info('MangaLoaderGUI done.')


if __name__ == '__main__':
    global logger
    logger = create_logger()
    logger.info('Starting {}...'.format(APP_NAME))
    startGUI()
