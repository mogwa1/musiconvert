#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  musiconvert.py, version 0.1
#  
#  Copyright 2013 Bart De Vries <devries.bart@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

import os
import sys
import multiprocessing as mp
import oxygenicons
from musiconvert_func import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.fileListView = None
        self.initUI()
        self.show()

    def initUI(self):

        # check if a default theme exists, if not load oxygen icons
        if not QIcon.hasThemeIcon('document-open'):
            QIcon.setThemeName('/')

        ############################
        #  Define actions
        ############################

        addFileAction = QAction(QIcon.fromTheme('document-open'),
                                'Add &File ...', self)
        addFileAction.setShortcut('Ctrl+F')
        addFileAction.setStatusTip('Add File')
        addFileAction.triggered.connect(self.addfile)
        
        addDirAction = QAction(QIcon.fromTheme('document-open-folder'),
                               'Add &Directory ...', self)
        addDirAction.setShortcut('Ctrl+D')
        addDirAction.setStatusTip('Add Directory')
        addDirAction.triggered.connect(self.adddir)
        
        exitAction = QAction(QIcon.fromTheme('application-exit'),
                             'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit Application')
        exitAction.triggered.connect(self.close)

        settingsAction = QAction(QIcon.fromTheme('preferences-other'),
                                 'Settings ...', self)
        settingsAction.setShortcut('Ctrl+S')
        settingsAction.setStatusTip('Settings')


        self.statusBar()


        menubar = self.menuBar()
        
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(addFileAction)
        fileMenu.addAction(addDirAction)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAction)

        toolsMenu = menubar.addMenu('&Tools')
        toolsMenu.addAction(settingsAction)

        toolbar = self.addToolBar('Toolbar')
        toolbar.addAction(addFileAction)
        toolbar.addAction(addDirAction)
        toolbar.addSeparator()
        toolbar.addAction(settingsAction)
        toolbar.addSeparator()

        self.fileListView = fileListWidget(self)

        self.setCentralWidget(self.fileListView)

        self.setGeometry(200, 200, 800, 600)
        self.setWindowTitle('MusiConvert v0.1')
        self.setWindowIcon(QIcon.fromTheme('applications-multimedia'))


    ############################
    #  Define 'slots'
    ############################
    @pyqtSlot()
    def addfile(self):
        extension = 'flac'
        items = QFileDialog.getOpenFileNames(self,
                                             'Select one or more files to open',
                                             '',
                                             '{0} files (*.{0});;All files(*.*)'.format(extension).title())
        self.fileListView.addItems([os.path.abspath(i) for i in items[0]])

    def adddir(self):
        item = QFileDialog.getExistingDirectory(self,
                                                'Select a directory to open',
                                                '',
                                                QFileDialog.ShowDirsOnly
                                                | QFileDialog.DontResolveSymlinks)
        self.fileListView.addItems(os.path.abspath(item))


class fileListWidget(QTreeWidget):
    def __init__(self, *args):
        super().__init__(*args)
        self.setAllColumnsShowFocus(True)
        self.setColumnCount(4)
        self.setHeaderLabels(['Filename', 'Relative Path', 'Conversion', 'Volume Gain'])
        self.setIndentation(0)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        #self.setSortingEnabled(True)
        #self.setDragEnabled(True)
        self.setAcceptDrops(True)

        self.informat = flac('', '')

    def mimeTypes(self):
        #return ['application/x-qabstractitemmodeldatalist', 'text/uri-list']
        return ['text/uri-list']
    
    def dragEnterEvent(self, e):
        #print(e.mimeData().formats())
        if (e.mimeData().hasFormat('text/uri-list')):
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        files = [os.path.abspath(i.toLocalFile())
                 for i in e.mimeData().urls()
                 if 'file' == i.scheme()]
        #print(files)
        self.addItems(files)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Delete:
            selected = self.selectedItems()
            if selected:
                self.deleteItems(selected)
        else:
            super().keyPressEvent(e)
        return

    def addItems(self, items):
        informat = self.informat
        # we're expecting a list, not a single string
        if isinstance(items, str):
            items = [items]
        for item in items:
            if os.path.isfile(item) and informat.istype(item):
                witem = file(item)
                self.addTopLevelItem(witem)
            if os.path.isdir(item):
                for filename in shell().getfiles(item):
                    if informat.istype(filename):
                        witem = file(filename, item)
                        self.addTopLevelItem(witem)

    def getItems(self):
        it = QTreeWidgetItemIterator(self)
        while it.value():
            yield it.value()
            it += 1

    def deleteItems(self, items):
        for i in items:
            self.takeTopLevelItem(self.indexOfTopLevelItem(i))

    def clearItems(self):
        self.clear()


class file(QTreeWidgetItem):
    def __init__(self, *args):
        super().__init__()
        self._abs_path = ''
        self._rel_path = ''
        self._gain = ''
        self._status = ''
        if args:
            self.setfile(*args)

    def setfile(self, *args):
        if len(args) == 1:
            if os.path.isfile(args[0]):
                self._abs_path = os.path.abspath(args[0])
                self._rel_path = os.path.dirname(self._abs_path)
        elif len(args) == 2:
            if os.path.isfile(args[0]) and os.path.isdir(args[1]):
                self._abs_path = os.path.abspath(args[0])
                self._rel_path = os.path.abspath(args[1])
        self.setText(0, self.name)
        self.setText(1, self._rel_path)

    def setstatus(self, value):
        if status == '' or status == 'finished':
            self._status = value
            self.setText(2, self._status)

    def setgain(self, value):
        if value == 'album' or value == 'track':
            self._gain = value
            self.setText(3, self._gain)

    def exists(self):
        valid = True
        if not os.path.isfile(self.abs_path):
            valid = False
        if not os.path.isdir(self.rel_path):
            valid = False
        return valid

    @property
    def abs_path(self):
        return self._abs_path

    @property
    def rel_path(self):
        return self._rel_path

    @property
    def status(self):
        return self._status

    @property
    def gain(self):
        return self._gain

    @property
    def name(self):
        if self.exists():
            return os.path.basename(self.abs_path)
        else:
            return '<blank>'

    def __repr__(self):
        if self.exists():
            return "file object('"+self._abs_path+"')"
        else:
            return ''

                
def main():
    app = QApplication(sys.argv)
    mwd = MainWindow()   
    sys.exit(app.exec_())


if __name__ == '__main__':
    mp.freeze_support()
    main()
