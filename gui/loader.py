
"""
Graphical user interface to load manga from various sites.

Created on Mon Dec 29 13:44:49 2014

@author: Christian Wichmann
"""


import logging
import os

from PyQt4 import QtGui
from PyQt4 import QtCore

from MangaBase import Loader
from gui import viewer
from src.plugins import MangaFoxPlugin
from src.plugins import MangaParkPlugin


logger = logging.getLogger('MangaLoader.gui')


MANGA_LIST_FILE = 'manga_list.data'


class LoaderWindow(QtGui.QWidget):
    """Shows a GUI to download manga."""
    def __init__(self, parent):
        super(LoaderWindow, self).__init__(parent)
        self.main_gui = parent
        self.manga_store_path = os.getcwd()
        self.loader = Loader(MangaFoxPlugin.MangaFoxPlugin(), self.manga_store_path)
        self.manga_list = []
        self.current_chapter_list = []
        self.create_fonts()
        self.setup_ui()
        self.set_signals_and_slots()

    def create_fonts(self):
        self.label_font = QtGui.QFont()
        self.label_font.setPointSize(22)

    def setup_ui(self):
        # setup grid layout
        grid = QtGui.QGridLayout()
        grid.setSpacing(15)
        # add manga chooser
        grid.addWidget(QtGui.QLabel('Load manga: '), 0, 0)
        grid.addWidget(self.buildMangaComboBox(), 0, 1, 1, 2)
        self.update_list_button = QtGui.QPushButton('Update...')
        grid.addWidget(self.update_list_button, 0, 3)
        # add chapter chooser
        grid.addWidget(QtGui.QLabel('From chapter: '), 1, 0)
        self.chapter_begin = QtGui.QSpinBox()
        self.chapter_begin.setValue(1)
        self.chapter_begin.setMinimum(1)
        self.chapter_begin.setMaximum(1000)
        self.chapter_begin.setSingleStep(1)
        grid.addWidget(self.chapter_begin, 1, 1)
        grid.addWidget(QtGui.QLabel('until chapter: '), 1, 2)
        self.chapter_end = QtGui.QSpinBox()
        self.chapter_end.setValue(10)
        self.chapter_end.setMinimum(1)
        self.chapter_end.setMaximum(1000)
        self.chapter_end.setSingleStep(1)
        grid.addWidget(self.chapter_end, 1, 3)
        # add directory chooser
        grid.addWidget(QtGui.QLabel('Into directory: '), 2, 0)
        self.directory_button = QtGui.QPushButton(self.manga_store_path)
        grid.addWidget(self.directory_button, 2, 1, 1, 3)
        # add options
        grid.addWidget(QtGui.QLabel('Create zipped CBZ files: '), 3, 0)
        self.do_zip_checkbox = QtGui.QCheckBox() 
        grid.addWidget(self.do_zip_checkbox, 3, 1, 1, 3)
        # add progressbar
        self.loader_progress = QtGui.QProgressBar()
        grid.addWidget(self.loader_progress, 4, 0, 1, 4)
        # add load button
        self.load_button = QtGui.QPushButton('Load...')
        grid.addWidget(self.load_button, 5, 0, QtCore.Qt.AlignLeft)
        # add show button
        self.show_button = QtGui.QPushButton('Show...')
        grid.addWidget(self.show_button, 5, 1, QtCore.Qt.AlignLeft)
        # add quit button
        self.quit_button = QtGui.QPushButton('Quit')
        grid.addWidget(self.quit_button, 5, 3, QtCore.Qt.AlignRight)
        self.setLayout(grid)

    def buildMangaComboBox(self):
        self.mangaComboBox = QtGui.QComboBox()
        completer = QtGui.QCompleter(self)
        completer.setCompletionMode(QtGui.QCompleter.UnfilteredPopupCompletion)  # PopupCompletion
        self.mangaComboBox.setCompleter(completer)
        # get list of mangas from Loader and populate combo box
        self.manga_list = self.loader.get_all_manga(update=False)
        for manga in self.manga_list:
            self.mangaComboBox.addItem(manga.name, userData=manga)
        return self.mangaComboBox

    def set_signals_and_slots(self):
        """Sets all signals and slots for this widget."""
        self.quit_button.clicked.connect(self.main_gui.close)
        self.directory_button.clicked.connect(self.on_choose_directory)
        self.load_button.clicked.connect(self.on_load_manga)
        self.mangaComboBox.currentIndexChanged.connect(self.on_update_chapter_fields)
        self.update_list_button.clicked.connect(self.on_update_manga_list)
        self.show_button.clicked.connect(self.on_show_manga)

    @QtCore.pyqtSlot()
    def on_update_manga_list(self):
        # TODO Load mangas in background and update combo box regularly?!
        self.manga_list = self.loader.get_all_manga(update=True)
        # load combo box with items from manga list
        for manga in self.manga_list:
            self.mangaComboBox.addItem(manga.name, userData=manga)

    @QtCore.pyqtSlot()
    def on_choose_directory(self):
        directory = QtGui.QFileDialog.getExistingDirectory(self, 'Select directory to save mangas...')
        self.manga_store_path = directory
        self.directory_button.setText(self.manga_store_path)
        self.loader.store_directory = self.manga_store_path
        logger.debug('Choosen directory: "{}".'.format(directory))

    @QtCore.pyqtSlot()
    def on_load_manga(self):
        # check whether the input fields are valid
        start_chapter = self.chapter_begin.value()
        end_chapter = self.chapter_end.value()
        chosen_manga_name = self.mangaComboBox.currentText()
        if end_chapter < start_chapter:
            QtGui.QMessageBox.warning(self, 'Error', 'Last chapter is smaller than first chapter!')
            return
        if not chosen_manga_name:
            QtGui.QMessageBox.warning(self, 'Error!', 'No manga was chosen.')
            return
        logger.info('Loading loader...')
        # setup progress bar for loading of chapters
        self.loader_progress.setRange(start_chapter - 1, end_chapter)
        self.loader_progress.setValue(start_chapter - 1)
        # enforce event processing to update progress bar
        QtGui.QApplication.processEvents()
        logger.info('Loading chapters {} - {}'.format(str(start_chapter), str(end_chapter)))
        for i in range(start_chapter, end_chapter + 1):
            # find chapter object
            current_chapter = None
            for c in self.current_chapter_list:
                if c.chapterNo == i:
                    current_chapter = c
                    break
            if current_chapter:
                self.loader.handle_chapter(current_chapter)
                # set new value for progress bar and enforce event processing
                self.loader_progress.setValue(i)
                QtGui.QApplication.processEvents()
                if self.do_zip_checkbox.checkState():
                    self.loader.zip_chapter(self.mangaComboBox.itemData(self.mangaComboBox.currentIndex()),
                                            current_chapter)
            else:
                logger.error('Could not find chapter object!')

    @QtCore.pyqtSlot()
    def on_update_chapter_fields(self):
        chosen_manga = self.mangaComboBox.itemData(self.mangaComboBox.currentIndex())
        logger.debug('Combo box changed to {}.'.format(chosen_manga))
        self.current_chapter_list = self.loader.get_all_chapters(chosen_manga)
        # set max and min for input fields
        chapter_number_list = [x.chapterNo for x in self.current_chapter_list]
        if chapter_number_list:
            maximum = max(chapter_number_list)
            minimum = min(chapter_number_list)
            self.chapter_begin.setMinimum(minimum)
            self.chapter_begin.setMaximum(maximum)
            self.chapter_end.setMinimum(minimum)
            self.chapter_end.setMaximum(maximum)
            logger.debug('Found chapter min and max: {} - {}'.format(minimum, maximum))

    @QtCore.pyqtSlot()
    def on_show_manga(self):
        logger.info('Show current manga chapter in viewer...')
        viewer_window = QtGui.QMainWindow()
        viewer_window.setWindowState(QtCore.Qt.WindowMaximized)
        viewer_window.setWindowTitle('MangaLoader Viewer')
        chosen_manga = self.mangaComboBox.itemData(self.mangaComboBox.currentIndex())
        self.current_chapter_list = self.plugin.load_chapter_list(chosen_manga)
        chosen_chapter = None
        for c in self.current_chapter_list:
            if c.chapterNo == self.chapter_begin.value():
                chosen_chapter = c
                break
        if chosen_chapter:
            image_view = viewer.ImageView(viewer_window, self.manga_store_path,
                                          start_with_manga=chosen_manga, start_with_chapter=chosen_chapter)
            viewer_window.setCentralWidget(image_view)
            viewer_window.show()
