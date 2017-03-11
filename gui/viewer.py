
"""
Image widgets for showing manga pages on fullscreen or at least scaled to
maximum size.

Created on Mon Dec 29 12:42:49 2014

@author: Christian Wichmann
"""

import os
import sys
import logging

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import Qt

from src import MangaBase


logger = logging.getLogger('MangaLoader.gui')


class ImageView(QtGui.QWidget):
    """
    Shows a widget containing a single image for a given chapter in a specified manga series.
    
    :param parent: parent widget or window
    :param base_dir: base directory for all manga series data
    :param start_with_manga: Manga object for the series that should be shown
    :param start_with_chapter: Chapter object for the chapter that should be shown
    """
    def __init__(self, parent, base_dir, start_with_manga=None, start_with_chapter=None):
        super(ImageView, self).__init__(parent)
        self.main_gui = parent
        self.base_dir = base_dir
        self.start_with_chapter = start_with_chapter
        self.start_with_manga = start_with_manga
        path_builder = MangaBase.ImageStoreManager(base_dir)
        self.image_switcher = path_builder.find_next_image(start_with_manga, start_with_chapter)
        self.create_fonts()
        self.setup_ui()
        self.set_signals_and_slots()

    #def resizeEvent(self, event):
    #    super(ImageView, self).resizeEvent(event)
    #    # handle resizing of image
    #    new_size = event.size()
    #    new_size.setWidth(new_size.width() - 125)
    #    new_size.setHeight(new_size.height() - 10)
    #    self.scaled_image = self.image.scaled(new_size, QtCore.Qt.KeepAspectRatio)
    #    self.image_label.setPixmap(self.scaled_image)

    def create_fonts(self):
        self.label_font = QtGui.QFont()
        self.label_font.setPointSize(22)

    def setup_ui(self):
        # set background color
        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.darkGray)
        self.setPalette(p)
        self.setAutoFillBackground(True)
        grid = QtGui.QGridLayout()
        # add dropdown box to chose manga series
        self.manga_choser = QtGui.QComboBox()
        # TODO: Load box with entries. From where?
        grid.addWidget(self.manga_choser, 0, 0)
        # add dropdown box to chose manga provider
        self.manga_provider = QtGui.QComboBox()
        grid.addWidget(self.manga_provider, 0, 2)
        # add previous button
        self.previous_button = QtGui.QPushButton('Previous')
        grid.addWidget(self.previous_button, 1, 0, QtCore.Qt.AlignCenter)
        # add image label
        self.image_label = QtGui.QLabel(self)
        #self.image_label.setGeometry(10, 10, 400, 100)
        path_to_image = next(self.image_switcher)
        pixmap = QtGui.QPixmap(path_to_image)
        #scaledPixmap = pixmap.scaled(self.image_label.size(), QtCore.Qt.KeepAspectRatio)
        #self.image_label.setPixmap(scaledPixmap)
        self.image_label.setPixmap(pixmap)
        self.image_label.setScaledContents(True)
        grid.addWidget(self.image_label, 1, 1, QtCore.Qt.AlignCenter | QtCore.Qt.AlignHCenter)
        # add next button
        self.next_button = QtGui.QPushButton('Next')
        grid.addWidget(self.next_button, 1, 2, QtCore.Qt.AlignCenter)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 100)
        grid.setColumnStretch(2, 0)
        self.setLayout(grid)

    def set_signals_and_slots(self):
        """Sets all signals and slots for this widget."""
        self.next_button.clicked.connect(self.on_next_image)
        self.previous_button.clicked.connect(self.on_previous_image)
        # TODO: Handle mouse clicks on image label.

    def keyPressEvent(self, event):
        """
        Handle key events for switching to next and previous page.
        """
        if event.isAutoRepeat():
            return
        # get key code and modifiers that were pressed
        modifiers = event.modifiers()
        key = event.key()
        if key == QtCore.Qt.Key_N:
            self.on_next_image()
        elif key == QtCore.Qt.Key_P:
            self.on_previous_image()
        elif key == QtCore.Qt.Key_Escape:
            self.on_next_image()
        elif key == QtCore.Qt.Key_Space:
            self.on_next_image()

    def on_next_image(self):
        try:
            path_to_image = next(self.image_switcher)
            logger.info('Switching to next image: {}.'.format(path_to_image))
            self.image_label.setPixmap(QtGui.QPixmap(path_to_image))
        except StopIteration:
            logger.warn('Reached end of manga.')
            # TODO: Show message box!
    
    def on_previous_image(self):
        logger.info('Switching to previous image.')


if __name__ == '__main__':
    pass
    #app = QtGui.QApplication(sys.argv)
    #app.setApplicationName('MangaLoader Viewer')
    #viewer_window = QtGui.QMainWindow()
    #viewer_window.setWindowState(QtCore.Qt.WindowMaximized)
    #viewer_window.setWindowTitle('MangaLoader Viewer')
    #viewer_window.setCentralWidget(ImageView(viewer_window, '..', start_with_manga='Coppelion', start_with_chapter='003'))
    #viewer_window.show()
    #sys.exit(app.exec_())
