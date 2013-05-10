#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  untitled.py
#  
#  Copyright 2012 nlv19412 <nlv19412@NXL00457>
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
#  

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
import multiprocessing as mp
import random
import time
import wx
import wx.lib.newevent
import threading
import musiconvert

(EncResultEvent, EVT_ENC_RESULT) = wx.lib.newevent.NewEvent()
(EncStopEvent,   EVT_ENC_STOP)   = wx.lib.newevent.NewEvent()

def trivial(nr):
    time.sleep(random.random())
    return nr

class encodepool(wx.EvtHandler):
    def __init__(self, win):
        self.win = win
        wx.EvtHandler.__init__(self)
        self.Bind(EVT_ENC_STOP, self.OnStop)
        self.keeprunning = False
        
    def run(self):
        self.keeprunning = True
        pool = mp.Pool()
        results = pool.imap_unordered(trivial, [i for i in xrange(10)])
        pool.close()
    
        for result in results:
            evt = EncResultEvent(value = result)
            wx.PostEvent(self.win, evt)
            if not self.keeprunning:
                pool.terminate()
                pool.join()
                print('aborted')
                return
    
        pool.join()
        print('done')
        
    def OnStop(self, e):
        self.keeprunning = False




def posteventconstructor(win):
    def f(result):
        evt = EncResultEvent(value = result)
        wx.PostEvent(win, evt)
    return f

def runpool1(win):
    postevent = posteventconstructor(win)
    pool = mp.Pool()
    for i in xrange(10):
        pool.apply_async(func = trivial, args = (i, ), 
                         callback = postevent)
    pool.close()
    pool.join()

    print('done')


class MainWindow(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title='MusiConvert v0.1')
        self.pool = encodepool(self)
        self.panel = wx.Panel(self)
        self.btn = wx.Button(self, id=wx.ID_STOP)
        self.Bind(wx.EVT_BUTTON, self.OnStop, self.btn)
        self.Bind(EVT_ENC_RESULT, self.OnResult)
        self.Show()
        threading.Thread(target=self.pool.run).start()

    def OnResult(self, e):
        print(e.value)
        
    def OnStop(self, e):
        evt = EncStopEvent()
        wx.PostEvent(self.pool, evt)


def main():
    mp.freeze_support()
    app = wx.App(False)
    frame = MainWindow(None)
    app.MainLoop()

def main1():
    diction = {'ARTIST': 'bla'}
    musiconvert.mp3.tag_id = diction
    print(musiconvert.mp3.tag_id)



if __name__ == '__main__':
    main()

