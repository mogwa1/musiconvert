#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  musiconvert-gui.py, version 0.1
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
import os
import cPickle as pickle
import multiprocessing as mp

class NotebookPanel1(wx.Panel):
    def __init__(self, parent, settings, evthandler):
        self.settings = settings
        self.evthandler = evthandler
        wx.Panel.__init__(self, parent)
        
        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        
        self.inputbox = wx.StaticBox(self, label='Input')
        self.inputboxsizer = wx.StaticBoxSizer(self.inputbox, wx.VERTICAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.text1 = wx.StaticText(self, label='Convert from: ')
        self.sizer2.Add(self.text1,
                        flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        self.sizer2.AddSpacer(5)
        self.combobox1 = wx.ComboBox(self, value=self.settings.informat,
                                     style=wx.CB_READONLY|wx.CB_DROPDOWN,
                                     choices=['flac'])
        self.sizer2.Add(self.combobox1,
                        flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        self.sizer2.AddSpacer(5)
        self.text2 = wx.StaticText(self, label=' to ')
        self.sizer2.Add(self.text2,
                        flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        self.sizer2.AddSpacer(5)
        self.combobox2 = wx.ComboBox(self, value=self.settings.outformat,
                                     style=wx.CB_READONLY|wx.CB_DROPDOWN,
                                     choices=['mp3'])
        self.sizer2.Add(self.combobox2,
                        flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        self.inputboxsizer.AddSizer(self.sizer2, flag=wx.ALL|wx.EXPAND, 
                                    border=10)
                        
        self.sizer1.AddSizer(self.inputboxsizer, 
                             flag=wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND, 
                             border = 10)
        self.sizer1.AddSpacer(5)                             
                             
        self.outputbox = wx.StaticBox(self, label='Output')
        self.outputboxsizer = wx.StaticBoxSizer(self.outputbox, wx.VERTICAL)
        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.text3 = wx.StaticText(self, label='Convert from: ')
        self.sizer3.Add(self.text3,
                        flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        self.sizer3.AddSpacer(5)
        self.combobox3 = wx.ComboBox(self, value=self.settings.informat,
                                     style=wx.CB_READONLY|wx.CB_DROPDOWN,
                                     choices=['flac', 'mp3'])
        self.sizer3.Add(self.combobox3,
                        flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        self.sizer3.AddSpacer(5)
        self.text4 = wx.StaticText(self, label=' to ')
        self.sizer3.Add(self.text4,
                        flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        self.sizer3.AddSpacer(5)
        self.combobox4 = wx.ComboBox(self, value=self.settings.outformat,
                                     style=wx.CB_READONLY|wx.CB_DROPDOWN,
                                     choices=['flac', 'mp3'])
        self.sizer3.Add(self.combobox4,
                        flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        self.outputboxsizer.AddSizer(self.sizer3, flag=wx.ALL|wx.EXPAND, 
                                     border=10)
                        
        self.sizer1.AddSizer(self.outputboxsizer, 
                             flag=wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 
                             border = 10)
                                  
                             
        self.SetSizer(self.sizer1)
        self.sizer1.Fit(self)
        
        self.Bind(wx.EVT_COMBOBOX, self.evthandler.OnInputSelection, self.combobox1)
        self.Bind(wx.EVT_COMBOBOX, self.evthandler.OnOutputSelection, self.combobox2)


class NotebookPanel2(wx.Panel):
    def __init__(self, parent, settings, evthandler):
        self.settings = settings
        self.evthandler = evthandler
        wx.Panel.__init__(self, parent)
        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)

        self.SetSizer(self.sizer1)
        self.sizer1.Fit(self)


class NotebookPanel3(wx.Panel):
    def __init__(self, parent, settings, evthandler):
        self.settings = settings
        self.evthandler = evthandler
        wx.Panel.__init__(self, parent)
        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)

        self.SetSizer(self.sizer1)
        self.sizer1.Fit(self)

        

class MainWindow(wx.Frame):
    def __init__(self, parent):
        # Create class to keep settings
        self.settings = ConvertSettings()
        # Create class to handle events
        self.eventhdl = EventHandler(self, self.settings)
        # Initialize widgets
        self._init_ctrls(parent)
    
    def _init_ctrls(self, prnt):
        wx.Frame.__init__(self, parent=prnt, title='MusiConvert v0.1')
        
        self.panel = wx.Panel(self)
        self.notebook = wx.Notebook(self.panel)
        
        self.panel1 = NotebookPanel1(self.notebook, self.settings, self.eventhdl)
        self.notebook.AddPage(self.panel1, 'Conversion')
        
        self.panel2 = NotebookPanel2(self.notebook, self.settings, self.eventhdl)
        self.notebook.AddPage(self.panel2, 'flac')

        self.panel3 = NotebookPanel3(self.notebook, self.settings, self.eventhdl)
        self.notebook.AddPage(self.panel2, 'mp3')

        self.CreateStatusBar() # A Statusbar in the bottom of the window

        # Setting up the menu.
        self.filemenu= wx.Menu()
        self.menuOpenSettings = self.filemenu.Append(wx.ID_OPEN,'&Open Settings ...',
                                                     ' Open settings file')
        self.menuSaveSettings = self.filemenu.Append(wx.ID_SAVE,'&Save Settings',
                                                     ' Save settings file')
        self.menuSaveAsSettings = self.filemenu.Append(wx.ID_SAVEAS,'Save Settings &As ...',
                                                     ' Save settings file')
        self.menuSep = self.filemenu.AppendSeparator()
        self.menuSettings = self.filemenu.Append(wx.ID_SETUP,'S&et Paths ...',
                                                 ' Set paths to external programs')
        self.menuSep2 = self.filemenu.AppendSeparator()
        self.menuExit = self.filemenu.Append(wx.ID_EXIT,'E&xit',
                                             ' Terminate the program')
        
        self.helpmenu= wx.Menu()
        self.menuAbout= self.helpmenu.Append(wx.ID_ABOUT, '&About',
                                             ' Information about this program')

        # Creating the menubar.
        self.menuBar = wx.MenuBar()
        self.menuBar.Append(self.filemenu,'&File') # Adding the 'filemenu' to the MenuBar

        self.menuBar.Append(self.helpmenu,'&Help') # Adding the 'helpmenu' to the MenuBar

        self.SetMenuBar(self.menuBar)  # Adding the MenuBar to the Frame content.


        # Events.
        self.Bind(wx.EVT_MENU, self.eventhdl.OnOpenSettings, self.menuOpenSettings)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnSaveSettings, self.menuSaveSettings)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnSaveAsSettings, self.menuSaveAsSettings)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnSettings, self.menuSettings)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnExit, self.menuExit)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnAbout, self.menuAbout)

        #Layout sizers
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.notebook, proportion=1, flag=wx.EXPAND|wx.ALL)
        self.panel.SetSizer(self.sizer)
        self.sizer.Fit(self.panel)
        self.Fit()
        self.Show()


class SettingsDialog(wx.Dialog):
    def __init__(self, parent, title, settings,
                 size=wx.DefaultSize, pos=wx.DefaultPosition, 
                 style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, parent=parent, title=title,
                           size=wx.DefaultSize, pos=wx.DefaultPosition, 
                           style=wx.DEFAULT_DIALOG_STYLE)
        self.settings     = settings
        self.lamepath     = settings.lamepath
        self.flacpath     = settings.flacpath
        self.metaflacpath = settings.metaflacpath
        self.mp3gainpath  = settings.mp3gainpath
        
        sizerV = wx.BoxSizer(wx.VERTICAL)

        boxmp3 = wx.StaticBox(self, label = 'MP3')
        boxmp3sizer = wx.StaticBoxSizer(boxmp3, wx.VERTICAL)

        sizerH1 = wx.BoxSizer(wx.HORIZONTAL)
        labellame = wx.StaticText(self, label='Path to LAME executable: ')
        sizerH1.Add(labellame, flag=wx.ALIGN_CENTER_VERTICAL)
        sizerH1.AddStretchSpacer()
        self.textlame = wx.TextCtrl(self, value=self.lamepath,
                                       size=(250,-1))
        sizerH1.Add(self.textlame, flag=wx.ALIGN_CENTER_VERTICAL)
        lamebutton = wx.Button(self, label='...', style=wx.BU_EXACTFIT)
        sizerH1.Add(lamebutton, flag=wx.ALIGN_CENTER_VERTICAL)
        boxmp3sizer.AddSizer(sizerH1, flag=wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND, 
                        border=10)
                        
        boxmp3sizer.AddSpacer(5)

        sizerH3 = wx.BoxSizer(wx.HORIZONTAL)
        labelmp3gain = wx.StaticText(self, label='Path to MP3gain executable: ')
        sizerH3.Add(labelmp3gain, flag=wx.ALIGN_CENTER_VERTICAL)
        sizerH3.AddStretchSpacer()
        self.textmp3gain = wx.TextCtrl(self, value=self.mp3gainpath,
                                       size=(250,-1))
        sizerH3.Add(self.textmp3gain, flag=wx.ALIGN_CENTER_VERTICAL)
        mp3gainbutton = wx.Button(self, label='...', style=wx.BU_EXACTFIT)
        sizerH3.Add(mp3gainbutton, flag=wx.ALIGN_CENTER_VERTICAL)

        boxmp3sizer.AddSizer(sizerH3, flag=wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 
                        border=10)
        
        sizerV.AddSizer(boxmp3sizer, flag=wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND,
                        border=10)
        
        sizerV.AddSpacer(10)

        boxflac = wx.StaticBox(self, label = 'FLAC')
        boxflacsizer = wx.StaticBoxSizer(boxflac, wx.VERTICAL)

        sizerH2 = wx.BoxSizer(wx.HORIZONTAL)
        labelflac = wx.StaticText(self, label='Path to FLAC executable: ')
        sizerH2.Add(labelflac, flag=wx.ALIGN_CENTER_VERTICAL)
        sizerH2.AddStretchSpacer()
        self.textflac = wx.TextCtrl(self, value=self.flacpath,
                                       size=(250,-1))
        sizerH2.Add(self.textflac, flag=wx.ALIGN_CENTER_VERTICAL)
        flacbutton = wx.Button(self, label='...', style=wx.BU_EXACTFIT)
        sizerH2.Add(flacbutton, flag=wx.ALIGN_CENTER_VERTICAL)

        boxflacsizer.AddSizer(sizerH2, flag=wx.TOP|wx.LEFT|wx.RIGHT|wx.EXPAND, 
                              border=10)
                              
        boxflacsizer.AddSpacer(5)
        
        sizerH4 = wx.BoxSizer(wx.HORIZONTAL)
        labelmetaflac = wx.StaticText(self, label='Path to METAFLAC executable: ')
        sizerH4.Add(labelmetaflac, flag=wx.ALIGN_CENTER_VERTICAL)
        sizerH4.AddStretchSpacer()
        self.textmetaflac = wx.TextCtrl(self, value=self.metaflacpath,
                                       size=(250,-1))
        sizerH4.Add(self.textmetaflac, flag=wx.ALIGN_CENTER_VERTICAL)
        metaflacbutton = wx.Button(self, label='...', style=wx.BU_EXACTFIT)
        sizerH4.Add(metaflacbutton, flag=wx.ALIGN_CENTER_VERTICAL)

        boxflacsizer.AddSizer(sizerH4, flag=wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 
                              border=10)

        sizerV.AddSizer(boxflacsizer, flag=wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND,
                        border=10)


        btnsizer = wx.StdDialogButtonSizer()
        
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizerV.Add(btnsizer, flag=wx.CENTER|wx.ALL, border=5)

        # Bind methods to buttons
        self.Bind(wx.EVT_BUTTON, self.OnButtonlamepath, lamebutton)
        self.Bind(wx.EVT_BUTTON, self.OnButtonflacpath, flacbutton)
        self.Bind(wx.EVT_BUTTON, self.OnButtonMp3gainpath, mp3gainbutton)
        self.Bind(wx.EVT_BUTTON, self.OnButtonmetaflacpath, metaflacbutton)

        self.SetSizer(sizerV)
        sizerV.Fit(self)

    def OnButtonlamepath(self,e):
        dlg = wx.FileDialog(
            self, message="Choose LAME executable",
            defaultDir=os.path.dirname(self.lamepath), 
            defaultFile=os.path.basename(self.lamepath),
            wildcard='Executable files (*.exe)|*.exe|'
                     'All files (*.*)|*.*',
            style=wx.OPEN
            )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            self.lamepath = paths[0]
            self.textlame.SetValue(self.lamepath)
        dlg.Destroy()

        
    def OnButtonflacpath(self,e):
        dlg = wx.FileDialog(
            self, message="Choose FLAC executable",
            defaultDir=os.path.dirname(self.flacpath), 
            defaultFile=os.path.basename(self.flacpath),
            wildcard='Executable files (*.exe)|*.exe|'
                     'All files (*.*)|*.*',
            style=wx.OPEN
            )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            self.flacpath = paths[0]
            self.textflac.SetValue(self.flacpath)
        dlg.Destroy()

    def OnButtonmetaflacpath(self,e):
        dlg = wx.FileDialog(
            self, message="Choose METAFLAC executable",
            defaultDir=os.path.dirname(self.metaflacpath), 
            defaultFile=os.path.basename(self.metaflacpath),
            wildcard='Executable files (*.exe)|*.exe|'
                     'All files (*.*)|*.*',
            style=wx.OPEN
            )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            self.metaflacpath = paths[0]
            self.textmetaflac.SetValue(self.metaflacpath)
        dlg.Destroy()

    def OnButtonMp3gainpath(self,e):
        dlg = wx.FileDialog(
            self, message="Choose MP3gain executable",
            defaultDir=os.path.dirname(self.mp3gainpath), 
            defaultFile=os.path.basename(self.mp3gainpath),
            wildcard='Executable files (*.exe)|*.exe|'
                     'All files (*.*)|*.*',
            style=wx.OPEN
            )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            self.mp3gainpath = paths[0]
            self.textmp3gain.SetValue(self.mp3gainpath)
        dlg.Destroy()
        



class EventHandler(object):
    def __init__(self, parent, settings):
        self.frame = parent
        self.settings = settings

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
        self.frame.Close(True)  # Close the frame.

    def OnOpenSettings(self,e):
        dlg = wx.FileDialog(
            self.frame, message="Open Settings File",
            defaultDir=os.path.dirname(self.settings.currentfile), 
            defaultFile=os.path.basename(self.settings.currentfile),
            wildcard='Settings files (*.ini)|*.ini|'
                     'All files (*.*)|*.*',
            style=wx.OPEN
            )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            self.settings.load(paths[0])
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
            self.settings.save(paths[0])
        dlg.Destroy()
        
    def OnSettings(self,e):
        dlg = SettingsDialog(parent=self.frame, title='Set Paths',
                             settings=self.settings)
        if (dlg.ShowModal() == wx.ID_OK): # Shows it
            self.settings.lamepath = dlg.lamepath
            self.settings.flacpath = dlg.flacpath
            self.settings.metaflacpath = dlg.metaflacpath
            self.settings.mp3gainpath = dlg.mp3gainpath
                        
        dlg.Destroy() # finally destroy it when finished.
        
    def OnInputSelection(self,e):
        self.settings.informat = e.GetString()

    def OnOutputSelection(self,e):
        self.settings.outformat = e.GetString()



class ConvertSettings(object):
    def __init__(self, filename='settings.ini'):
        self.currentfile = os.path.abspath(filename)
        if os.path.isfile(filename):
            self.load(filename)
        else:
            self.informat = 'flac'
            self.outformat = 'mp3'
            self.mp3gainpath = 'C:\Personal'
            self.flacpath = ''
            self.metaflacpath = ''
            self.lamepath = ''

    def save(self, filename=''):
        if filename == '':
            filename = self.currentfile
        with open(filename, 'wb') as setfile:
            pickle.dump(self.__dict__, setfile)

    def load(self, filename='settings.ini'):
        if os.path.isfile(filename):
            with open(filename, 'rb') as setfile:
                tmp_dict = pickle.load(setfile)
            self.__dict__.update(tmp_dict)
            self.currentfile = os.path.abspath(filename)
           


def main():
    mp.freeze_support()
    app = wx.App(False)
    frame = MainWindow(None)
    app.MainLoop()


if __name__ == '__main__':
    main()
