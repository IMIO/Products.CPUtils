#!/usr/bin/python
#

import sys, urllib, os
import datetime
import shutil

method = 'cputils_pack_db'
module = 'CPUtils.utils'
function = 'pack_db'
buildout_inst_type = None #True for buildout, False for manual instance

def verbose(*messages):
    print '>>', ' '.join(messages)
def error(*messages):
    print >>sys.stderr, '!!', (' '.join(messages))

#------------------------------------------------------------------------------

class MyUrlOpener(urllib.FancyURLopener):
    def prompt_user_passwd(self, host, realm):
        return (user,pwd)
    def __init__(self, *args):
        self.version = "Zope Packer"
        urllib.FancyURLopener.__init__(self, *args)

#------------------------------------------------------------------------------

def read_file(zodbfilename, lines):
    """ read the zope conf filename and include subfile"""
    try:
        zfile = open( zodbfilename, 'r')
    except IOError:
        error("! Cannot open %s file" % zodbfilename)
        return
    for line in zfile.readlines():
        line = line.strip('\n ')
        if line.startswith('%include'):
            otherfilename = line.split()[1]
            read_file(otherfilename, lines)
            continue
        lines.append(line)

#------------------------------------------------------------------------------

def packdb(port, dbs):
    host = "http://localhost:%s" % port
    urllib._urlopener = MyUrlOpener()
    for db in dbs:
        verbose("\tPacking db '%s' for instance %s (%s days)" % (db, host, days))    
        url_spd = "%s/Control_Panel/Database/%s/%s?days:float=%s" % (host, db, method, days)
        #verbose("url='%s'"%url_spd)
        try:
            ret_html = urllib.urlopen(url_spd).read()
            if 'the requested resource does not exist' in ret_html or 'error was encountered while publishing this resource' in ret_html:
                verbose('\texternal method %s not exist : we will create it'%method)
                url_em = "%s/manage_addProduct/ExternalMethod/manage_addExternalMethod?id=%s&module=%s&function=%s&title="%(host, method, module, function)
                try:
                    ret_html = urllib.urlopen(url_em).read()
                    if 'the requested resource does not exist' in ret_html or 'error was encountered while publishing this resource' in ret_html:
                        error('! Cannot create external method in zope')
                    elif 'The specified module,' in ret_html:
                        error('! The specified module %s is not present in the instance'%module)
                    else:
                        try:
                            ret_html = urllib.urlopen(url_spd).read()
#                            if "/Control_Panel/Database/%s"%db not in ret_html:
#                                error("Problem during compression of %s"%db)
#                                log.debug(ret_html) 
                        except IOError, msg:
                            error("! Cannot open URL %s, aborting : %s" % (url_spd, msg))
                except Exception, msg:
                    error("! Cannot open URL %s, aborting : %s" % (url_em, msg))
        except IOError, msg:
            error("! Cannot open URL %s, aborting : %s" % (url_spd, msg))

#------------------------------------------------------------------------------

def main():
    global buildout_inst_type

    tmp = instdir
    if tmp.endswith('/'):
        tmp = tmp[0:-1]
    verbose("Working on instance %s" % tmp)

    if os.path.exists(os.path.join(tmp,'parts')):
        buildout_inst_type = True
        verbose("\tInstance is a buildout !")
    elif os.path.exists(os.path.join(tmp,'etc')):
        buildout_inst_type = False
        verbose("\tInstance is a manual installation !")
    elif not os.path.exists(tmp) or True:
        error("! Invalid instance path '%s' or instance type not detected"%tmp)
        sys.exit(1)

    if buildout_inst_type:
        zodbfilename = instdir + '/parts/instance/etc/zope.conf'
    else:
        zodbfilename = instdir + '/etc/zope.conf'

    lines = []
    read_file(zodbfilename, lines)

    port = ''
    httpflag = False
    dbs = []
    for line in lines:
        #verbose("=>'%s'"%line)
        if line.startswith('<http-server>'):
            httpflag = True
            continue
        if httpflag and line.startswith('address'):
            port = line.split()[1]
            httpflag = False
            continue
        if line.startswith('<zodb_db'):
            dbname = line.split()[1]
            dbname = dbname.rstrip('>')
            if dbname != 'temporary':
                dbs.append(dbname)
    verbose("\tport='%s', dbs='%s'"%(port, ';'.join(dbs)))

    if not port:
        error("! the port was not found in the config file '%s'"%zodbfilename)

    packdb(port,dbs)
    
    #we delete every .old created during packing in the /var directory of the zope instance
    if buildout_inst_type:
        dir_path = instdir + '/var/filestorage/'
    else:
        dir_path = instdir + '/var/'

    for file in shutil.os.listdir(dir_path):
        if file.endswith('.fs.old'):
            #we do no more delete fs.old to safely copy this file as zodb file
            #shutil.os.unlink(dir_path + file)
            #verbose("\t%s deleted" % (dir_path + file))
            pass
        elif file.endswith('.fs.pack'):
            shutil.os.unlink(dir_path + file)
            error("! .pack file found : pack not correctly ended")
            verbose("\t%s deleted" % (dir_path + file))

#------------------------------------------------------------------------------

try:
    arg = sys.argv[1]
    if arg.startswith('#'):
        sys.exit(0)
    instdir, days, user, pwd = arg.split(';')
#    print instdir, days, user, pwd
except IndexError:
    error("No parameter found")
    sys.exit(1)
except ValueError:
    error("No enough parameters")
    sys.exit(1)

if __name__ == '__main__':
    main()
