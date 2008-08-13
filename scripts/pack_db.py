#!/usr/bin/python
#

import sys, urllib, os
import datetime
import logging
import shutil

LOGFILE = '/srv/scripts3/pack.log'
#LOGFILE = 'pack.log'
method = 'cputils_pack_db'
module = 'CPUtils.utils'
function = 'pack_db'
buildout_inst_type = None #True for buildout, False for manual instance

#------------------------------------------------------------------------------

class MyUrlOpener(urllib.FancyURLopener):
    def prompt_user_passwd(self, host, realm):
        return (user,pwd)
    def __init__(self, *args):
        self.version = "Zope Packer"
        urllib.FancyURLopener.__init__(self, *args)

#------------------------------------------------------------------------------

def initLog(filename):
    """
    Initialise the logger.
    """
    log = logging.getLogger()
    hdlr = logging.FileHandler(filename, 'a')
    formatter = logging.Formatter('%(asctime)s %(levelname)-5s %(message)s')
    hdlr.setFormatter(formatter)
    log.addHandler(hdlr)
    log.setLevel(logging.DEBUG)

#------------------------------------------------------------------------------

def packdb(port, dbs):
    host = "http://localhost:%s" % port
    urllib._urlopener = MyUrlOpener()
    for db in dbs:
        log = logging.getLogger(db)
        log.info("\tPacking db '%s' for instance %s (%s days)" % (db, host, days))    
        url_spd = "%s/Control_Panel/Database/%s/%s?days:float=%s" % (host, db, method, days)
        #log.info("url='%s'"%url_spd)
        try:
            ret_html = urllib.urlopen(url_spd).read()
            if 'the requested resource does not exist' in ret_html or 'error was encountered while publishing this resource' in ret_html:
                log.info('\texternal method %s not exist : we will create it'%method)
                url_em = "%s/manage_addProduct/ExternalMethod/manage_addExternalMethod?id=%s&module=%s&function=%s&title="%(host, method, module, function)
                try:
                    ret_html = urllib.urlopen(url_em).read()
                    if 'the requested resource does not exist' in ret_html or 'error was encountered while publishing this resource' in ret_html:
                        log.error('! Cannot create external method in zope')
                    elif 'The specified module,' in ret_html:
                        log.error('! The specified module %s is not present in the instance'%module)
                    else:
                        try:
                            ret_html = urllib.urlopen(url_spd).read()
#                            if "/Control_Panel/Database/%s"%db not in ret_html:
#                                log.error("Problem during compression of %s"%db)
#                                log.debug(ret_html) 
                        except IOError, msg:
                            log.error("! Cannot open URL %s, aborting : %s" % (url_spd, msg))
                except Exception, msg:
                    log.error("! Cannot open URL %s, aborting : %s" % (url_em, msg))
        except IOError, msg:
            log.error("! Cannot open URL %s, aborting : %s" % (url_spd, msg))

#------------------------------------------------------------------------------

def main():
    initLog(LOGFILE)
    global buildout_inst_type
    log = logging.getLogger('main')

    tmp = instdir
    if tmp.endswith('/'):
        tmp = tmp[0:-1]
    log.info("Working on instance %s" % tmp)

    if os.path.exists(os.path.join(tmp,'parts')):
        buildout_inst_type = True
        log.info("\tInstance is a buildout !")
    elif os.path.exists(os.path.join(tmp,'etc')):
        buildout_inst_type = False
        log.info("\tInstance is a manual installation !")
    elif not os.path.exists(tmp) or True:
        log.error("! Invalid instance path '%s' or instance type not detected"%tmp)
        sys.exit(1)

    if buildout_inst_type:
        zodbfilename = instdir + '/parts/instance/etc/zope.conf'
    else:
        zodbfilename = instdir + '/etc/zope.conf'
    try:
        zfile = open( zodbfilename, 'r')
    except IOError:
        log.error("! Cannot open %s file" % zodbfilename)
        return
    port = ''
    httpflag = False
    dbs = []
    for line in zfile.readlines():
        line = line.lstrip()
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
    log.info("\tport='%s', dbs='%s'"%(port, ';'.join(dbs)))

    if not port:
        log.error("! the port was not found in the config file '%s'"%zodbfilename)

    packdb(port,dbs)
    
    #we delete every .old created during packing in the /var directory of the zope instance
    if buildout_inst_type:
        dir_path = instdir + '/var/filestorage/'
    else:
        dir_path = instdir + '/var/'

    for file in shutil.os.listdir(dir_path):
        if file.endswith('.fs.old'):
            shutil.os.unlink(dir_path + file)
            log.info("\t%s deleted" % (dir_path + file))
        elif file.endswith('.fs.pack'):
            shutil.os.unlink(dir_path + file)
            log.error("! .pack file found : pack not correctly ended")
            log.info("\t%s deleted" % (dir_path + file))

#------------------------------------------------------------------------------

try:
    arg = sys.argv[1]
    instdir, days, user, pwd = arg.split(';')
#    print instdir, days, user, pwd
except IndexError:
    initLog(LOGFILE)
    log = logging.getLogger('pack_db')
    log.error("No parameter found")
    sys.exit(1)
except ValueError:
    initLog(LOGFILE)
    log = logging.getLogger('pack_db')
    log.error("No enough parameters")
    sys.exit(1)

if __name__ == '__main__':
    main()
