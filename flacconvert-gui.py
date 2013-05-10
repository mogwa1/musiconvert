#!/usr/bin/env python
#
# Copyright 2012 Bart De Vries
#
# file: flacconvert-gui.py
#
#

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from __future__ import unicode_literals
import wx
import wx.lib.wordwrap
import os
import cPickle as pickle


class MainWindow(wx.Frame):
    def __init__(self, parent):
        # Create class to keep settings
        self.settings = ConvertSettings()
        # Create class to handle events
        self.eventhdl = EventHandler(self, self.settings)
        # Initialize widgets
        self._init_ctrls(parent)
    
    def _init_ctrls(self, prnt):
        wx.Frame.__init__(self, parent=prnt, title='Audio converter',
                          pos=wx.DefaultPosition, size=wx.DefaultSize)
        
        self.panel1 = wx.Panel(self)
        self.text1 = wx.StaticText(self.panel1, label='Convert from ')
        self.combobox1 = wx.ComboBox(self.panel1, value=self.settings.informat,
                                     style=wx.CB_READONLY|wx.CB_DROPDOWN,
                                     choices=['flac', 'mp3'])
        self.text2 = wx.StaticText(self.panel1, label=' to ')

        self.CreateStatusBar() # A Statusbar in the bottom of the window

        # Setting up the menu.
        self.filemenu= wx.Menu()
        self.menuOpenSettings = self.filemenu.Append(wx.ID_OPEN,'&Open Settings',
                                                     ' Open settings file')
        self.menuSaveSettings = self.filemenu.Append(wx.ID_SAVE,'&Save Settings',
                                                     ' Save settings file')
        self.menuSettings = self.filemenu.Append(wx.ID_SETUP,'S&ettings',
                                                 ' Change general settings')
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
        self.Bind(wx.EVT_MENU, self.eventhdl.OnSettings, self.menuSettings)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnExit, self.menuExit)
        self.Bind(wx.EVT_MENU, self.eventhdl.OnAbout, self.menuAbout)


        # Use some sizers to see layout options
        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer1.AddSizer(self.sizer2, flag=wx.ALL, border = 10)
        self.sizer2.Add(self.text1, proportion=1,
                        flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        self.sizer2.Add(self.combobox1, proportion=1,
                        flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        self.sizer2.Add(self.text2, proportion=1,
                        flag=wx.ALIGN_CENTER_VERTICAL|wx.ALL)

        #Layout sizers
        self.panel1.SetSizer(self.sizer1)
        self.sizer1.Fit(self.panel1)
        
        self.Show()


class SettingsDialog(wx.Dialog):
    def __init__(self, parent, title, settings,
                 size=wx.DefaultSize, pos=wx.DefaultPosition, 
                 style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, parent=parent, title=title,
                           size=wx.DefaultSize, pos=wx.DefaultPosition, 
                           style=wx.DEFAULT_DIALOG_STYLE)
        self.mp3gainpath=settings.mp3gainpath
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        
        labelmp3gain = wx.StaticText(self, label='Path to MP3gain: ')
        sizer2.Add(labelmp3gain, flag=wx.ALIGN_CENTER_VERTICAL)

        sizer2.AddSpacer(5)
        
        self.textmp3gain = wx.TextCtrl(self, value=self.mp3gainpath,
                                       size=(300,-1))
        sizer2.Add(self.textmp3gain, flag=wx.ALIGN_CENTER_VERTICAL)

        mp3gainbutton = wx.Button(self, label='...', style=wx.BU_EXACTFIT)
        sizer2.Add(mp3gainbutton, flag=wx.ALIGN_CENTER_VERTICAL)

        sizer.AddSizer(sizer2, flag=wx.ALL, border=10)

        btnsizer = wx.StdDialogButtonSizer()
        
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, flag=wx.CENTER|wx.ALL, border=5)

        # Bind methods to buttons
        self.Bind(wx.EVT_BUTTON, self.OnButtonMp3gainpath, mp3gainbutton)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def OnButtonMp3gainpath(self,e):
        dlg = wx.FileDialog(
            self, message="Choose mp3gain executable",
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
        info.Name = 'Audio Converter'
        info.Version = '0.1'
        info.Copyright = '(C) 2012 Bart De Vries'
        info.Description = wx.lib.wordwrap.wordwrap(
            'This is a GUI interface to the command line tool \'flacconvert\', '
            'which can convert all audio files in a directory into another audio '
            'format.  This includes tagging (also album art) and volume normalization.',
            350, wx.ClientDC(self.frame))
        info.Developers = ['Bart De Vries']
        info.License = 'GNU General Public License v3 or higher'
        wx.AboutBox(info)


    def OnExit(self,e):
        self.frame.Close(True)  # Close the frame.

    def OnOpenSettings(self,e):
        dlg = wx.FileDialog(
            self.frame, message="Choose settings file",
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
        
    def OnSettings(self,e):
        dlg = SettingsDialog(parent=self.frame, title='Settings',
                             settings=self.settings)
        if (dlg.ShowModal() == wx.ID_OK): # Shows it
            self.settings.mp3gainpath = dlg.mp3gainpath
            
        dlg.Destroy() # finally destroy it when finished.



class ConvertSettings(object):
    def __init__(self, filename='settings.ini'):
        self.currentfile = os.path.abspath(filename)
        if os.path.isfile(filename):
            self.load(filename)
        else:
            self.informat = 'flac'
            self.outformat = 'mp3'
            self.mp3gainpath = 'C:\Personal'

    def save(self, filename=''):
        if filename == '':
            filename = self.currentfile
        with open(filename, 'w') as setfile:
            pickle.dump(self, setfile)

    def load(self, filename='settings.ini'):
        if os.path.isfile(filename):
            with open(filename, 'r') as setfile:
                self = pickle.load(setfile)
            self.currentfile = os.path.abspath(filename)
           


def main():
    app = wx.App(False)
    frame = MainWindow(None)
    app.MainLoop()


if __name__ == '__main__':
    main()
