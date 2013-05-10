#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  TangoArtProvider.py, version 0.1
#  
#  Copyright 2012 Bart De Vries <devries.bart@gmail.com>
#  
#  Based on tangoart.py from PyDE project, which is also GPL
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
import logging

def counter_generator():
    num = 100
    while True:
        yield str(num)
        num += 1

counter = counter_generator()

ART_MEDIA_PLAYBACK_START = counter.next()
ART_MEDIA_PLAYBACK_STOP = counter.next()
ART_EDIT_CLEAR = counter.next()
ART_PRINT_PREVIEW = counter.next()	
ART_SELECT_ALL = counter.next()		
ART_FOLDER_NEW = counter.next()		
ART_INDENT_MORE = counter.next()		
ART_INDENT_LESS = counter.next()		
ART_LIST_ADD = counter.next()		
ART_LIST_REMOVE = counter.next()		
ART_STOP = counter.next()				
ART_TAB_NEW = counter.next()			
ART_VIEW_FULLSCREEN = counter.next()	
ART_VIEW_REFRESH = counter.next()		
ART_WINDOW_NEW = counter.next()		
ART_PREFS_FONT = counter.next()		
ART_PREFS_SHORTCUTS = counter.next()	
ART_PREFS_LOCALE = counter.next()		
ART_SOFTWARE_UPDATE = counter.next()	
ART_TERMINAL = counter.next()			
ART_FAVORITE = counter.next()			
ART_IMPORTANT = counter.next()		
ART_READONLY = counter.next()			
ART_FOLDER = counter.next()			
ART_NETWORK_SERVER = counter.next()	
ART_NETWORK_FOLDER = counter.next()	
ART_NETWORK_GROUP = counter.next()	
ART_DOC_TEXT = counter.next()			
ART_DOC_PYTHON = counter.next()		
ART_DOC_JAVA = counter.next()			
ART_DOC_SCRIPT = counter.next()		
ART_DOC_BOO = counter.next()			
ART_DOC_RUBY = counter.next()			
ART_DOC_PHP = counter.next()			
ART_DOC_RSS = counter.next()			
ART_DOC_HTML = counter.next()			
ART_DOC_PDF = counter.next()			
ART_IMAGE = counter.next()			
ART_DOC_GENERIC = counter.next()
ART_PREFERENCES_DESKTOP = counter.next()		
ART_PREFERENCES = counter.next()		
ART_PREFS_EDITOR = counter.next()		
ART_LINT = counter.next()
ART_TYPE_AUDIO = counter.next()
ART_SYSTEM = counter.next()	

class TangoArtProvider(wx.ArtProvider):
    """An ArtProvider for Tango Icons.
    To use, add
    art = TangoArt.TangoArtProvider()
    wx.ArtProvider.Push(art)
    after app = wx.App() and the standard ArtProvider calls will use Tango Icons.
    
    Three sizes of icons are available, 16x16, 22x22 and 32x32. If you specify
    a client and not a size, TangoArt will do its best to pick an art size but
    if you really care, specify a wx.Size as well. If you pick a wx.Size other
    than those listed above, you'll get 16x16 art.
    
    Also Available:
    TangoArt.ART_PRINT_PREVIEW
    TangoArt.ART_SELECT_ALL
    TangoArt.ART_FOLDER_NEW
    TangoArt.ART_INDENT_MORE
    TangoArt.ART_INDENT_LESS
    TangoArt.ART_STOP 
    TangoArt.ART_TAB_NEW
    TangoArt.ART_VIEW_FULLSCREEN 
    TangoArt.ART_VIEW_REFRESH 
    TangoArt.ART_WINDOW_NEW 
    TangoArt.ART_PREFS_FONT 
    TangoArt.ART_PREFS_SHORTCUTS 
    TangoArt.ART_PREFS_LOCALE 
    TangoArt.ART_SOFTWARE_UPDATE 
    TangoArt.ART_TERMINAL 
    TangoArt.ART_FAVORITE 
    TangoArt.ART_IMPORTANT
    TangoArt.ART_READONLY 
    TangoArt.ART_FOLDER 
    TangoArt.ART_NETWORK_SERVER 
    TangoArt.ART_NETWORK_FOLDER 
    TangoArt.ART_NETWORK_GROUP
    
    wx.ART overridden:
    NEW, FILE_OPEN, PRINT, FILE_SAVE_AS, FILE_SAVE, COPY, CUT, PASTE, FIND,
    FND_AND_REPLACE, REDO, UNDO, HELP, FOLDER, ERROR, WARNING
    """
    def __init__(self, path):
        wx.ArtProvider.__init__(self)
        self.logger = logging.getLogger('TangoArt')
        self.path = path
    
    def CreateBitmap(self, artid, client=wx.ART_OTHER, size=0):
        """Adds and overrides art to the standard ArtProvider set. It is called
        by wx.ArtProvider when you push an instance to wx.ArtProvider. Don't
        call it explicitly."""
        
        if artid not in self.iconDict:
            return wx.NullBitmap
        if size.GetHeight() != -1:
            height = size.GetHeight()
            if height is not 16 and height is not 32 and height is not 22 \
            and height is not 10 and height is not 24:
                height = 16
        elif client is wx.ART_BUTTON or client is wx.ART_OTHER:
            height = 22
        elif client is wx.ART_TOOLBAR or client is wx.ART_CMN_DIALOG or \
            client is wx.ART_MESSAGE_BOX or client is wx.ART_HELP_BROWSER:
            height = 32
        else:
            height = 16
        icon = self.path + '/' + str(height)+'x'+str(height) + '/' + self.iconDict[artid] + '.png'
        self.logger.info('Seeking file ' + str(icon))
        bmp = wx.Image(icon, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        return bmp
    
    iconDict = {
        wx.ART_NEW : 'actions/document-new',
        wx.ART_FILE_OPEN : 'actions/document-open',             
        ART_PRINT_PREVIEW : 'actions/document-print-preview',   
        wx.ART_PRINT : 'actions/document-print',
        wx.ART_FILE_SAVE_AS : 'actions/document-save-as',       
        wx.ART_FILE_SAVE : 'actions/document-save',             
        wx.ART_COPY : 'actions/edit-copy',  
        wx.ART_CUT : 'actions/edit-cut',                        
        wx.ART_PASTE : 'actions/edit-paste',
        wx.ART_FIND : 'actions/edit-find',
        wx.ART_FIND_AND_REPLACE : 'actions/edit-find-replace',  
        wx.ART_REDO : 'actions/edit-redo',                      
        ART_SELECT_ALL : 'actions/edit-select-all',             
        wx.ART_UNDO : 'actions/edit-undo',                      
        ART_FOLDER_NEW : 'actions/folder-new',                  
        ART_INDENT_MORE : 'actions/format-indent-more',         
        ART_INDENT_LESS : 'actions/format-indent-less',
        ART_LIST_ADD :  'actions/list-add',
        ART_LIST_REMOVE :  'actions/list-remove',
        ART_STOP : 'actions/process-stop',                      
        ART_TAB_NEW : 'actions/tab-new',                    
        ART_VIEW_FULLSCREEN : 'actions/view-fullscreen',
        ART_VIEW_REFRESH : 'actions/view-refresh',              
        ART_WINDOW_NEW : 'actions/window-new',                  
        wx.ART_HELP : 'actions/help-browser',                   
        ART_PREFS_FONT : 'actions/preferences-desktop-font',    
        ART_PREFS_SHORTCUTS : 'actions/preferences-desktop-keyboard-shortcuts', 
        ART_PREFS_LOCALE : 'actions/preferences-desktop-locale',
        ART_SOFTWARE_UPDATE : 'actions/system-software-update', 
        ART_TERMINAL : 'actions/utilities-terminal',            
        ART_FAVORITE : 'actions/emblem-favorite',               
        ART_IMPORTANT : 'actions/emblem-important',             
        ART_READONLY : 'actions/emblem-readonly',
        wx.ART_FOLDER : 'places/folder',                       
        ART_NETWORK_SERVER : 'actions/network-server',
        ART_NETWORK_FOLDER : 'actions/folder-remote',           
        ART_NETWORK_GROUP : 'actions/network-workgroup',    
        wx.ART_ERROR : 'status/dialog-error',
        wx.ART_WARNING : 'status/dialog-warning',
        ART_DOC_TEXT : 'actions/text-x-generic',
        ART_DOC_PYTHON : 'actions/text-x-python',
        ART_DOC_JAVA : 'actions/text-x-java-source',
        ART_DOC_SCRIPT : 'actions/text-x-script',
        ART_DOC_BOO : 'actions/text-x-boo',
        ART_DOC_RUBY : 'actions/application-x-ruby',
        ART_DOC_PHP : 'actions/application-x-php',
        ART_DOC_RSS : 'actions/rss',
        ART_DOC_HTML : 'actions/text-html',
        ART_DOC_PDF : 'actions/gnome-mime-application-pdf',
        ART_DOC_GENERIC : 'actions/file-generic',
        ART_IMAGE : 'actions/image-x-generic',
        ART_PREFERENCES_DESKTOP: 'categories/preferences-desktop',
        ART_PREFERENCES :  'categories/preferences-system',
        ART_PREFS_EDITOR: 'actions/accessories-text-editor',
        ART_LINT: 'actions/edit-clear',
        ART_MEDIA_PLAYBACK_START : 'actions/media-playback-start',
        ART_MEDIA_PLAYBACK_STOP : 'actions/media-playback-stop',
        ART_EDIT_CLEAR : 'actions/edit-clear',
        ART_TYPE_AUDIO : 'mimetypes/audio-x-generic',
        ART_SYSTEM : 'emblems/emblem-system'
    }
