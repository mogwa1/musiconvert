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

import musiconvert
import eyed3
import eyed3.mp3
from eyed3.id3.frames import ImageFrame
import tempfile
import os
import shutil
import tempfile
import collections
import multiprocessing as mp


def main1():
    opts = {}
    opts = musiconvert.setexternalpaths(opts)
    tempdir = tempfile.mkdtemp()
    filename = os.path.abspath('c:\\Music\\flac\\zzz - others\\.calibre\\.calibre - 2002 - Kill the Logo\\04 - .calibre - Dialogue.flac')
    outfile = os.path.splitext(filename)[0]+'.mp3'
    outfile = os.path.abspath('c:\\Personal\\convertor\\output\\01 - .calibre - E.L.I.T.E..mp3')
    imgfile = os.path.abspath('c:\\Personal\\convertor\\output\\00 - .calibre - 2002 - Kill the Logo.jpg')

    #imgfile = os.path.join(tempdir, os.path.basename(outfile)+'jpeg')
    tags = musiconvert.flac(opts).gettags(filename, imgfile)
    print(tags)
    #print(tempdir)
    #shutil.rmtree(tempdir)
    

    print(tempfile.gettempprefix())

    return 0

filelist = ['/a/b/c', '/a/b/d', '/a/b/e', '/a/b/f', 
            '/a/g/h', '/a/g/i', '/a/g/j', '/a/g/k',
            '/a/l/m', '/a/l/n', '/a/l/o', '/a/l/p']
dirlist = ['/a/b', '/a/g', '/a/l']

def trivial(nr):
    import time
    import random
    time.sleep(random.random())
    return nr
    
class generator(object):
    def __init__(self, filelist, dirlist):
        self.filelist = collections.deque(filelist)
        self.filelist2 = filelist[:]
        self.dirlist = dirlist[:]
    
    def __iter__(self):
        return self    
    
    def print(self):
        print(self.filelist, self.filelist2, self.dirlist)
    
    def remove(self, filename):
        self.filelist2.remove(filename)
    
    def next(self):
        filename = None
        dirname = None
        for i, dir in enumerate(self.dirlist):
            found = False
            for k in self.filelist2:
                if dir in k:
                    found = True
            if not found:
                try:
                    dirname = self.dirlist.pop(i)
                    break
                except IndexError:
                    pass
        if not dirname:
            try:
                filename = self.filelist.popleft()
            except IndexError:
                pass
        if filename:
            return filename
        elif dirname:
            return dirname
        else:
            raise StopIteration
    
def callback(counter):
    def f(result):
        print(result)
        counter.print()
        counter.remove(result)
    return f
    
def runpool1():
    pool = mp.Pool()
    counter = generator(filelist, dirlist)
    f = callback(counter)

    for i in counter:
        pool.apply_async(trivial, (i, ), callback = f)

    pool.close()
    pool.join()

    print('done')

def main():
    runpool1()

    

if __name__ == '__main__':
    main()

