#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  musiconvert.py, version 0.1
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
import argparse
import os
import sys
import multiprocessing
import time
import shutil
import subprocess
import shlex
import glob
import tempfile
import eyed3
import eyed3.mp3
from eyed3.id3.frames import ImageFrame
import unicodedata

def header():
    return """MusiConvert python script, v0.1"""

def setexternalpaths(opts):
    opts['flacpath'] = os.path.abspath('C:/Program Files (x86)/FLAC/flac.exe')
    opts['metaflacpath'] = os.path.abspath('C:/Program Files (x86)/FLAC/metaflac.exe')
    opts['lamepath'] = os.path.abspath('C:/Program Files (x86)/Lame/lame.exe')
    opts['mp3gainpath'] = os.path.abspath('C:/Program Files (x86)/MP3Gain/mp3gain.exe')
    return opts


class shell(object):
    def parseEscapechars(self, path):
        #characters which must be escaped in the shell, note
        #"[" and "]" seems to be automatically escaped
        #add 'long' hyphen
        escChars = ["\"","*",";"," ","'","(",")","&","`"]

        for char in escChars:
            #add an escape character to the character
            path = path.replace(char, '\\' + char)
        return path

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


class audioformat(object):
    def __init__(self, opts):
        self.opts = opts
        
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
        
    def albumgain(self, outfiles):
        pass


class flac(audioformat):
    def getdecoder(self, infile):
        command = [self.opts['flacpath'], '-d', '-s', '-c', infile]
        decoder = subprocess.Popen(command, shell=False, bufsize=1024, 
                                   stdout=subprocess.PIPE).stdout
        return decoder

    def gettags(self, infile, imgfilename):
        command = [self.opts['metaflacpath'], 
                   '--export-picture-to='+imgfilename, infile]
        subprocess.call(command)
        
        #The FLAC file format states that song info will be stored in block 2, so
        #we do not look at the other blocks
        command = [self.opts['metaflacpath'], '--list', '--block-number',
                   '2', infile]
        flacdata = subprocess.Popen(command, stdout=subprocess.PIPE).stdout

        datalist = [] #init a list for storing all the data in this block

        #this dictionary (note different brackets) will store only the comments
        #for the music file
        commentlist = {}

        for data in flacdata.readlines():
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
    tag_id = {'ARTIST'      : 'TPE1',
              'TITLE'       : 'TIT2',
              'ALBUM'       : 'TALB',
              'DATE'        : 'TYER',
              'TRACKNUMBER' : 'TRCK',
              'TRACKTOTAL'  : 'TXXX TOTALTRACKS',
              'DISCNUMBER'  : 'TPOS',
              'DISCTOTAL'   : 'TXXX TOTALDISCS',
              'ALBUMARTIST' : 'TXXX ALBUMARTIST',
              'PERFORMER'   : 'TXXX PERFORMER',
              'COMPOSER'    : 'TCOM',
              'COMMENT'     : 'COMM'}
    
    def encode(self, decoder, outfile):
        command = [self.opts['lamepath'], '--silent'] + \
                   shlex.split(self.opts['lameopts']) + \
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
            for label in mp3.tag_id:
                if metadata[label]:
                    if mp3.tag_id[label][:4] == 'TXXX':
                        audiofile.tag.user_text_frames.set(
                                metadata[label], mp3.tag_id[label][5:])
                    else:
                        audiofile.tag.setTextFrame(mp3.tag_id[label], 
                                                   metadata[label])

            try:
                audiofile.tag._setGenre(metadata['GENRE'])
            except TypeError:
                if self.opts['verbose']:
                    print('         --> genre not recognized:',
                          metadata['GENRE'])
            if os.path.isfile(imgfilename):
                img_type = ImageFrame.FRONT_COVER
                img_mt = eyed3.utils.guessMimetype(imgfilename)
                if img_mt:
                    with open(imgfilename, "rb") as img_fp:
                        audiofile.tag.images.set(
                                img_type, img_fp.read(), img_mt)
            audiofile.tag.save(version=eyed3.id3.ID3_V2_3)
            audiofile.tag.save(version=eyed3.id3.ID3_V1_1)
            
    def albumgain(self, outfiles):
        command = [self.opts['mp3gainpath'], '-a', '-k', '-q'] + outfiles
        with open(os.devnull, 'w') as fnull:
            subprocess.call(command, stdout=fnull)

    def trackgain(self, outfile):
        command = [self.opts['mp3gainpath'], '-r', '-k', '-q', outfile]
        with open(os.devnull, 'w') as fnull:
            subprocess.call(command, stdout=fnull)


def encode_process(filename, opts, informat, 
                   outformat):
    current_file_local = filename.replace(opts['indir'],'')
    outdirFinal = opts['outdir'] + os.path.dirname(current_file_local)
    
    #if the path does not exist, then make it
    if not os.path.exists(outdirFinal):
        try: # needed for race conditions
            #recursive, will make the entire path if required
            os.makedirs(outdirFinal)
        except(OSError):
            print('Directory already exists! Reusing...')

    outfile = os.path.join(outdirFinal,os.path.basename(current_file_local))
    outfile_noext = os.path.splitext(outfile)[0]
    outfile = outfile_noext + '.' + opts['outext']

    # get pipe from decoder
    decoder = informat.getdecoder(filename)
    # hand pipe over to encoder
    outformat.encode(decoder, outfile)
    
    # get tags from input file
    imgfile = os.path.join(opts['tempdir'], 
                           os.path.basename(outfile_noext+'.jpeg'))
    tags = informat.gettags(filename, imgfile)
    # write tags to output file
    outformat.settags(tags, outfile, imgfile)
    # remove imagefile if it exists
    if os.path.exists(imgfile):
        os.remove(imgfile)
        
    if opts['trackgain']:
        if opts['verbose']:
            print('         Applying track gain to: ', outfile)
        outformat.trackgain(outfile)


def convert_dir(opts):
    #check if input path is really a directory
    if not os.path.isdir(opts['indir']):
        print('ABORT: The given input path is not a directory!  Please provide a directory.')
        return

    if opts['informat'] == 'vorbis':
        opts['ext'] = 'ogg'
    else:
        opts['ext'] = opts['informat']

    if opts['outformat'] == 'vorbis':
        opts['outext'] = 'ogg'
    else:
        opts['outext'] = opts['outformat']

    # get list of files
    filelist = shell().getfiles(opts['indir'], opts['recursive'])

    # make function to check whether file has the right extension
    hasinputextension = shell().makeextensionchecker(opts['ext'])
    hasoutputextension = shell().makeextensionchecker(opts['outext'])

    # get total number of files and number of files that match the input type,
    # i.e. files that need to be converted
    filenr = len(filelist)
    convertlist = [x for x in filelist if hasinputextension(x)]
    convertnr = len(convertlist)
    otherlist = [x for x in filelist if not hasinputextension(x)]
    othernr = len(otherlist)

    if opts['verbose']:
        if convertnr == 0:
            print('ABORT: No {} files found. Are you sure this is '
                  'the correct directory?'
                  .format(opts['ext'].lower()))
        else:
            print('There are {} files, of which {} are convertible {} files'
                  .format(filenr, convertnr, opts['ext'].lower()))



    # make sure output directory exists
    # create it if necessary
    if not os.path.exists(opts['outdir']):
        os.makedirs(opts['outdir'])

    # create temporary directory to store imagefiles
    opts['tempdir'] = tempfile.mkdtemp()

    # first copy all the non-audio files to the output directory
    if opts['copy'] and (opts['indir'] != opts['outdir']):
        for current_file in otherlist:
            # remove the indir placed in parameters, so that we 
            # work from that directory
            current_file_local = current_file.replace(opts['indir'],'')
            outdirFinal = opts['outdir'] + os.path.split(current_file_local)[0]
    
            #if the path does not exist, then make it
            if not os.path.exists(outdirFinal):
                os.makedirs(outdirFinal)
            if opts['verbose']:
                print("Copying file ({}) to destination".format(
                      os.path.basename(current_file)))
            shutil.copy(current_file, outdirFinal)
    
    # create conversion objects
    inputformat = None
    if opts['informat'] == 'mp3':
        inputformat = mp3(opts)
    elif opts['informat'] == 'flac':
        inputformat = flac(opts)
        
    outputformat = None
    if opts['outformat'] == 'mp3':
        outputformat = mp3(opts)
    elif opts['outformat'] == 'flac':
        outputformat = flac(opts)
    
    # do file conversion using separate processes
    nrprocessed = 0
    while convertlist: # as long as list is not empty
        current_file = convertlist.pop()

        nrprocessed += 1
        if opts['verbose']:
            print('Converting {}/{}: {}'
                  .format(nrprocessed, convertnr, 
                          os.path.basename(current_file)))

        process = multiprocessing.Process(
                        target=encode_process,
                        args=(current_file, opts,
                              inputformat, outputformat))
        process.start()
        # use line below to stop multithreading
        #encode_process(current_file, opts, inputformat, outputformat)

        # check if number of running processes has reached the maximum
        # if so, just sit and wait
        while len(multiprocessing.active_children()) >= opts['threads']:
            time.sleep(0.1)

    # wait for final process to finish
    while len(multiprocessing.active_children()) > 0:
        time.sleep(0.1)
            
    # repeat similar loop for directories if album gain is needed
    if opts['albumgain']:
        dirlist = shell().getdirs(opts['outdir'], opts['recursive'])
        # filter out the directories that don't contain input files
        dirlist = [x for x in dirlist 
                   if glob.glob(os.path.join(x, '*.'+opts['outext']))]
        dirtotal = len(dirlist)
        dirnr = 0
        while dirlist:
            current_dir = dirlist.pop()
            dirfiles = glob.glob(os.path.join(current_dir,
                                              '*.'+opts['outext']))
            dirnr += 1
            if opts['verbose']:
                print('Applying album gain {}/{}: {}'
                      .format(dirnr, dirtotal, 
                              os.path.basename(current_dir)))
            process = multiprocessing.Process(
                            target=outputformat.albumgain,
                            args=(dirfiles,))
            process.start()
            # check if number of running processes has reached the maximum
            # if so, just sit and wait
            while len(multiprocessing.active_children()) >= opts['threads']:
                time.sleep(0.1)
            
    # wait for final process to finish
    while len(multiprocessing.active_children()) > 0:
        time.sleep(0.1)
        
    # delete temporary directory
    # print('temporary directory is ', opts['tempdir'])
    shutil.rmtree(opts['tempdir'])


def parse_arguments():
    parser = argparse.ArgumentParser(description='Convert audio files to different format '
                                                 'including tagging and volume normalization.')
    parser.add_argument('indir', metavar='DIR', type=unicode,
                        help='Directory containing audio files to be converted.')
    parser.add_argument('-i', '--input-format', dest='informat', metavar='IN_FORMAT',
                        default='flac', type=unicode,
                        help='Format to convert from (Default is "flac").  Currently '
                        'only "flac" is supported.')
    parser.add_argument('-o', '--output-format', dest='outformat', metavar='OUT_FORMAT',
                        default='mp3', type=unicode,
                        help='Format to convert to (Default is "mp3"). '
                        'Currently only "mp3" is supported.')
    parser.add_argument('-c', '--copy', action='store_true', dest='copy',
                        default=False, help='Copy non-audio files across (default=False).')
    parser.add_argument('-l', '--lame-options', dest='lameopts', default='-V2', type=unicode,
                        help='Options to pass to lame (mp3 encoder), for example: '
                        '"--preset extreme -q 0 -h --abr". Default is "-V2".')
    parser.add_argument('-od', '--outdir', dest='outdir', metavar='OUT_DIR', type=unicode,
                        help='Set custom output directory (default="./")', default='./'),
    parser.add_argument('-f', '--force', dest='overwrite', action='store_true',
                        help='Force overwrite of existing files (default=False).',
                        default=False),
    parser.add_argument('-t', '--threads', dest='threads', type=int, default=1,
                        help='How many encoding threads to run in parallel (default 1).')
    parser.add_argument('-n', '--nodirs', dest='nodirs', action='store_true', default=False,
                        help='Don\'t create subdirectories, put everything together '
                        '(Default=False).')
    parser.add_argument('-r', '--recursive', dest='recursive', action='store_true',
                        default=False, help='Recursively loop trough subdirectories '
                        'of the given input directory (default=False).')
    parser.add_argument('-s', '--silent', dest='verbose', action='store_false',
                        default=True, help='Suppress output to terminal (Default=False).')
    gaingroup = parser.add_mutually_exclusive_group()
    gaingroup.add_argument('-ga', '--album-gain', dest='albumgain', action='store_true',
                        default=False, help='Run album gain analysis on folder level '
                        '(default=False).')
    gaingroup.add_argument('-gt', '--track-gain', dest='trackgain', action='store_true',
                        default=False, help='Run track gain analysis '
                        '(default=False).')

    opts = vars(parser.parse_args()) #translate from namespace to dictionary using vars
    # make a few option variables nicer
    opts['indir'] = os.path.abspath(opts['indir'])
    opts['outdir'] = os.path.abspath(opts['outdir'])
    opts['informat'] = opts['informat'].lower()
    opts['outformat'] = opts['outformat'].lower()
    return opts
    
           
def main():
    opts = parse_arguments()
 
    if opts['verbose']:
        print(header())

    opts = setexternalpaths(opts)
    convert_dir(opts)
    
    return 0


if __name__ == '__main__':
    main()
