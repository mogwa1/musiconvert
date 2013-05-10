#!/usr/bin/python

import sys
import os
import string
import re

class counter:
    current=0
    total=0

class shell:    
    def parseEscapechars(self,file,quoteonly=False):

        if(quoteonly == False):
            #characters which must be escaped in the shell, note
            #"[" and "]" seems to be automatically escaped
            #(strange, look into this)
            escChars = ["\"","*",";"," ","'","(",")","&","`"]

            for char in escChars:
                #add an escape character to the character
                file = string.replace(file, char, '\\' + char)
        else:
            file = string.replace(file, "\"", "\\\"")

        return file

    def getfiles(self,path):
        infiles = os.listdir(path) #the files going in for reading
        outfiles = [] #the files going out in a list

        for file in infiles:
	        if(os.path.isdir(os.path.join(path,file))):
	            #recursive call
	            outfiles = outfiles + self.getfiles(os.path.join(path,file))
	        else:
	            outfiles.append(os.path.join(path,file))

        return outfiles

    def getdirs(self,path):
        infiles = os.listdir(path)
        outdirs = []
        
        for file in infiles:
            if os.path.isdir(os.path.join(path,file)):
                outdirs.append(os.path.join(path,file))
                outdirs = outdirs + self.getdirs(os.path.join(path,file))
                
        return outdirs
        

class flac:
    def getmeta(self,flacfile,imagefile):
		
        os.system('{}metaflac --export-picture-to={} {}'.format(
            metaflacpath, shell().parseEscapechars(imagefile), flacfile))
        #The FLAC file format states that song info will be stored in block 2, so
        #we do not look at the other blocks
        flacdata = os.popen(
            "{}metaflac --list --block-number 2 {}".format(
				metaflacpath,flacfile))

        datalist = [] #init a list for storing all the data in this block

        #this dictionary (note different brackets) will store only the comments
        #for the music file
        commentlist = {}

        for data in flacdata.readlines():
            #get rid of any whitespace from the left to the right
            data = string.strip(data)

            #check if the tag is a comment field (shown by the first 7 chars
            #spelling out "comment")
            if(data[:8] == "comment["):
                datalist.append(string.split(data,":"))

        for data in datalist:
            #split according to [NAME]=[VALUE] structure
            comment = string.split(data[1],"=")
            comment[0] = string.strip(comment[0])
            comment[1] = string.strip(comment[1])
            #convert to upper case
            #we want the key values to always be the same case, we decided on
            #uppercase (whether the string is upper or lowercase, is dependent
            # on the tagger used)
            comment[0] = string.upper(comment[0])

            #assign key:value pair, comment[0] will be the key, and comment[1]
            #the value
            commentlist[comment[0]] = comment[1]
        return commentlist


class mp3:
    def convert(self,lameopts,infile,outfile):

        #rb stands for read-binary, which is what we are doing, with a 1024 byte buffer
        decoder = os.popen(flacpath + "flac -d -s -c " + shell().parseEscapechars(infile),'rb',1024)
        #wb stands for write-binary
        encoder = os.popen("{}lame --silent {} - -o {}.mp3".format(
            lamepath,
            lameopts,
            shell().parseEscapechars(outfile)
            ) ,'wb',8192) 

        for line in decoder.readlines(): #while data exists in the decoders buffer
            encoder.write(line) #write it to the encoders buffer

        decoder.flush() #if there is any data left in the buffer, clear it
        decoder.close() #somewhat self explanetory

        encoder.flush() #as above
        encoder.close()
        

    def tag(self,metadata,outfile,imgfile):
        eyeD3defaults = '--to-v2.3 --no-zero-padding --no-color --no-tagging-time-frame'
        outputredir = '> /dev/null 2> /dev/null'
        tagstring = ''
        if 'ARTIST' in metadata: 
            tagstring += '--artist="{}" '.format(metadata['ARTIST'])
        if 'ALBUM' in metadata: 
            tagstring += '--album="{}" '.format(metadata['ALBUM'])
        if 'TITLE' in metadata:
            tagstring += '--title="{}" '.format(metadata['TITLE'])
        if 'GENRE' in metadata:
            tagstring += '--genre="{}" '.format(metadata['GENRE'])
        if 'DATE' in metadata:
            tagstring += '--year="{}" '.format(metadata['DATE'])
        if 'COMMENT' in metadata:
            tagstring += '--comment=::"{}" '.format(metadata['COMMENT'])
        if 'TRACKNUMBER' in metadata:
            tagstring += '--track="{}" '.format(metadata['TRACKNUMBER'])
        if 'TRACKTOTAL' in metadata:
            tagstring += '--set-user-text-frame=TOTALTRACKS:"{}" '.format(metadata['TRACKTOTAL'])
        if 'DISCNUMBER' in metadata:
            tagstring += '--set-text-frame=TPOS:"{}" '.format(metadata['DISCNUMBER'])
        if 'DISCTOTAL' in metadata:
            tagstring += '--set-user-text-frame=TOTALDISCS:"{}" '.format(metadata['DISCTOTAL'])
        if 'ALBUMARTIST' in metadata:
            tagstring += '--set-text-frame=TPE2:"{}" '.format(metadata['ALBUMARTIST'])
        if 'COMPOSER' in metadata:
            tagstring += '--set-text-frame=TCOM:"{}" '.format(metadata['COMPOSER'])
        if 'PERFORMER' in metadata:
            tagstring += '--set-user-text-frame=PERFORMER:"{}" '.format(metadata['PERFORMER'])
        if os.path.exists(imgfile):
            tagstring += '--add-image={!s}:FRONT_COVER: '.format(
                shell().parseEscapechars(imgfile))
       
        #print tagstring
       
        if tagstring != '':
            os.system('{}eyeD3 {} {} {}.mp3 {}'.format(
                eyeD3path,eyeD3defaults,
                tagstring,shell().parseEscapechars(outfile), outputredir))
            os.system('{}eyeD3 --to-v1.1 --no-color {}.mp3 {}'.format(
                eyeD3path,shell().parseEscapechars(outfile), outputredir))
		
        if os.path.exists(imgfile):
            os.system('rm -f {}'.format(shell().parseEscapechars(imgfile)))

    def gain(self, current_dir):
            os.system('{}mp3gain -a -k -q {} > /dev/null'.format(mp3gainpath,
                os.path.join(shellInst.parseEscapechars(current_dir),'*.mp3')))


def header():
    return """Flac2mp3 python script, v1.0"""
def infohelp():
    return """flac2mp3 [convert type] [input dir] <options>
where \'convert type\' is one of:
\t [mp3]: convert file to mp3
\t [vorbis]: convert file to ogg vorbis
\t [flac]: convert file to flac
\t [aacplusNero]: convert file to aacplus using the proprietery (but excellent) Nero AAC encoder."""


def encode_thread(current_file,filecounter,opts):
    #Recursive directory creation script, if selected
    if (opts['nodirs'] == False):
    #remove the dirpath placed in parameters, so that we work from that
    #directory
        current_file_local = current_file.replace(opts['dirpath'],'')
        outdirFinal = opts['outdir'] + os.path.split(current_file_local)[0]
	
        #if the path does not exist, then make it
        if (os.path.exists(outdirFinal) == False):
            #the try/catch here is to deal with race condition, sometimes one
            #thread creates the path before the other, causing errors
            try:
                #recursive, will make the entire path if required
                os.makedirs(outdirFinal)
            except(OSError):
                print "Directory already exists! Reusing..."

    #this chunk of code provides us with the full path sans extension
    outfile = os.path.join(outdirFinal,os.path.split(current_file_local)[1])
    #return the name on its own, without the extension
    outfile = string.split(outfile, ".flac")[0]
    #This part deals with copying non-music data over (so everything that isn't
    #a flac file)
    if (string.lower(current_file [-4:]) != "flac"):
        if (opts['copy'] == True):
            print "Copying file ({}) to destination".format(
                current_file.split('/')[-1])
            os.system("cp \"{}\" \"{}\"".format(current_file,outdirFinal) )
            return 1

    else:
        filecounter.current += 1 #increment the file we are doing

        #the below is because "vorbis" is "ogg" extension, so we need the right extension
        #if we are to correctly check for existing files.
        if opts['mode'] == "vorbis":
            ext = "ogg"
        else:
            ext = opts['mode']

        if ( os.path.exists(outfile + "." + ext) and (opts['overwrite'] == False) ):
            print "file #{} of {} exists, skipping".format(
                filecounter.current, filecounter.total)
        else:
            #[case insensitive] check if the last 4 characters say flac (as in
            #flac extension, if it doesn't, then we assume it is not a flac
            #file and skip it
            if (string.lower(current_file [-4:]) == "flac"):
				#get metadata from input file
                imgfile = outfile+".jpeg"

                if (opts['mode'] != "test"):
                    print "converting file #{} of {} to {}:".format(
                        filecounter.current, filecounter.total, opts['mode']),
                    print os.path.split(current_file)[1]
                else:
                    print "testing file #{} of {}".format(
                        filecounter.current,filecounter.total)

                if(opts['mode'] == "mp3"):
                    mp3Inst.convert(opts['lameopts'],current_file,outfile)
                    metadata = flacInst.getmeta(
                        shellInst.parseEscapechars(current_file),imgfile)
                    mp3Inst.tag(metadata,outfile,imgfile)
                elif(opts['mode'] == "flac"):
                    flacClass.flacconvert(opts['flacopts'],current_file,outfile)
                elif(opts['mode'] == "vorbis"):
                    vorbisClass.oggconvert(opts['oggencopts'],current_file,outfile)
                elif(opts['mode'] == "aacplusNero"):
                    aacpClass.AACPconvert(opts['aacplusopts'],current_file,outfile)
                elif(opts['mode'] == "test"):
                    flacClass.flactest(current_file, outfile)
                else:
                    print "Error, Mode {} not recognised. Thread dying".format(opts['mode'])
                    sys.exit(-2)
                    
        return 1 


def post_processing(current_dir,dircounter,opts):
    if opts['mode'] == "vorbis":
        ext = "ogg"
    else:
        ext = opts['mode']

    if (opts['gain'] == True):
        if glob(os.path.join(current_dir,'*.{}'.format(ext))):
            dircounter.current += 1
            print 'Applying gain to dir #{} of {}: {}'.format(
                dircounter.current, dircounter.total, os.path.split(current_dir)[1])
            mp3Inst.gain(current_dir)
                



shellInst = shell()
flacInst = flac()
mp3Inst = mp3()
cnt = counter()

metaflacpath=''
flacpath=''
lamepath=''
eyeD3path=''
mp3gainpath=''

opts = {
"outdir":"./", #the directory we output to, defaults to current directory
"overwrite":False, #do we overwrite existing files
"nodirs":False, #do not create directories (dump all files into single dir)
"threads":2, #How many encoding threads to run simultaniously.
"copy":False, #Copy non flac files (default is to ignore)
"lameopts":"-V2", #your mp3 encoding settings
"oggencopts":"quality=2", # your vorbis encoder settings
"flacopts":"-q 8", #your flac encoder settings
"aacplusopts":"-q 0.3 ",
"gain":False
}

#This area deals with checking the command line options,

from optparse import OptionParser

parser = OptionParser(usage=infohelp())
parser.add_option("-c","--copy",action="store_true",dest="copy",
      default=False,help="Copy non flac files across (default=False)")

parser.add_option("-v","--vorbis-options",dest="oggencopts",
      default="quality=2",help="Colon delimited options to pass to oggenc,for example:" +
      " 'quality=5:resample 32000:downmix:bitrate_average=96'." +
      " Any oggenc long option (one with two '--' in front) can be specified in the above format.")
parser.add_option("-l","--lame-options",dest="lameopts",
      default="V2",help="Options to pass to lame, for example:           '-preset extreme:q 0:h:-abr'. "+
      "Any lame option can be specified here, if you want a short option (e.g. -h), then just do 'h'. "+
      "If you want a long option (e.g. '--abr'), then you need a dash: '-abr'")
parser.add_option("-a","--aacplus-options",dest="aacplusopts",
      default="-q 0.3", help="AACplus options, currently only bitrate supported. e.g: \" -a 64 \""),
parser.add_option("-o","--outdir",dest="outdir",metavar="DIR", 
      help="Set custom output directory (default='./')",
      default="./"),
parser.add_option("-f","--force",dest="overwrite",action="store_true",
      help="Force overwrite of existing files (by default we skip)",
      default=False),
parser.add_option("-t","--threads",dest="threads",default=2,
      help="How many encoding threads to run in parallel (default 2)")
parser.add_option("-n","--nodirs",dest="nodirs",action="store_true",
      default=False,help="Don't create Directories, put everything together")
parser.add_option("-g","--gain",dest="gain",action="store_true",
      default=False,help="Run gain album analysis on folder level")


(options,args) = parser.parse_args()

#update the opts dictionary with new values
opts.update(eval(options.__str__()))

#convert the formats in the args to valid formats for lame and oggenc
opts['oggencopts'] = ' --'+' --'.join(opts['oggencopts'].split(':'))
#lame is stupid, it is not consistent, somteims using long opts, sometimes not
#so we need to specify on command line with dashes whether it is a long op or short
opts['lameopts'] = ' -'+' -'.join(opts['lameopts'].split(':'))

print header()
#pdb.set_trace()
try:
    opts['mode'] = args[0]

except(IndexError): #if no arguments specified
    print "No mode specified! Run with '-h' for help"
    sys.exit(-1) #quit the program with non-zero status

try:
    opts['dirpath'] = os.path.realpath(args[1])

except(IndexError):
    print "No directory specified! Run with '-h' for help"
    sys.exit(-1) #quit the program with non-zero status

#end command line checking

#start main code


opts['dirpath']= os.path.abspath(opts['dirpath'])
opts['outdir']= os.path.abspath(opts['outdir'])


filelist=shellInst.getfiles(opts['dirpath'])
filelist.sort(reverse=True)

flacnum = 0 #tells us number of flac media files
filenum = 0 #tells us number of files

for files in filelist:
    filenum += 1
    #make sure both flac and FLAC are read
    if (string.lower(files [-4:]) == "flac"):
        flacnum += 1


print "There are {!s} files, of which {!s} are convertable FLAC files".format(
    filenum,flacnum)
 
if flacnum == 0:
    print "Error, we got no flac files. Are you sure you put in the correct directory?"
    sys.exit(-1) 
    
cnt.current = 0 #keep track of number of files we have done
cnt.total = flacnum

#Why did we not use "for file in filelist" for the code below? Because this is
#more flexible. As an example for multiple file encoding simultaniously, we
#can do filelist.pop() multiple times (well, along with some threading, but its
#good to plan for the future.

import threading,time
#one thread is always for the main program, so if we want two encoding threads,
#we need three threads in total
opts['threads'] = int(opts['threads']) + 1

while len(filelist) != 0: #while the length of the list is not 0 (i.e. not empty)
    #remove and return the first element in the list
    current_file = filelist.pop()

    threading.Thread(target=encode_thread,args=(
        current_file,
        cnt,
        opts
        )
    ).start()
    
    #Don't use threads, single process, used for debugging
    #encode_thread(current_file,x,opts)
    while threading.activeCount() == opts['threads']:
        #just sit and wait. we check every tenth second to see if it has
        #finished
        time.sleep(0.1)
 
 
# postprocessing of mp3gain etc

from glob import glob

dircnt = counter()
dirlist=shellInst.getdirs(opts['outdir'])
dirlist.append(opts['outdir'])
dirlist.sort(reverse=True)

# rough count, we assume that the files we want to count contain dots, and dirs not
for current_dir in dirlist:
    if glob(os.path.join(current_dir,'*.*')):
        dircnt.total += 1

while len(dirlist) != 0:
    current_dir = dirlist.pop()
    
    threading.Thread(target=post_processing,args=(
        current_dir,
        dircnt,
        opts
        )
    ).start()
 
    while threading.activeCount() == opts['threads']:
        #just sit and wait. we check every tenth second to see if it has
        #finished
        time.sleep(0.1)
 
#END

