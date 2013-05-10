#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  musiconvert_func.py, version 0.1
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

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
import random
import os
import tempfile
import glob
import shlex
import shutil
import logging
import subprocess
import eyed3
import eyed3.mp3
from eyed3.id3.frames import ImageFrame
from contextlib import contextmanager

"""
Utility functions
"""

@contextmanager
def temporary_dir(*args, **kwargs):
    name = tempfile.mkdtemp(*args, **kwargs)
    try:
        yield name
    finally:
        import time
        time.sleep(5)
        shutil.rmtree(name)

@contextmanager
def working_directory(path):
    current_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(current_dir)

        

class shell(object):
    def getfiles(self, path, recursive=False):
        infiles = os.listdir(path) #the files going in for reading
        outfiles = [] #the files going out in a list

        for file in infiles:
	        if os.path.isdir(os.path.join(path,file)):
                   if recursive:
                        #recursive call
                        outfiles = outfiles + self.getfiles(os.path.join(path,file), recursive)
	        else:
	            outfiles.append(os.path.abspath(os.path.join(path,file)))
        return outfiles

    def getdirs(self, path, recursive=False):
        infiles = os.listdir(path)
        outdirs = [os.path.abspath(path)]
        
        for file in infiles:
            if (os.path.isdir(os.path.join(path,file)) and recursive):
                #outdirs.append(os.path.join(path,file))
                outdirs = outdirs + self.getdirs(os.path.join(path,file), recursive)             
        return outdirs

    def makeextensionchecker(self, mask):
        def f(file):
            masklen = len(mask)
            return file[-masklen:].lower() == mask.lower()
        return f

    def replacepath(self, filename, indir, outdir, flat=False):
        current_file_rel = os.path.relpath(filename, 
                                           os.path.abspath(indir))
        outdirFinal = os.path.abspath(outdir)
        if not flat:
            outdirFinal = os.path.join(os.path.abspath(outdir),
                                       os.path.dirname(current_file_rel))
        outfile = os.path.join(outdirFinal,
                               os.path.basename(current_file_rel))
        if (os.path.isdir(filename) and flat):
            outfile = outdirFinal
        return outfile
        
    def replaceextension(self, filename, outext):
        filename_noext = os.path.splitext(filename)[0]
        outfile = filename_noext + '.' + outext
        return outfile
        
    def uni2ascii(self, stringval):
        import unicodedata
        return unicode(unicodedata.normalize('NFKD', stringval)
                            .encode('ascii', 'replace'))


def getinputfilelists(indir, ext, recursive=True, verbose=False):
    # make function to check whether file has the right extension
    hasinputextension = shell().makeextensionchecker(ext)

    # get list of files
    filelist = shell().getfiles(indir, recursive)

    # get total number of files and number of files that match the input type,
    # i.e. files that need to be converted
    filenr = len(filelist)
    convertlist = [x for x in filelist if hasinputextension(x)]
    convertlist.sort()
    otherlist = [x for x in filelist if not hasinputextension(x)]
    otherlist.sort()
    convertnr = len(convertlist)
    
    if verbose:
        if convertnr == 0:
            print('ABORT: No {} files found. Are you sure this is '
                  'the correct directory?'
                  .format(ext.lower()))
        else:
            print('There are {} files, of which {} are convertible {} files'
                  .format(filenr, convertnr, ext.lower()))
    
    return convertlist, otherlist


def getdirlist(indir, ext, recursive=False):
    # get list of directories containing converted files
    dirlist = shell().getdirs(indir, recursive)
    # filter out the directories that don't contain input files
    indirlist = [x for x in dirlist 
                 if glob.glob(os.path.join(x, '*.'+ext))]
    # sort list
    indirlist.sort()
    return indirlist


"""
Implementation of the different audio formats
"""

class audioformat(object):
    """
    Template class to implement decoding and encoding of an audio format
    including volume normalization and tagging.  Specific codec
    implementations should inherit this class and implement all member
    functions.
    """
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.extension = ''
        self.name = ''
    
    def gettags(self, infile, imgfilename):
        pass
    
    def settags(self, metadata, outfile, imgfilename):
        pass

    def getdecoder(self, infile):
        pass

    def encode(self, decoder, outfile):
        pass
        
    def trackgain(self, outfile):
        pass
        
    def albumgain(self, outdir):
        pass


class flac(audioformat):
    def __init__(self, flacpath, metaflacpath, *args, **kwargs):
        audioformat.__init__(self, *args, **kwargs)
        self.extension = 'flac'
        self.flacpath = flacpath
        self.metaflacpath = metaflacpath

    def getdecoder(self, infile):
        command = [self.flacpath, '-d', '-s', '-c', infile]
        decoder = subprocess.Popen(command, shell=False, bufsize=1024, 
                                   stdout=subprocess.PIPE).stdout
        return decoder

    def gettags(self, infile, imgfilename):
        command = [self.metaflacpath,
                   '--export-picture-to='+imgfilename, infile]
        subprocess.call(command)
        
        #The FLAC file format states that song info will be stored in block 2, so
        #we do not look at the other blocks
        command = [self.metaflacpath, '--no-utf8-convert',
                   '--list', '--block-number', '2', infile]
        flacdata = subprocess.Popen(command, stdout=subprocess.PIPE).stdout

        datalist = [] #init a list for storing all the data in this block

        #this dictionary (note different brackets) will store only the comments
        #for the music file
        commentlist = {}

        for data in flacdata.readlines():
            data = data.decode('utf-8')
            #get rid of any whitespace from the left to the right
            data = data.strip()

            #check if the tag is a comment field (shown by the first 7 chars
            #spelling out "comment")
            if(data[:8] == "comment["):
                datalist.append(data.split(':'))

        for data in datalist:
            #split according to [NAME]=[VALUE] structure
            comment = data[1].split('=')
            comment[0] = comment[0].strip()
            comment[1] = comment[1].strip()
            #convert to upper case
            #we want the key values to always be the same case, we decided on
            #uppercase (whether the string is upper or lowercase, is dependent
            # on the tagger used)
            comment[0] = comment[0].upper()

            #assign key:value pair, comment[0] will be the key, and comment[1]
            #the value
            commentlist[comment[0]] = comment[1]
        return commentlist


class mp3(audioformat):
    def __init__(self, lamepath, mp3gainpath, lameopts, 
                 tagmapping=None, *args, **kwargs):
        audioformat.__init__(self, *args, **kwargs)
        self.extension = 'mp3'
        self.lamepath = lamepath
        self.mp3gainpath = mp3gainpath
        self.lameopts = lameopts
        if tagmapping:
            self.tagmapping = tagmapping
        else:
            self.tagmapping = { 'ARTIST'      : 'TPE1',
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
    
    def encode(self, decoder, outfile):
        command = [self.lamepath, '--silent'] + \
                   shlex.split(self.lameopts) + \
                   ['-', '-o', outfile]
        encoder = subprocess.Popen(command, shell=False, bufsize=8192, 
                                   stdin=subprocess.PIPE).stdin

        for line in decoder.readlines(): #while data exists in the decoders buffer
            encoder.write(line) #write it to the encoders buffer

        decoder.flush() #if there is any data left in the buffer, clear it
        decoder.close() #somewhat self explanetory

        encoder.flush() #as above
        encoder.close()

    def settags(self, metadata, outfile, imgfilename):
        if eyed3.mp3.isMp3File(outfile):
            audiofile = eyed3.load(outfile)
            audiofile.tag = eyed3.id3.Tag()
            audiofile.tag.file_info = eyed3.id3.FileInfo(outfile)
            audiofile.tag.version = eyed3.id3.ID3_V2_3
            audiofile.tag = self.settagfields(audiofile.tag, 
                                           metadata, imgfilename)
            try:
                audiofile.tag.save(version=eyed3.id3.ID3_V2_3)
            except UnicodeEncodeError:
                for label in metadata:
                    metadata[label] = shell().uni2ascii(metadata[label])
                audiofile.tag = self.settagfields(audiofile.tag, 
                                metadata, imgfilename)
                audiofile.tag.save(version=eyed3.id3.ID3_V2_3)
            try:
                audiofile.tag.save(version=eyed3.id3.ID3_V1_1)
            except UnicodeEncodeError:
                for label in metadata:
                    metadata[label] = shell().uni2ascii(metadata[label])
                audiofile.tag = self.settagfields(audiofile.tag, 
                                metadata, imgfilename)
                audiofile.tag.save(version=eyed3.id3.ID3_V1_1)

    def settagfields(self, tag, metadata, imgfilename):
        for label in self.tagmapping:
            if label in metadata:
                if self.tagmapping[label][:4] == 'TXXX':
                    tag.user_text_frames.set(
                            metadata[label], self.tagmapping[label][5:])
                else:
                    tag.setTextFrame(self.tagmapping[label], 
                                     metadata[label])
        if 'GENRE' in metadata:
            try:
                tag._setGenre(metadata['GENRE'])
            except TypeError:
                if self.verbose:
                    logging.warning('GENRE not recognized: {}'.format(
                                    metadata['GENRE']))
        if 'COMMENT' in metadata:
            tag.comments.set(metadata['COMMENT'])
        if os.path.isfile(imgfilename):
            img_type = ImageFrame.FRONT_COVER
            img_mt = eyed3.utils.guessMimetype(imgfilename)
            if img_mt:
                with open(imgfilename, "rb") as img_fp:
                    tag.images.set(img_type, img_fp.read(), img_mt)
        return tag

            
    def albumgain(self, outdir):
        """
        Changing current directory to avoid problems with unicode
        characters in filenames.  Also, use call to shell to be able
        to expand the wildcard.
        """
        with working_directory(outdir):
            command = [self.mp3gainpath, 
                       '-a', '-k', '-q', '*.'+self.extension]
            # This command doesn't work in linux, because of wildcard
            if os.name == 'posix':
                filelist = glob.glob('*.'+self.extension)
                command = [self.mp3gainpath, '-a', '-k', '-q'] + filelist
            with open(os.devnull, 'w') as fnull:
                subprocess.call(command, stdout=fnull)

    def trackgain(self, outfile):
        command = [self.mp3gainpath, '-r', '-k', '-q', outfile]
        with open(os.devnull, 'w') as fnull:
            subprocess.call(command, stdout=fnull)

def encode_process_star(args):
    return encode_process(*args)

def encode_process(infile, outfile, informat, outformat, verbose=False, 
                   overwrite=False, trackgain=False, tempdir='.'):
    status = ''
    outdirFinal = os.path.dirname(outfile)
    
    #if the path does not exist, then make it
    if not os.path.exists(outdirFinal):
        try: # needed for race conditions
            #recursive, will make the entire path if required
            os.makedirs(outdirFinal)
        except(OSError):
            if verbose:
                logging.warning('Directory already exists! Reusing...')

    # check if filename contains unicode characters
    unistring = False
    try:
        os.path.abspath(infile).encode('ascii')
    except UnicodeEncodeError:
        unistring = True
        
    prefix = str(random.randint(0,100000))+'-'
    tempbasename = os.path.basename(infile).encode('ascii', 'ignore')
    tempoutfile = os.path.join(tempdir, 
                               prefix+'out-'+tempbasename)
    tempoutfile_noext = os.path.splitext(tempoutfile)[0]

    # workaround for unicode infiles which are not supported by
    # subprocess.Pipe and subprocess.call
    if unistring:
        tempinfile = os.path.join(tempdir, 
                                  prefix+'in-'+tempbasename)
        tempoutfile = tempoutfile_noext  + '.' + outformat.extension
        shutil.copy(infile, tempinfile)
    else:
        tempinfile = infile
        tempoutfile = outfile

    if os.path.exists(outfile) and not overwrite:
        status = 'ok exists'
    else:
        # get pipe from decoder
        decoder = informat.getdecoder(tempinfile)
        # hand pipe over to encoder
        outformat.encode(decoder, tempoutfile)
        
        # get tags from input file
        imgfile = tempoutfile_noext+'.jpg'
        tags = informat.gettags(tempinfile, imgfile)
        # write tags to output file
        outformat.settags(tags, tempoutfile, imgfile)
        # remove imagefile if it exists
        if os.path.exists(imgfile):
            os.remove(imgfile)
        
        if trackgain:
            status = ' trackgain'
            outformat.trackgain(tempoutfile)
        
        # workaround for unicode infiles (part 2)
        if unistring:
            shutil.copy(tempoutfile, outfile)
            os.remove(tempinfile)
            os.remove(tempoutfile)

        status = 'ok'+status
    return (infile, status)


def albumgain_process_star(args):
    return albumgain_process(*args)

def albumgain_process(indir, outdir, outformat):
    outformat.albumgain(outdir)
    status = 'ok albumgain'
    return (indir, status)
