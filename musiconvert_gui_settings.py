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
import os
import tangoart as ta
import musiconvert_func as mc
import musiconvert_gui as mcg
import mywxclasses as mwx
import multiprocessing
import wx.lib.mixins.listctrl as listmix


class PreferencesDialog(wx.Dialog):
    def __init__(self, parent, title, settings, selectedpage,
                 style=wx.DEFAULT_DIALOG_STYLE, *args, **kwargs):
        wx.Dialog.__init__(self, parent=parent, title=title,
                           style=style, *args, **kwargs)
        self.settings     = settings
        self.lamepath     = settings.lamepath
        self.flacpath     = settings.flacpath
        self.metaflacpath = settings.metaflacpath
        self.mp3gainpath  = settings.mp3gainpath
        self.overwrite    = settings.overwrite
        self.flat         = settings.flat
        self.gain         = settings.gain
        self.manualprocesses = True if settings.nrprocesses else False
        if settings.nrprocesses:
            self.nrprocesses = settings.nrprocesses
        else:
            self.nrprocesses = multiprocessing.cpu_count()
        self.lamebitrate   = settings.lamebitrate
        self.lameextraopts = settings.lameextraopts
        self.tagfields     = settings.tagfields[:]
        self.id3mapping    = settings.id3mapping.copy()
       
        wx.ArtProvider.Push(ta.TangoArtProvider('tango-icon-theme-0.8.90'))
        tbsize = (32,32)
        system_bmp = wx.ArtProvider.GetBitmap(ta.ART_SYSTEM, wx.ART_TOOLBAR, tbsize)
        audio_bmp = wx.ArtProvider.GetBitmap(ta.ART_TYPE_AUDIO, wx.ART_TOOLBAR, tbsize)
        tbsize = (22,22)
        folder_bmp = wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_TOOLBAR, tbsize)
        
        #################
        # setup controls
        #################
        
        # imagelist for listbook
        il = wx.ImageList(32,32)
        il.Add(system_bmp)
        for i in xrange(len(self.settings.codecnames)):
            il.Add(audio_bmp)
        
        # listbook
        self.listbook = wx.Listbook(self)
        self.listbook.AssignImageList(il)
        self.generalpanel = wx.Panel(self.listbook)
        self.flacpanel = wx.Panel(self.listbook)
        self.mp3panel = wx.Panel(self.listbook)
        self.listbook.AddPage(self.generalpanel, 'General', imageId=0)
        self.listbook.AddPage(self.flacpanel, 'Flac', imageId=1)
        self.listbook.AddPage(self.mp3panel, 'Mp3', imageId=2)
        self.listbook.ChangeSelection(selectedpage)
        
        # buttons
        btnok = wx.Button(self, wx.ID_OK)
        btnok.SetDefault()
        btncancel = wx.Button(self, wx.ID_CANCEL)

        
        ######################
        # generalpanel
        ######################
        
        self.generalbook = wx.Notebook(self.generalpanel)
        self.optionspanel = wx.Panel(self.generalbook)
        self.pathpanel = wx.Panel(self.generalbook)
        self.tagpanel = wx.Panel(self.generalbook)
        self.generalbook.AddPage(self.optionspanel, text='General settings')
        self.generalbook.AddPage(self.pathpanel, text='External programs')
        self.generalbook.AddPage(self.tagpanel, text='Tag descriptions')
        
        self.generalsizer = wx.BoxSizer(wx.VERTICAL)
        self.generalsizer.Add(self.generalbook, flag=wx.EXPAND, proportion=1)
        self.generalpanel.SetSizer(self.generalsizer)

        #######
        # optionspanel
        #######
        
        # controls on optionspanel
        boxoutopts = wx.StaticBox(self.optionspanel, 
                                  label = 'Output file/directory options')
        overwritecb = wx.CheckBox(self.optionspanel,
                                  label = 'Overwrite existing files')
        overwritecb.SetValue(self.overwrite)
        flatcb = wx.CheckBox(self.optionspanel,
                             label = 'Don\'t create subdirectories, put everyting into output folder')
        flatcb.SetValue(self.flat)

        boxgain = wx.StaticBox(self.optionspanel, 
                               label = 'Volume normalization options')
        labelgain = wx.StaticText(self.optionspanel, label='After conversion, do:')
        self.comboboxgain = wx.ComboBox(self.optionspanel, value=self._getgainname(),
                                        style=wx.CB_READONLY|wx.CB_DROPDOWN,
                                        choices=('Nothing', 'Track gain', 'Album gain'))

        boxprocess = wx.StaticBox(self.optionspanel,
                                  label = 'General conversion settings')
        self.processcb = wx.CheckBox(self.optionspanel, 
                                     label = 'Manually set # of encoding processes: ')
        self.processcb.SetValue(self.manualprocesses)
        self.processspinctrl = wx.SpinCtrl(self.optionspanel, 
                                           style = wx.SP_ARROW_KEYS,
                                           min=1, max=10, initial=self.nrprocesses, 
                                           size=(50,-1))
        self.processspinctrl.Enable(self.manualprocesses)
        processtext = wx.StaticText(self.optionspanel, 
                                    label = '(default = # of cpu cores)')

        # setup sizers
        outoptssizer = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        outoptssizer.AddGrowableCol(1, proportion=1)
        outoptssizer.SetFlexibleDirection(wx.HORIZONTAL)
        outoptssizer.Add(overwritecb, flag=wx.TOP, border=5)
        outoptssizer.AddStretchSpacer()
        outoptssizer.Add(flatcb, flag=wx.BOTTOM, border=5)
        outoptssizer.AddStretchSpacer()
        
        boxoutoptssizer = wx.StaticBoxSizer(boxoutopts, wx.VERTICAL)
        boxoutoptssizer.AddSpacer(outoptssizer, flag=wx.LEFT|wx.RIGHT, border=10)


        gainsizer = wx.FlexGridSizer(rows=1, cols=3, vgap=5, hgap=5)
        gainsizer.AddGrowableCol(2, proportion=1)
        gainsizer.SetFlexibleDirection(wx.HORIZONTAL)
        gainsizer.Add(labelgain, flag=wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 
                      border=5)
        gainsizer.Add(self.comboboxgain, flag=wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 
                      border=5)
        gainsizer.AddStretchSpacer()
        
        boxgainsizer = wx.StaticBoxSizer(boxgain, wx.VERTICAL)
        boxgainsizer.AddSpacer(gainsizer, flag=wx.LEFT|wx.RIGHT, border=10)

        processsizer = wx.BoxSizer(wx.HORIZONTAL)
        processsizer.Add(self.processcb, 
                         flag=wx.TOP|wx.ALIGN_CENTER_VERTICAL, border=5)
        processsizer.Add(self.processspinctrl, 
                         flag=wx.TOP|wx.ALIGN_CENTER_VERTICAL, border=5)
        processsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        processsizer2.Add(processtext, flag=wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, border=5)
        
        boxprocesssizer = wx.StaticBoxSizer(boxprocess, wx.VERTICAL)
        boxprocesssizer.AddSpacer(processsizer, flag=wx.LEFT|wx.RIGHT, border=10)
        boxprocesssizer.AddSpacer(processsizer2, flag=wx.LEFT, border=50)

        optionssizer = wx.BoxSizer(wx.VERTICAL)
        optionssizer.AddSizer(boxoutoptssizer, flag=wx.ALL|wx.EXPAND,
                              border=10)
        optionssizer.AddSizer(boxgainsizer, flag=wx.RIGHT|wx.LEFT|wx.BOTTOM|wx.EXPAND,
                              border=10)
        optionssizer.AddSizer(boxprocesssizer, flag=wx.RIGHT|wx.LEFT|wx.BOTTOM|wx.EXPAND,
                              border=10)
        optionssizer.AddStretchSpacer()
        
        self.optionspanel.SetSizer(optionssizer)
        
        ######
        # Path panel
        ######
        
        # controls on pathpanel
        boxflacpaths = wx.StaticBox(self.pathpanel, 
                                    label = 'Flac related programs')

        labelflac = wx.StaticText(self.pathpanel, label='Flac:')
        self.textflac = wx.TextCtrl(self.pathpanel, value=self.flacpath)
        flacbutton = wx.BitmapButton(self.pathpanel, bitmap=folder_bmp)
        
        labelmetaflac = wx.StaticText(self.pathpanel, label='MetaFlac:')
        self.textmetaflac = wx.TextCtrl(self.pathpanel, value=self.metaflacpath)
        metaflacbutton = wx.BitmapButton(self.pathpanel, bitmap=folder_bmp)
        
        boxmp3paths = wx.StaticBox(self.pathpanel, 
                                   label = 'Mp3 related programs')
        
        labellame = wx.StaticText(self.pathpanel, label='Lame:')
        self.textlame = wx.TextCtrl(self.pathpanel, value=self.lamepath)
        lamebutton = wx.BitmapButton(self.pathpanel, bitmap=folder_bmp)
                    
        labelmp3gain = wx.StaticText(self.pathpanel, label='MP3Gain:')
        self.textmp3gain = wx.TextCtrl(self.pathpanel, value=self.mp3gainpath)
        mp3gainbutton = wx.BitmapButton(self.pathpanel, bitmap=folder_bmp)

        # setup sizers
        textflacsizer = wx.BoxSizer(wx.HORIZONTAL)
        textflacsizer.Add(self.textflac, flag=wx.ALIGN_CENTER_VERTICAL, 
                          proportion=1)
        textmetaflacsizer = wx.BoxSizer(wx.HORIZONTAL)
        textmetaflacsizer.Add(self.textmetaflac, flag=wx.ALIGN_CENTER_VERTICAL, 
                              proportion=1)
        textlamesizer = wx.BoxSizer(wx.HORIZONTAL)
        textlamesizer.Add(self.textlame, flag=wx.ALIGN_CENTER_VERTICAL, 
                          proportion=1)
        textmp3gainsizer = wx.BoxSizer(wx.HORIZONTAL)
        textmp3gainsizer.Add(self.textmp3gain, flag=wx.ALIGN_CENTER_VERTICAL, 
                             proportion=1)
        
        flacpathsizer = wx.FlexGridSizer(rows=2, cols=3, vgap=5, hgap=5)
        flacpathsizer.AddGrowableCol(1, proportion=1)
        flacpathsizer.SetFlexibleDirection(wx.HORIZONTAL)
        flacpathsizer.Add(labelflac, flag=wx.ALIGN_CENTER_VERTICAL)
        flacpathsizer.AddSizer(textflacsizer, flag=wx.EXPAND)
        flacpathsizer.Add(flacbutton, flag=wx.ALIGN_CENTER_VERTICAL)
        flacpathsizer.Add(labelmetaflac, flag=wx.ALIGN_CENTER_VERTICAL)
        flacpathsizer.AddSizer(textmetaflacsizer, flag=wx.EXPAND)
        flacpathsizer.Add(metaflacbutton, flag=wx.ALIGN_CENTER_VERTICAL)
        mp3pathsizer = wx.FlexGridSizer(rows=2, cols=3, vgap=5, hgap=5)
        mp3pathsizer.AddGrowableCol(1, proportion=1)
        mp3pathsizer.SetFlexibleDirection(wx.HORIZONTAL)
        mp3pathsizer.Add(labellame, flag=wx.ALIGN_CENTER_VERTICAL)
        mp3pathsizer.AddSizer(textlamesizer, flag=wx.EXPAND)
        mp3pathsizer.Add(lamebutton, flag=wx.ALIGN_CENTER_VERTICAL)
        mp3pathsizer.Add(labelmp3gain, flag=wx.ALIGN_CENTER_VERTICAL)
        mp3pathsizer.AddSizer(textmp3gainsizer, flag=wx.EXPAND)
        mp3pathsizer.Add(mp3gainbutton, flag=wx.ALIGN_CENTER_VERTICAL)
        
        boxflacpathsizer = wx.StaticBoxSizer(boxflacpaths, wx.VERTICAL)
        boxflacpathsizer.AddSpacer(flacpathsizer, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, 
                                   proportion=1, border=10)
        boxmp3pathsizer = wx.StaticBoxSizer(boxmp3paths, wx.VERTICAL)
        boxmp3pathsizer.AddSpacer(mp3pathsizer, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, 
                                   proportion=1, border=10)

        pathsizer = wx.BoxSizer(wx.VERTICAL)
        pathsizer.AddSizer(boxflacpathsizer, flag=wx.ALL|wx.EXPAND,
                           border=10)
        pathsizer.AddSizer(boxmp3pathsizer, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND,
                           border=10)
        self.pathpanel.SetSizer(pathsizer)
        
        ######
        # Tag descriptions
        ######
        
        # controls
        taglabel = wx.StaticText(self.tagpanel, 
                                 label='List of tag descriptions to be mapped '+\
                                       'to the individual format tags.\n'+\
                                       'Add your own tag descriptions here. '+\
                                       'You can then map them to specific\n'+\
                                       'format tags on the individual format tabs.')
        self.taglist = mwx.AddListCtrl(self.tagpanel, style=wx.LC_REPORT)
        self.taglist.InsertColumn(0, 'Tag description')

        # sizers
        
        tagsizer = wx.BoxSizer(wx.VERTICAL)
        tagsizer.Add(taglabel, flag=wx.ALL, border=10)
        tagsizer.Add(self.taglist, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 
                     proportion=1, border=10)
        
        self.tagpanel.SetSizer(tagsizer)

        
        ######################
        # mp3 panel
        ######################
        
        self.mp3book = wx.Notebook(self.mp3panel)
        self.lamepanel = wx.Panel(self.mp3book)
        self.id3panel = wx.Panel(self.mp3book)
        self.mp3book.AddPage(self.lamepanel, text='LAME options')
        self.mp3book.AddPage(self.id3panel, text='Tagging')
        
        self.mp3booksizer = wx.BoxSizer(wx.VERTICAL)
        self.mp3booksizer.Add(self.mp3book, flag=wx.EXPAND, proportion=1)
        self.mp3panel.SetSizer(self.mp3booksizer)

        #######
        # LAME options
        #######
        
        # options
        self.lamevbrchoices = ('V0 (~ 245 kbit/s)', 'V1 (~ 225 kbit/s)', 
                               'V2 (~ 190 kbit/s)', 'V3 (~ 175 kbit/s)',
                               'V4 (~ 165 kbit/s)', 'V5 (~ 130 kbit/s)', 
                               'V6 (~ 115 kbit/s)', 'V7 (~ 100 kbit/s)', 
                               'V8 (~ 85 kbit/s)', 'V9 (~ 65 kbit/s)')
        self.lamevbroptions = ('-V0', '-V1', '-V2', '-V3', '-V4', '-V5', 
                               '-V6', '-V7', '-V8', '-V9')
        self.lamecbrchoices = ('320 kbit/s', '256 kbit/s', '224 kbit/s', 
                               '192 kbit/s', '160 kbit/s', '128 kbit/s', 
                               '112 kbit/s', '96 kbit/s', '80 kbit/s', 
                               '64 kbit/s', '48 kbit/s', '40 kbit/s', 
                               '32 kbit/s', '24 kbit/s', '16 kbit/s', 
                               '8 kbit/s')
        self.lamecbroptions = ('-b 320', '-b 256', '-b 224', '-b 192', 
                               '-b 160', '-b 128', '-b 112', '-b 96', 
                               '-b 80',  '-b 64', '-b 48',  '-b 40',  
                               '-b 32',  '-b 24', '-b 16',  '-b 8')
        
        # controls
        boxbitrate = wx.StaticBox(self.lamepanel, 
                                  label = 'Bitrate')

        self.rbvbr = wx.RadioButton(self.lamepanel, label = 'Variable bit rate:',
                                    style = wx.RB_GROUP)
        self.rbabr = wx.RadioButton(self.lamepanel, label = 'Average bit rate:')
        self.rbcbr = wx.RadioButton(self.lamepanel, label = 'Constant bit rate:')
        self.combovbr = wx.ComboBox(self.lamepanel, value=settings.lamevbr,
                                    style=wx.CB_READONLY|wx.CB_DROPDOWN,
                                    choices=self.lamevbrchoices)
        self.spinabr = wx.SpinCtrl(self.lamepanel, style = wx.SP_ARROW_KEYS,
                                   min=80, max=320, initial=settings.lameabr, 
                                   size=(60,-1))
        self.combocbr = wx.ComboBox(self.lamepanel, value=settings.lamecbr,
                                    style=wx.CB_READONLY|wx.CB_DROPDOWN,
                                    choices=self.lamecbrchoices)
        
        boxlameextra = wx.StaticBox(self.lamepanel, 
                                    label = 'Other options')
        lameextralabel = wx.StaticText(self.lamepanel,
                                       label = 'Additional command line options: ')
        self.lameextratext = wx.TextCtrl(self.lamepanel, value=self.lameextraopts)
        
        lameoptslabel = wx.StaticText(self.lamepanel, label='Full LAME options: ')
        self.lameoptstext = wx.TextCtrl(self.lamepanel, style=wx.TE_READONLY)
        self.lameoptstext.Enable(False)
        self._setlamebitratestate()
        self._updatelameoptions()
        
        # sizers
        bitratesizer = wx.FlexGridSizer(rows=3, cols=3, vgap=5, hgap=5)
        bitratesizer.AddGrowableCol(1, proportion=1)
        bitratesizer.SetFlexibleDirection(wx.HORIZONTAL)
        bitratesizer.Add(self.rbvbr, flag=wx.TOP|wx.ALIGN_CENTER_VERTICAL, 
                         border=5)
        bitratesizer.Add(self.combovbr, flag=wx.TOP|wx.ALIGN_CENTER_VERTICAL, 
                         border=5)
        bitratesizer.AddStretchSpacer()
        bitratesizer.Add(self.rbabr, flag=wx.ALIGN_CENTER_VERTICAL, 
                         border=5)
        bitratesizer.Add(self.spinabr, flag=wx.ALIGN_CENTER_VERTICAL, 
                         border=5)
        bitratesizer.AddStretchSpacer()
        bitratesizer.Add(self.rbcbr, flag=wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 
                         border=5)
        bitratesizer.Add(self.combocbr, flag=wx.BOTTOM|wx.ALIGN_CENTER_VERTICAL, 
                         border=5)
        bitratesizer.AddStretchSpacer()

        boxbitratesizer = wx.StaticBoxSizer(boxbitrate, wx.VERTICAL)
        boxbitratesizer.AddSpacer(bitratesizer, flag=wx.LEFT|wx.RIGHT, border=10)

        lameextrasizer = wx.BoxSizer(wx.HORIZONTAL)
        lameextrasizer.Add(lameextralabel, flag=wx.ALIGN_CENTER_VERTICAL)
        lameextrasizer.Add(self.lameextratext, flag=wx.TOP|wx.BOTTOM|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 
                           border=5, proportion=1)
 
        boxlameextrasizer = wx.StaticBoxSizer(boxlameextra, wx.VERTICAL)
        boxlameextrasizer.AddSpacer(lameextrasizer, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, border=10)
 
        lameoptssizer = wx.BoxSizer(wx.HORIZONTAL)
        lameoptssizer.Add(lameoptslabel, flag=wx.ALIGN_CENTER_VERTICAL)
        lameoptssizer.Add(self.lameoptstext, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 
                          proportion=1)
 
        lamesizer = wx.BoxSizer(wx.VERTICAL)
        lamesizer.AddSizer(boxbitratesizer, flag=wx.ALL|wx.EXPAND, 
                          border = 10)
        lamesizer.AddSizer(boxlameextrasizer, border = 10,
                          flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND)
        lamesizer.AddSizer(lameoptssizer, border = 10,
                          flag=wx.ALL|wx.EXPAND)
        lamesizer.AddStretchSpacer()
        
        self.lamepanel.SetSizer(lamesizer)
        
        ######
        # ID3 tag mapping
        ######
        
        # controls
        id3label = wx.StaticText(self.id3panel, 
                                 label='Mapping of tag descriptions to ID3 tags')
        self.id3list = mwx.EditListCtrl(self.id3panel, vetocols=[0], style=wx.LC_REPORT)
        listwidth = self.id3list.GetSizeTuple()[0]
        self.id3list.InsertColumn(0, 'Tag description', width=int(listwidth/2))
        self.id3list.InsertColumn(1, 'ID3 tags')

        # sizers
        
        id3sizer = wx.BoxSizer(wx.VERTICAL)
        id3sizer.Add(id3label, flag=wx.ALL, border=10)
        id3sizer.Add(self.id3list, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 
                     proportion=1, border=10)
        
        self.id3panel.SetSizer(id3sizer)
        
        
        ######################
        # General sizers
        ######################
        
        btnsizer = wx.StdDialogButtonSizer()
        btnsizer.AddButton(btnok)
        btnsizer.AddButton(btncancel)
        btnsizer.Realize()

        sizerV = wx.BoxSizer(wx.VERTICAL)
        sizerV.Add(self.listbook, proportion=1, flag=wx.EXPAND|wx.ALL, border = 0)
        sizerV.Add(btnsizer, flag=wx.CENTER|wx.ALL, border=5)
    
        ##############
        # setup events
        ##############
        self.Bind(wx.EVT_BUTTON, self.OnButtonlamepath, lamebutton)
        self.Bind(wx.EVT_BUTTON, self.OnButtonflacpath, flacbutton)
        self.Bind(wx.EVT_BUTTON, self.OnButtonMp3gainpath, mp3gainbutton)
        self.Bind(wx.EVT_BUTTON, self.OnButtonmetaflacpath, metaflacbutton)
        self.Bind(wx.EVT_TEXT, self.OnTextlamepath, self.textlame)
        self.Bind(wx.EVT_TEXT, self.OnTextflacpath, self.textflac)
        self.Bind(wx.EVT_TEXT, self.OnTextMp3gainpath, self.textmp3gain)
        self.Bind(wx.EVT_TEXT, self.OnTextmetaflacpath, self.textmetaflac)
        self.Bind(wx.EVT_CHECKBOX, self.OnOverwrite, overwritecb)
        self.Bind(wx.EVT_CHECKBOX, self.OnFlat, flatcb)
        self.Bind(wx.EVT_COMBOBOX, self.OnGain, self.comboboxgain)
        self.Bind(wx.EVT_CHECKBOX, self.OnNrProcesses, self.processcb)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnChangeLameOptions, self.rbvbr)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnChangeLameOptions, self.rbabr)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnChangeLameOptions, self.rbcbr)
        self.Bind(wx.EVT_COMBOBOX, self.OnChangeLameOptions, self.combovbr)
        self.Bind(wx.EVT_SPINCTRL, self.OnChangeLameOptions, self.spinabr)
        self.Bind(wx.EVT_COMBOBOX, self.OnChangeLameOptions, self.combocbr)
        self.Bind(wx.EVT_TEXT, self.OnChangeLameOptions, self.lameextratext)
        self.Bind(wx.EVT_LISTBOOK_PAGE_CHANGING, self.OnChangeListPage, self.listbook)

        self.SetSizer(sizerV)
        self.Layout()
        
        # Finally populate the (tagging) listctrls
        self._populatelists()

    def _getgainname(self):
        gainname = 'Nothing'
        if self.gain == 'track':
            gainname = 'Track gain'
        elif self.gain == 'album':
            gainname = 'Album gain'
        return gainname
        
    def _setgainname(self, gainname):
        if gainname == 'Track gain':
            self.gain = 'track'
        elif gainname == 'Album gain':
            self.gain = 'album'
        else:
            self.gain = None

    def _setlamebitratestate(self):
        if self.lamebitrate in self.lamevbroptions:
            self.rbvbr.SetValue(True)
            index = self.lamevbroptions.index(self.lamebitrate)
            self.combovbr.SetValue(self.lamevbrchoices[index])
        if self.lamebitrate in self.lamecbroptions:
            self.rbcbr.SetValue(True)
            index = self.lamecbroptions.index(self.lamebitrate)
            self.combocbr.SetValue(self.lamecbrchoices[index])
        if '--preset' in self.lamebitrate:
            self.rbabr.SetValue(True)
            value = int(self.lamebitrate.split(' ')[1])
            self.spinabr.SetValue(value)

    def _updatelameoptions(self):
        if self.rbvbr.GetValue():
            index = self.lamevbrchoices.index(self.combovbr.GetValue())
            self.lamebitrate = self.lamevbroptions[index]
        if self.rbcbr.GetValue():
            index = self.lamecbrchoices.index(self.combocbr.GetValue())
            self.lamebitrate = self.lamecbroptions[index]
        if self.rbabr.GetValue():
            self.lamebitrate = '--preset '+str(self.spinabr.GetValue())
        self.lameextraopts = self.lameextratext.GetValue()
        self.lameoptstext.SetValue(self.lamebitrate + ' ' + self.lameextraopts)
        
    def _populatelists(self):
        self.taglist.DeleteAllItems()
        self.id3list.DeleteAllItems()
        for i, label in enumerate(self.tagfields):
            self.taglist.InsertStringItem(i, label)
            self.id3list.InsertStringItem(i, label)
            try:
                id3label = self.id3mapping[label]
            except KeyError:
                id3label = ''
            self.id3list.SetStringItem(i, 1, id3label)
        self.taglist.InsertStringItem(len(self.tagfields)+1, '')
        listwidth = self.id3list.GetSizeTuple()[0]
        self.id3list.SetColumnWidth(0, int(listwidth/2))
        self.taglist.resizeLastColumn(100)
        self.id3list.resizeLastColumn(100)

    def _getlistdata(self):
        self.tagfields = []
        self.id3mapping = {}
        for i in xrange(self.taglist.GetItemCount()-1):
            self.tagfields.append(self.taglist.GetItem(i, 0).GetText())
        for i in xrange(self.id3list.GetItemCount()):
            key = self.id3list.GetItem(i, 0).GetText()
            value = self.id3list.GetItem(i, 1).GetText()
            if value:
                self.id3mapping[key] = value

    def OnChangeListPage(self, e):
        self._getlistdata()
        self._populatelists()

    def OnButtonlamepath(self, e):
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
    
    def OnTextlamepath(self, e):
        path = e.GetString()
        self.lamepath = path
        
    def OnButtonflacpath(self, e):
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

    def OnTextflacpath(self, e):
        path = e.GetString()
        self.flacpath = path

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

    def OnTextmetaflacpath(self, e):
        path = e.GetString()
        self.metaflacpath = path
        
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
        
    def OnTextMp3gainpath(self, e):
        path = e.GetString()
        self.mp3gainpath = path
        
    def OnOverwrite(self, e):
        self.overwrite = e.IsChecked()
        
    def OnFlat(self, e):
        self.flat = e.IsChecked()

    def OnGain(self, e):
        self._setgainname(e.GetString())

    def OnNrProcesses(self, e):
        self.manualprocesses = e.IsChecked()
        self.processspinctrl.Enable(self.manualprocesses)
        if not self.manualprocesses:
            self.processspinctrl.SetValue(multiprocessing.cpu_count())
            
    def OnChangeLameOptions(self, e):
        self._updatelameoptions()

def main():
    appsettings = mcg.AppSettings()
    settings = mcg.ConvertSettings(appsettings.convertfile)
    app = wx.App(False)
    frame = mcg.MainWindow(None, appsettings, settings)
    dlg = PreferencesDialog(frame, 'Preferences', settings, 
                            selectedpage=appsettings.optionsselectedpage, size=(500,500), 
                            style=wx.RESIZE_BORDER|wx.DEFAULT_DIALOG_STYLE)
    dlg.ShowModal()
    appsettings.optionsselectedpage=dlg.listbook.GetSelection()
    dlg.Destroy()
    app.MainLoop()


if __name__ == '__main__':
    main()
