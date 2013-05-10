#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  musiconvert_gui.py, version 0.1
#  
#  Copyright 2012 Bart De Vries <devries.bart@gmail.com>
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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals
import wx
import wx.lib.wordwrap
import wx.lib.newevent
import os
import cPickle as pickle
import multiprocessing as mp
import threading
import tangoart as ta
import musiconvert_func as mc
import musiconvert_gui_settings as mcs
import datetime

###############################################
# Custom Events for multithreading encoding
# and Custum IDs for buttons etc.
###############################################

(EncResultEvent, EVT_ENC_RESULT) = wx.lib.newevent.NewEvent()
(EncStopEvent,   EVT_ENC_STOP)   = wx.lib.newevent.NewEvent()
ID_START=wx.NewId()
ID_LOAD=wx.NewId()
ID_OUTFOLDER=wx.NewId()

###############################################
# Utility functions and classes
###############################################

def time2str(td):
    timestr = ''
    if td.days//365:
        timestr += '{} yrs'.format(td.days//365)
    if td.days:
        timestr += ' {} days'.format(td.days%365)
    if td.seconds//3600:
        timestr += ' {} hrs'.format(td.seconds//3600)
    if (td.seconds%3600)//60:
        timestr += ' {} min'.format((td.seconds%3600)//60)
    if not timestr or td.seconds%60:
        timestr += ' {} sec'.format(td.seconds%60)
    return timestr.strip()


###############################################
# Main Window
###############################################

class MainWindow(wx.Frame):
    def __init__(self, parent, appsettings, settings):
        # class to keep conversion settings
        self.settings = settings
        # class to keep app settings
        self.appsettings = appsettings
        # Create class to handle events
        self.eventhdl = EventHandler(self, self.appsettings, self.settings)
        # Initialize widgets
        self._init_ctrls(parent)
    
    def _init_ctrls(self, prnt):
        wx.Frame.__init__(self, parent=prnt, title='MusiConvert v0.1',
                          size=self.appsettings.framesize)
        
        wx.ArtProvider.Push(ta.TangoArtProvider('tango-icon-theme-0.8.90'))
        self.toolbar = self.CreateToolBar(style=wx.TB_NODIVIDER|wx.TB_FLAT)
        
        self.text1 = wx.StaticText(self.toolbar, label='Input:')
        self.combobox1 = wx.ComboBox(self.toolbar, value=self.settings.inname,
                                     style=wx.CB_READONLY|wx.CB_DROPDOWN,
                                     choices=self.settings.codecnames)

        self.text2 = wx.StaticText(self.toolbar, label='Output: ')
        self.combobox2 = wx.ComboBox(self.toolbar, value=self.settings.outname,
                                     style=wx.CB_READONLY|wx.CB_DROPDOWN,
                                     choices=self.settings.codecnames)
        self.labeloutdir = wx.StaticText(self.toolbar, label='Output dir: ')
        self.textoutdir = wx.TextCtrl(self.toolbar, value=self.settings.outdir,
                                      size=(200,-1))
        
        tbsize = (22,22)
        add_bmp = wx.ArtProvider.GetBitmap(ta.ART_LIST_ADD, wx.ART_TOOLBAR, tbsize)
        remove_bmp = wx.ArtProvider.GetBitmap(ta.ART_LIST_REMOVE, wx.ART_TOOLBAR, tbsize)
        clear_bmp = wx.ArtProvider.GetBitmap(ta.ART_EDIT_CLEAR, wx.ART_TOOLBAR, tbsize)
        start_bmp = wx.ArtProvider.GetBitmap(ta.ART_MEDIA_PLAYBACK_START, wx.ART_TOOLBAR, tbsize)
        stop_bmp =  wx.ArtProvider.GetBitmap(ta.ART_MEDIA_PLAYBACK_STOP, wx.ART_TOOLBAR, tbsize)
        folder_bmp = wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_TOOLBAR, tbsize)
        preferences_bmp = wx.ArtProvider.GetBitmap(ta.ART_PREFERENCES, wx.ART_TOOLBAR, tbsize)
        self.toolbar.SetToolBitmapSize(tbsize)
        
        self.toolbar.AddLabelTool(id=wx.ID_ADD, label='Add', bitmap=add_bmp, 
                                  bmpDisabled=wx.NullBitmap, shortHelp='Add Directory', 
                                  longHelp='Add Directory')
        self.toolbar.AddLabelTool(id=wx.ID_REMOVE, label='Remove', bitmap=remove_bmp, 
                                  bmpDisabled=wx.NullBitmap, shortHelp='Remove Selected Files', 
                                  longHelp='Remove Selected Files')
        self.toolbar.AddLabelTool(id=wx.ID_CLEAR, label='Remove All', 
                                  bitmap=clear_bmp, bmpDisabled=wx.NullBitmap, 
                                  shortHelp='Remove All', longHelp='Remove All')
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(id=wx.ID_PREFERENCES, label='Preferences', bitmap=preferences_bmp, 
                                  bmpDisabled=wx.NullBitmap, shortHelp='Preferences', 
                                  longHelp='Open Preferences Dialog')        
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(id=ID_START, label='Start', bitmap=start_bmp, 
                                  bmpDisabled=wx.NullBitmap, shortHelp='Start', 
                                  longHelp='Start Encoding')
        self.toolbar.AddLabelTool(id=wx.ID_STOP, label='Stop', bitmap=stop_bmp, 
                                  bmpDisabled=wx.NullBitmap, shortHelp='Stop', 
                                  longHelp='Stop Encoding')
        self.toolbar.AddSeparator()
        self.toolbar.AddControl(control=self.text1)
        self.toolbar.AddControl(control=self.combobox1)
        self.toolbar.AddSeparator()
        self.toolbar.AddControl(control=self.text2)
        self.toolbar.AddControl(control=self.combobox2)
        self.toolbar.AddSeparator()
        self.toolbar.AddControl(control=self.labeloutdir)
        self.toolbar.AddControl(control=self.textoutdir)
        self.toolbar.AddLabelTool(id=ID_OUTFOLDER, label='Output Folder', bitmap=folder_bmp, 
                                  bmpDisabled=wx.NullBitmap, shortHelp='Select Output Folder', 
                                  longHelp='Select Output Folder')

        self.toolbar.Realize()
        
        self.toolbar.EnableTool(wx.ID_STOP, False)
        
        self.statusbar = self.CreateStatusBar() # A Statusbar in the bottom of the window
        self.statusbar.SetFieldsCount(3)
        self.statusbar.SetStatusWidths([-5,-2,-3])
        
        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.panel, proportion=1, flag=wx.EXPAND|wx.ALL)

        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.listctrl = MyListControl(self.panel, self.appsettings, 
                                      self.settings, self.eventhdl)
        self.sizer1.Add(self.listctrl, proportion = 1, flag=wx.EXPAND|wx.ALL, border=0)

        self.gauge = wx.Gauge(self, range=100)
        self.sizer1.Add(self.gauge, flag=wx.ALL|wx.EXPAND, border=5)


        self.panel.SetSizerAndFit(self.sizer1)


        # Setting up the menu.
        self.filemenu= wx.Menu()
        self.menuAddDirectory = self.filemenu.Append(wx.ID_ADD,'Add &Directory ...',
                                                     ' Add directory with input files')
        self.menuRemoveSelected = self.filemenu.Append(wx.ID_REMOVE,'&Remove Selected Files',
                                                     ' Remove selected input files from list')
        self.menuClearList = self.filemenu.Append(wx.ID_CLEAR,'Remove &All Files',
                                                     ' Remove all input files from list')
        self.filemenu.AppendSeparator()
        self.menuOutFolder = self.filemenu.Append(ID_OUTFOLDER,'Select &Output Folder ...',
                                                  ' Select Output Folder')
        self.filemenu.AppendSeparator()
        self.menuLoadSettings = self.filemenu.Append(ID_LOAD,'&Load Settings ...',
                                                     ' Load settings file')
        self.menuSaveSettings = self.filemenu.Append(wx.ID_SAVE,'&Save Settings',
                                                     ' Save settings file')
        self.menuSaveAsSettings = self.filemenu.Append(wx.ID_SAVEAS,'Save Settings &As ...',
                                                     ' Save settings file')
        self.filemenu.AppendSeparator()
        self.menuExit = self.filemenu.Append(wx.ID_EXIT,'E&xit',
                                             ' Terminate the program')
        self.toolsmenu= wx.Menu()
        self.menuStartEncoding = self.toolsmenu.Append(ID_START,'Start &Encoding',
                                                    ' Start Encoding')
        self.menuStopEncoding = self.toolsmenu.Append(wx.ID_STOP,'&Stop Encoding',
                                                    ' Stop Encoding')
        self.toolsmenu.AppendSeparator()
        self.menuPreferences = self.toolsmenu.Append(wx.ID_PREFERENCES,'&Preferences ...',
                                                     ' Set preferences')

        self.menuStopEncoding.Enable(False)
      
        self.helpmenu= wx.Menu()
        self.menuAbout= self.helpmenu.Append(wx.ID_ABOUT, '&About',
                                             ' Information about this program')

        # Creating the menubar.
        self.menuBar = wx.MenuBar()
        self.menuBar.Append(self.filemenu,'&File') # Adding the 'filemenu' to the MenuBar
        self.menuBar.Append(self.toolsmenu,'&Tools') # Adding the 'toolsmenu' to the MenuBar
        self.menuBar.Append(self.helpmenu,'&Help') # Adding the 'helpmenu' to the MenuBar

        self.SetMenuBar(self.menuBar)  # Adding the MenuBar to the Frame content.


        # Events.
        self.Bind(wx.EVT_MENU, self.eventhdl.OnAddDirectory, self.menuAddDirectory)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnRemoveSelected, self.menuRemoveSelected)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnClearList, self.menuClearList)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnOutFolderBtn, self.menuOutFolder)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnLoadSettings, self.menuLoadSettings)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnSaveSettings, self.menuSaveSettings)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnSaveAsSettings, self.menuSaveAsSettings)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnPreferences, self.menuPreferences)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnExit, self.menuExit)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnAbout, self.menuAbout)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnStartEncoding, self.menuStartEncoding)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnStopEncoding, self.menuStopEncoding)
        self.Bind(wx.EVT_CLOSE, self.eventhdl.OnExit)

        self.Bind(wx.EVT_COMBOBOX, self.eventhdl.OnInputSelection, self.combobox1)
        self.Bind(wx.EVT_COMBOBOX, self.eventhdl.OnOutputSelection, self.combobox2)

        self.Bind(wx.EVT_TEXT, self.eventhdl.OnOutFolderText, self.textoutdir)

        self.Bind(wx.EVT_LIST_KEY_DOWN, self.listctrl.OnKeyPressed, self.listctrl)

        self.Bind(EVT_ENC_RESULT, self.eventhdl.OnEncodingResult)

        self.SetSizer(self.sizer)
        self.Show()


class MyListControl(wx.ListCtrl):
    def __init__(self, parent, appsettings, settings, evthandler):
        self.appsettings = appsettings
        self.settings = settings
        self.evthandler = evthandler
        self.parent = parent
        wx.ListCtrl.__init__(self, parent, style=wx.LC_REPORT)
        
        self.InsertColumn(0, 'Relative Path')
        self.InsertColumn(1, 'File')
        self.InsertColumn(2, 'Conversion')
        self.InsertColumn(3, 'ReplayGain')
        for i in xrange(self.GetColumnCount()):
            self.SetColumnWidth(i, self.appsettings.columnwidth[i])
        self.populate()
                             
    def populate(self):
        self.DeleteAllItems()
        self.files = {}
        index=0
        for file, indir in zip(self.settings.files, self.settings.indir):
            relpath = os.path.relpath(os.path.dirname(file), indir)
            self.InsertStringItem(index, relpath)
            self.SetStringItem(index, 1, os.path.basename(file))
            self.SetItemData(index, id(file))
            self.files[id(file)] = file
            index += 1
            
    def resetstatus(self, i = None):
        if i:
            self.SetStringItem(i, 2, '')
            self.SetStringItem(i, 3, '')
        else:
            for i in xrange(self.GetItemCount()):
                self.SetStringItem(i, 2, '')
                self.SetStringItem(i, 3, '')
    
    def getselecteditems(self):
        """    
        Gets the selected items for the list control.
        Selection is returned as a list of selected indices,
        low to high, and a list of matching filenames.
        """
        selection = []
        filelist = []
        index = self.GetFirstSelected()
        if index == -1:
            return None, None
        selection.append(index)
        filelist.append(self.files[self.GetItemData(index)])
        while len(selection) != self.GetSelectedItemCount():
            index = self.GetNextSelected(index)
            selection.append(index)
            filelist.append(self.files[self.GetItemData(index)])
        return selection, filelist
    
    def removeselected(self):
        _, filelist = self.getselecteditems()
        if filelist:
            self.settings.removefiles(filelist)
            #self.populate()
    
    def finditem(self, filename):
        for key, value in self.files.items():
            if value == filename:
                return self.FindItemData(-1, key)
        return None
        
    def finddiritems(self, dirname):
        files = []
        for key, value in self.files.items():
            if os.path.abspath(dirname) in os.path.abspath(value):
                files.append(self.FindItemData(-1,key))
        return files
        
    def OnKeyPressed(self, e):
        keycode = e.GetKeyCode()
        if keycode == wx.WXK_DELETE:
            self.removeselected()


class EventHandler(object):
    def __init__(self, parent, appsettings, settings):
        self.frame = parent
        self.appsettings = appsettings
        self.settings = settings
        self.pool = EncodePool(self.frame)

    def OnAbout(self,e):
        # Create a message dialog box
        info = wx.AboutDialogInfo()
        info.Name = 'MusiConvert'
        info.Version = '0.1'
        info.Copyright = '(C) 2012 Bart De Vries'
        info.Description = wx.lib.wordwrap.wordwrap(
            'This is a GUI interface to the command line tool \'musiconvert\', '
            'which can convert all audio files in a directory into another audio '
            'format, including tagging (also album art) and volume normalization.',
            350, wx.ClientDC(self.frame))
        info.Developers = ['Bart De Vries']
        info.License = 'GNU General Public License v3 or higher'
        wx.AboutBox(info)


    def OnExit(self,e):
        self.appsettings.framesize = self.frame.GetSize()
        self.appsettings.columnwidth = []
        for i in xrange(self.frame.listctrl.GetColumnCount()):
            self.appsettings.columnwidth.append(
                            self.frame.listctrl.GetColumnWidth(i))
        self.appsettings.save()
        self.settings.save()
        self.frame.Destroy()

    def OnLoadSettings(self,e):
        dlg = wx.FileDialog(
            self.frame, message="Load Settings File",
            defaultDir=os.path.dirname(self.settings.currentfile), 
            defaultFile=os.path.basename(self.settings.currentfile),
            wildcard='Settings files (*.ini)|*.ini|'
                     'All files (*.*)|*.*',
            style=wx.OPEN
            )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            if self.settings.load(paths[0]):
                self.appsettings.convertfile = paths[0]
        dlg.Destroy()

    def OnSaveSettings(self,e):
        self.settings.save()
        
    def OnSaveAsSettings(self,e):
        dlg = wx.FileDialog(
            self.frame, message="Save Settings File As",
            defaultDir=os.path.dirname(self.settings.currentfile), 
            defaultFile=os.path.basename(self.settings.currentfile),
            wildcard='Settings files (*.ini)|*.ini|'
                     'All files (*.*)|*.*',
            style=wx.SAVE
            )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            if self.settings.save(paths[0]):
                self.appsettings.convertfile = paths[0]
        dlg.Destroy()
        
    def OnPreferences(self,e):
        dlg = mcs.PreferencesDialog(parent=self.frame, title='Preferences',
                                    settings=self.settings, size=(500,500),
                                    selectedpage=self.appsettings.optionsselectedpage,
                                    style=wx.RESIZE_BORDER|wx.DEFAULT_DIALOG_STYLE)
        if (dlg.ShowModal() == wx.ID_OK): # Shows it
            self.settings.lamepath = dlg.lamepath
            self.settings.flacpath = dlg.flacpath
            self.settings.metaflacpath = dlg.metaflacpath
            self.settings.mp3gainpath = dlg.mp3gainpath
            self.settings.overwrite = dlg.overwrite
            self.settings.flat = dlg.flat
            self.settings.gain = dlg.gain
            if dlg.manualprocesses:
                self.settings.nrprocesses = dlg.processspinctrl.GetValue()
            else:
                self.settings.nrprocesses = None
            self.settings.lamebitrate = dlg.lamebitrate
            self.settings.lameextraopts = dlg.lameextraopts
            self.settings.lamevbr = dlg.combovbr.GetValue()
            self.settings.lamecbr = dlg.combocbr.GetValue()
            self.settings.lameabr = dlg.spinabr.GetValue()
            dlg._getlistdata()
            self.settings.tagfields = dlg.tagfields
            self.settings.id3mapping = dlg.id3mapping

        self.appsettings.optionsselectedpage = dlg.listbook.GetSelection()
        dlg.Destroy() # finally destroy it when finished.
        
    def OnInputSelection(self,e):
        if self.settings.files:
            msg = 'Changing the input format will empty the current '+\
                  'list of selected files. Do you want to proceed?'
            dlg = wx.MessageDialog(self.frame, message=msg, 
                                   style=wx.OK|wx.CANCEL|wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_CANCEL:
                dlg.Destroy()
                self.frame.combobox1.SetValue(self.settings.inname)
                return
            dlg.Destroy()
        self.settings.setinformat(e.GetString())
        self.settings.resetlist()
        self.frame.listctrl.populate()

    def OnOutputSelection(self,e):
        self.settings.setoutformat(e.GetString())

    def OnAddDirectory(self,e):
        dlg = wx.DirDialog(
            self.frame, message="Add directory containing input files",
            defaultPath=self.appsettings.adddirectory)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.settings.addfiles(path)
            self.frame.listctrl.populate()
            self.appsettings.adddirectory = path
        dlg.Destroy()

    def OnRemoveSelected(self, e):
        self.frame.listctrl.removeselected()

    def OnClearList(self,e):
        self.settings.resetlist()
        self.frame.listctrl.populate()

    def OnOutFolderBtn(self, e):
        dlg = wx.DirDialog(
            self.frame, message="Select output directory",
            defaultPath=self.settings.outdir)
        if dlg.ShowModal() == wx.ID_OK:
            path = os.path.abspath(dlg.GetPath())
            self.settings.outdir = path
            self.frame.textoutdir.ChangeValue(path)
        dlg.Destroy()

    def OnOutFolderText(self, e):
        path = os.path.abspath(e.GetString())
        self.settings.outdir = path
        
    def OnStartEncoding(self, e):
        if not self.settings.externalcodecsexist():
            msg = 'Please set the paths to the appropriate codecs.\n' +\
                  'At least one of them is missing.'
            dlg = wx.MessageDialog(self.frame, message=msg, 
                                   style=wx.OK|wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        self.frame.listctrl.resetstatus()
        self.frame.menuStartEncoding.Enable(False)
        self.frame.toolbar.EnableTool(ID_START, False)
        self.frame.menuStopEncoding.Enable(True)
        self.frame.toolbar.EnableTool(wx.ID_STOP, True)
        self.progresscnt = 0
        self.totalcnt = len(self.settings.files)
        if self.settings.gain == 'album':
            self.totalcnt += len(self.settings.ingaindirs)
        self.frame.statusbar.SetStatusText('Processed: 0/{}'.format(self.totalcnt),1)
        self.frame.statusbar.SetStatusText('Time remaining:', 2)
        self.frame.gauge.SetRange(self.totalcnt)
        encodeopts = self.settings.getencodeoptions()
        self.thread = threading.Thread(target=self.pool.run, args=encodeopts)
        self.thread.start()
        
    def OnEncodingResult(self, e):
        listctrl = self.frame.listctrl
        if 'ok' in e.status:
            self.progresscnt += 1
            remtime = datetime.timedelta(seconds=e.runtime.total_seconds() 
                            * ((self.totalcnt-self.progresscnt)/self.progresscnt))
            msg1 = 'Processed: {}/{}'.format(self.progresscnt, 
                                             self.totalcnt)
            msg2 = 'Time remaining: {}'.format(time2str(remtime))
            self.frame.statusbar.SetStatusText(msg1, 1)
            self.frame.statusbar.SetStatusText(msg2, 2)
            self.frame.gauge.SetValue(self.progresscnt)
            if 'albumgain' in e.status:
                items = listctrl.finddiritems(e.dirname)
                for item in items:
                    listctrl.SetStringItem(item, 3, 'album gain')
            elif 'exists' in e.status:
                item = listctrl.finditem(e.filename)
                listctrl.SetStringItem(item, 2, 'already exists')
                listctrl.SetItemTextColour(item, wx.RED)
                if 'trackgain' in e.status:
                    listctrl.SetStringItem(item, 3, 'skipped')
            else:
                item = listctrl.finditem(e.filename)
                listctrl.SetStringItem(item, 2, 'done')
                if 'trackgain' in e.status:
                    listctrl.SetStringItem(item, 3, 'track gain')
        elif e.status == 'finished':
            msg = 'Finished transcoding.\nConverted {} files in {}.'.format(
                        len(self.settings.files), time2str(e.runtime))
            dlg = wx.MessageDialog(self.frame, message=msg, style=wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.OnEndEncoding()
        elif e.status == 'aborted':
            msg = 'Transcoding aborted.\nSo far, {} files of {} have ' \
                  'been transcoded in {}.'.format(self.progresscnt, 
                  self.totalcnt, time2str(e.runtime))
            dlg = wx.MessageDialog(self.frame, message=msg, style=wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            self.OnEndEncoding()
        
    def OnStopEncoding(self, e):
        evt = EncStopEvent()
        wx.PostEvent(self.pool, evt)

    def OnEndEncoding(self):
        self.frame.statusbar.SetStatusText('',1)
        self.frame.statusbar.SetStatusText('',2)
        self.frame.menuStartEncoding.Enable(True)
        self.frame.toolbar.EnableTool(ID_START, True)
        self.frame.menuStopEncoding.Enable(False)
        self.frame.toolbar.EnableTool(wx.ID_STOP, False)
        self.frame.gauge.SetValue(0)


class AppSettings(object):
    def __init__(self, filename='musiconvert.ini'):
        self.filename = filename
        # set defaults in case the settings file doesn't exist
        self.framesize = (770,670)
        self.columnwidth = [180, 330, 110, 110]
        self.convertfile = 'settings.ini'
        self.adddirectory = '.'
        self.optionsselectedpage = 0
        # load settings file
        if os.path.isfile(filename):
            self.load(filename)

    def save(self, filename=''):
        if filename == '':
            filename = self.filename
        with open(filename, 'wb') as appsetfile:
            pickle.dump(self.__dict__, appsetfile)
            
    def load(self, filename='musiconvert.ini'):
        if os.path.isfile(filename):
            with open(filename, 'rb') as appsetfile:
                tmp_dict = pickle.load(appsetfile)
            self.__dict__.update(tmp_dict)
            self.filename = filename


class ConvertSettings(object):
    """
    Main class containing the settings for the different codecs and the
    selected input (and output) files.  
    
    In order to implement a new codec/audioformat: 
      - implement a subclass of 'audioformat'
      - add name to self.codecnames
      - add the needed settings variables to the self.__init__ constructor
      - implement a GUI settings tab which sets those variables
      - add the check for external codecs to self.externalcodecsexist
    """
    def __init__(self, filename='settings.ini'):
        self.currentfile = os.path.abspath(filename)
        # set defaults in case settings file doesn't exist
        self.inname = 'flac'
        self.outname = 'mp3'
        # general/file/dir settings
        self.files = []
        self.indir = []
        self.ingaindirs = []
        self.ingainrefdir = []
        self.outdir = 'C:\\Personal\\convertor\\out'
        self.recursive = True
        self.flat = False
        self.gain = 'album'
        self.overwrite = True
        self.nrprocesses = None
        self.tagfields = ['ARTIST', 'TITLE', 'ALBUM', 'DATE', 
                          'TRACKNUMBER', 'TRACKTOTAL', 'DISCNUMBER', 
                          'DISCTOTAL', 'ALBUMARTIST', 'PERFORMER', 
                          'COMPOSER']
        
        # flac settings
        self.flacpath = 'C:\\Program Files (x86)\\FLAC\\flac.exe'
        self.metaflacpath = 'C:\\Program Files (x86)\\FLAC\\metaflac.exe'

        # mp3/lame settings
        self.mp3gainpath = 'C:\\Program Files (x86)\\MP3Gain\\mp3gain.exe'
        self.lamepath = 'C:\\Program Files (x86)\\Lame\\lame.exe'
        self.lamebitrate = '-V2'
        self.lamevbr = 'V2 (~ 190 kbit/s)'
        self.lamecbr = '192 kbit/s'
        self.lameabr = 192
        self.lameextraopts = ''
        self.id3mapping = { 'ARTIST'      : 'TPE1',
                            'TITLE'       : 'TIT2',
                            'ALBUM'       : 'TALB',
                            'DATE'        : 'TYER',
                            'TRACKNUMBER' : 'TRCK',
                            'TRACKTOTAL'  : 'TXXX TOTALTRACKS',
                            'DISCNUMBER'  : 'TPOS',
                            'DISCTOTAL'   : 'TXXX TOTALDISCS',
                            'ALBUMARTIST' : 'TPE2',
                            'PERFORMER'   : 'TXXX PERFORMER',
                            'COMPOSER'    : 'TCOM' }
                            
        # load settings file
        if os.path.isfile(filename):
            self.load(filename)
        self.codecnames = ('flac', 'mp3',)

    def save(self, filename=''):
        if filename == '':
            filename = self.currentfile
        with open(filename, 'wb') as setfile:
            pickle.dump(self.__dict__, setfile)
        return 1

    def load(self, filename='settings.ini'):
        if os.path.isfile(filename):
            with open(filename, 'rb') as setfile:
                tmp_dict = pickle.load(setfile)
            self.__dict__.update(tmp_dict)
            self.currentfile = filename
        return 1
 
    def _getformat(self, name):
        """
        This method calls the right audioformat class for the given 
        name, which is the name used in the GUI (which can be different
        from e.g. the file extension).
        """
        if name == 'mp3':
            lameopts = self.lamebitrate + ' ' + self.lameextraopts 
            audioformat = mc.mp3(self.lamepath, self.mp3gainpath, 
                                 lameopts)
        elif name == 'flac':
            audioformat = mc.flac(self.flacpath, self.metaflacpath)
        return audioformat

    def externalcodecsexist(self):
        if 'mp3' in (self.inname, self.outname):
            if (not os.path.exists(self.lamepath) or
                not os.path.exists(self.mp3gainpath)):
                return False
        elif 'flac' in (self.inname, self.outname):
            if (not os.path.exists(self.flacpath) or
                not os.path.exists(self.metaflacpath)):
                return False
        return True

    def setinformat(self, name):
        if name in self.codecnames:
            self.inname = name
        
    def setoutformat(self, name):
        if name in self.codecnames:
            self.outname = name

    def addfiles(self, path):
        inext = self._getformat(self.inname).extension
        newfiles, _ = mc.getinputfilelists(path, inext, 
                                           self.recursive)
        newdir = [path for i in newfiles]
        self.files += newfiles
        self.indir += newdir
        
        newgaindirs = mc.getdirlist(path, inext, self.recursive)
        newrefdir = [path for i in newgaindirs]
        self.ingaindirs += newgaindirs
        self.ingainrefdir += newrefdir
        
    def removefiles(self, filelist):
        # part one: remove files
        indices = []
        for i in filelist:
            indices.append(self.files.index(os.path.abspath(i)))
        indices.sort(reverse=True)
        for index in indices:
            del self.files[index]
            del self.indir[index]
        
        # part two: remove directories for album gain if no input
        # files from those directories remain
        remgaindir = []
        for i in xrange(len(self.ingaindirs)):
            found = False
            for file in self.files:
                if self.ingaindirs[i] in file:
                    found = True
            if not found:
                remgaindir.append(i)
        remgaindir.sort(reverse=True)
        for index in remgaindir:
            del self.ingaindirs[index]
            del self.ingainrefdir[index]
                    
    def resetlist(self):
        self.files = []
        self.indir = []
        self.ingaindirs = []
        self.ingainrefdir = []

    def getencodeoptions(self):
        options = []
        gainoptions = []
        informat = self._getformat(self.inname)
        outformat = self._getformat(self.outname)
        trackgain = True if self.gain == 'track' else False
        albumgain = True if self.gain == 'album' else False
        for infile, indir in zip(self.files, self.indir):
            outfile = mc.shell().replacepath(infile, indir,
                                             self.outdir, self.flat)
            outfile = mc.shell().replaceextension(outfile, 
                                                  outformat.extension)
            options.append([infile, outfile, informat, outformat,
                            True, self.overwrite, trackgain])
        if albumgain:
            for indir, inrefdir in zip(self.ingaindirs, self.ingainrefdir):
                outgaindir = mc.shell().replacepath(indir, 
                                                    inrefdir, 
                                                    self.outdir, 
                                                    self.flat)
                gainoptions.append([indir, outgaindir, outformat])
        return options, gainoptions, informat, outformat, self.nrprocesses
        
        
class EncodePool(wx.EvtHandler):
    def __init__(self, win):
        self.win = win
        wx.EvtHandler.__init__(self)
        self.Bind(EVT_ENC_STOP, self.OnStop)
        self.keeprunning = False
        
    def run(self, options, options_album, informat, outformat, nrprocesses):
        # create temporary directory for intermediate files
        # i.e. image files etc.
        with mc.temporary_dir() as tempdir:
            # first add temporary directory to options
            for i in options:
                i.append(tempdir)

            # keep track of time for progress
            starttime = datetime.datetime.today()
            self.keeprunning = True
            if nrprocesses:
                pool = mp.Pool(processes = nrprocesses)
            else:
                pool = mp.Pool()
            results = pool.imap_unordered(mc.encode_process_star, 
                                          options)
            pool.close()
    
            for result in results:
                timediff = datetime.datetime.today() - starttime
                evt = EncResultEvent(filename = result[0], 
                                     runtime = timediff, 
                                     status = result[1])
                wx.PostEvent(self.win, evt)
                if not self.keeprunning:
                    pool.terminate()
                    pool.join()
                    evt2 = EncResultEvent(runtime = timediff, status = 'aborted')
                    wx.PostEvent(self.win, evt2)
                    return
            pool.join()
            
            if options_album:
                if nrprocesses:
                    pool = mp.Pool(processes = nrprocesses)
                else:
                    pool = mp.Pool()
                results = pool.imap_unordered(mc.albumgain_process_star,
                                              options_album)
                pool.close()
                
                for result in results:
                    timediff = datetime.datetime.today() - starttime
                    evt = EncResultEvent(dirname = result[0], 
                                         runtime = timediff, 
                                         status = result[1])
                    wx.PostEvent(self.win, evt)
                    if not self.keeprunning:
                        pool.terminate()
                        pool.join()
                        evt2 = EncResultEvent(runtime = timediff, status = 'aborted')
                        wx.PostEvent(self.win, evt2)
                        return
                pool.join()
                
            timediff = datetime.datetime.today() - starttime
            evt2 = EncResultEvent(runtime = timediff, status = 'finished')
            wx.PostEvent(self.win, evt2)
        
    def OnStop(self, e):
        self.keeprunning = False


def main():
    mp.freeze_support()
    appsettings = AppSettings()
    settings = ConvertSettings(appsettings.convertfile)
    app = wx.App(False)
    frame = MainWindow(None, appsettings, settings)
    app.MainLoop()


if __name__ == '__main__':
    main()
