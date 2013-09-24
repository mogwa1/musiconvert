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
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

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
        # add trigger
        
        addDirAction = QAction(QIcon.fromTheme('document-open-folder'),
                               'Add &Directory ...', self)
        addDirAction.setShortcut('Ctrl+D')
        addDirAction.setStatusTip('Add Directory')
        # add trigger
        
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
        fileMenu.addAction(exitAction)

        toolsMenu = menubar.addMenu('&Tools')
        toolsMenu.addAction(settingsAction)

        toolbar = self.addToolBar('Toolbar')
        toolbar.addAction(addFileAction)
        toolbar.addAction(addDirAction)
        toolbar.addSeparator()
        toolbar.addAction(settingsAction)
        toolbar.addSeparator()

        fileListView = fileListWidget(self)

        self.setCentralWidget(fileListView)

        self.setGeometry(200, 200, 800, 600)
        self.setWindowTitle('MusiConvert v0.1')
        self.setWindowIcon(QIcon.fromTheme('applications-multimedia'))
        self.show()


class fileListWidget(QTreeWidget):
    def __init__(self, *args):
        super().__init__(*args)
        self.setAllColumnsShowFocus(True)
        self.setColumnCount(4)
        self.setHeaderLabels(['Filename', 'Relative Path', 'Conversion', 'Volume Gain'])
        self.setIndentation(0)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        #self.setSortingEnabled(True)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)

        items = []
        for i in range(10):
            items.append(file())

        self.addTopLevelItems(items)

        items[0].set('README.md')

        self.addTopLevelItem(file('README.md'))

    def mimeTypes(self):
        return ['application/x-qabstractitemmodeldatalist', 'text/uri-list']
       
    def dragEnterEvent(self, e):
        print(e.mimeData().formats())
        #if (e.mimeData().hasFormat('text/uri-list')):
        #    e.accept()
        #else:
        #    e.decline()
        e.accept()

    def dropEvent(self, e):
        files = [os.path.abspath(i.toLocalFile()) for i in e.mimeData().urls() if 'file' == i.scheme()]
        print(files)
        #self.addTopLevelItem(item)

        
class file(QTreeWidgetItem):
    def __init__(self, *args):
        self.abs_path = ''
        self.rel_path = ''
        self.name = ''
        if args:
            self.set(*args)
        super().__init__([self.name, 'bla', 'bla', 'bla'], 0)

    def set(self, *args):
        if len(args) == 1:
            if os.path.isfile(args[0]):
                self.abs_path, self.name = os.path.split(os.path.abspath(args[0]))
                self.abs_path = os.path.abspath(self.abs_path)
                self.rel_path = self.abs_path
        elif len(args) == 2:
            if os.path.isfile(os.path.join(args[1], args[0])):
                self.abs_path, self.name  = os.path.split(os.path.abspath(os.path.join(args[1], args[0])))
                self.rel_path = self.abs_path
            elif os.path.isfile(args[0]) and os.path.isdir(args[1]):
                self.abs_path, self.name = os.path.split(args[0])
                self.abs_path = os.path.abspath(self.abs_path)
                self.rel_path = os.path.abspath(args[1])
        elif len(args) == 3:
            if os.path.isfile(os.path.join(args[1], args[0])) and os.path.isdir(args[2]):
                self.abs_path, self.name = os.path.split(os.path.abspath(os.path.join(args[1], args[0])))
                self.rel_path = os.path.abspath(args[2])

    def exists(self):
        valid = True
        if not os.path.isfile(os.path.join(self.abs_path, self.name)):
            valid = False
        if not os.path.isdir(self.rel_path):
            valid = False
        return valid

    def __repr__(self):
        if self.exists():
            return self.name+' '+self.abs_path+' '+self.rel_path
        else:
            return ''
                



def main():
    app = QApplication(sys.argv)
    mwd = MainWindow()   
    sys.exit(app.exec_())


if __name__ == '__main__':
    mp.freeze_support()
    main()
