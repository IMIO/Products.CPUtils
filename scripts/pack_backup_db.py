#!/usr/bin/python
#
"""
    This script treats dbs of a zope instance :
    * packing each db
    * backuping with repozo each fs file
"""

import sys, urllib, os
import datetime
import shutil
from datetime import datetime 

method = 'cputils_pack_db'
module = 'CPUtils.utils'
function = 'pack_db'
buildout_inst_type = None #True for buildout, False for manual instance
BACKUP_DIR = '/srv/backups/zope'

def verbose(*messages):
    print '>>', ' '.join(messages)
def error(*messages):
#    print >>sys.stderr, '!!', (' '.join(messages))
    print '!!', (' '.join(messages))

#------------------------------------------------------------------------------

class MyUrlOpener(urllib.FancyURLopener):
    def prompt_user_passwd(self, host, realm):
        return (user,pwd)
    def __init__(self, *args):
        self.version = "Zope Packer"
        urllib.FancyURLopener.__init__(self, *args)

#------------------------------------------------------------------------------

def runCommand(cmd):
    """ run an os command and get back the stdout and stderr outputs """
    ret = os.system(cmd + ' >_cmd_zr.out 2>_cmd_zr.err')
    stdout = stderr = []
    try:
        if os.path.exists('_cmd_zr.out'):
            ofile = open( '_cmd_zr.out', 'r')
            stdout = ofile.readlines()
            ofile.close()
            os.remove('_cmd_zr.out')
        else:
            error("File %s does not exist" % '_cmd_zr.out')
    except IOError:
        error("Cannot open %s file" % '_cmd_zr.out')
    try:
        if os.path.exists('_cmd_zr.err'):
            ifile = open( '_cmd_zr.err', 'r')
            stderr = ifile.readlines()
            ifile.close()
            os.remove('_cmd_zr.err')
        else:
            error("File %s does not exist" % '_cmd_zr.err')
    except IOError:
        error("Cannot open %s file" % '_cmd_zr.err')
    return( stdout,stderr )

#------------------------------------------------------------------------------

def read_zopeconffile(zodbfilename, lines):
    """ read the zope conf filename and include subfile """
    try:
        zfile = open( zodbfilename, 'r')
    except IOError:
        error("! Cannot open %s file" % zodbfilename)
        return
    for line in zfile.readlines():
        line = line.strip('\n\t ')
        if line.startswith('%include'):
            otherfilename = line.split()[1]
            read_zopeconffile(otherfilename, lines)
            continue
        lines.append(line)

#------------------------------------------------------------------------------

def treat_zopeconflines(zodbfilename):
    """
        read zope configuration lines to get informations
    """
    lines = []
    read_zopeconffile(zodbfilename, lines)

    port = ''
    httpflag = False
    fsflag = False
    dbs = []
    dbname = ''
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
            if dbname:
                error("\tnext db found while fs not found: previous dbname '%s', current line '%s'"%(dbname, line))
            dbname = line.split()[1]
            dbname = dbname.rstrip('>')
            if dbname == 'temporary':
                dbname = ''
        if line.startswith('<filestorage>'):
            fsflag = True
            continue
        if fsflag and line.startswith('path'):
            fsflag = False
            fs = line.split()[1]
            fs = os.path.basename(fs)
            dbs.append([dbname, fs])
            dbname = ''
            continue
    verbose("\tport='%s', dbs='%s'"%(port, ';'.join([','.join(dbinfo) for dbinfo in dbs])))

    if not port:
        error("! the port was not found in the config file '%s'"%zodbfilename)

    return(port, dbs)

#------------------------------------------------------------------------------

def read_zopectlfile(zopectlfilename):
    """ read the zopectl file to find the zope path """
    try:
        zfile = open( zopectlfilename, 'r')
    except IOError:
        error("! Cannot open %s file" % zopectlfilename)
        return
    zopepath = ''
    pythonfile = ''
    for line in zfile.readlines():
        line = line.strip('\n\t ')
        if line.startswith('ZOPE_HOME'):
            zopepath = line.split('=')[1]
            zopepath = zopepath.strip('"\' ')
        elif line.startswith('PYTHON'):
            pythonfile = line.split('=')[1]
            pythonfile = zopepath.strip('"\' ')
    return(zopepath, pythonfile)

#------------------------------------------------------------------------------

def packdb(port, db):
    host = "http://localhost:%s" % port
    urllib._urlopener = MyUrlOpener()
    start = datetime.now()
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
    verbose("\t\t-> elapsed time %s"%(datetime.now()-start))

#------------------------------------------------------------------------------

def backupdb(fs, zopepath, fspath, pythonfile):
    """ call the repozo script to backup file """
    repozofilename = os.path.join(zopepath, 'bin', 'repozo.py')
    pythonpath = os.path.join(zopepath, 'lib', 'python')
    if not os.path.exists(repozofilename):
        repozofilename = os.path.join(zopepath, 'utilities', 'ZODBTools', 'repozo.py')
    elif not os.path.exists(repozofilename):
        repozofilename = os.path.join(pythonpath, 'ZODB', 'scripts', 'repozo.py')
    backupcmd = "env PYTHONPATH=%s %s %s -Bv "%(pythonpath, pythonfile, repozofilename)
    if options.fullbackup:
        backupcmd += '-F '
    # -B / -R : backup or recover
    # -r backupdir
    # -F : full backup
    # -f fs file
    start = datetime.now()
    fsfilename = os.path.join(fspath, fs)
#        backupdir = os.path.join(BACKUP_DIR, os.path.basename(instdir))
#        if not os.path.exists(backupdir):
#            os.mkdir(backupdir)
    backupdir = os.path.join(BACKUP_DIR, os.path.basename(instdir), os.path.splitext(fs)[0])
    if os.path.exists(backupdir) and options.fullbackup:
        for file in shutil.os.listdir(backupdir):
            shutil.os.unlink(os.path.join(backupdir, file))
            verbose("\t%s deleted because we do a full backup" % (os.path.join(backupdir, file)))
    if not os.path.exists(backupdir):
        os.makedirs(backupdir)
    verbose("\tBackup of '%s' with script '%s'" % (fsfilename, repozofilename))    
    cmd = backupcmd + ' -r %s -f %s' % (backupdir, fsfilename)
    verbose("\tRunning command '%s'" % cmd)
    (cmd_out, cmd_err) = runCommand(cmd)

    if cmd_err:
        verbose("\t\tOutput/Error when backuping : '%s'" % "".join(cmd_err))
    elif cmd_out:
        verbose("\t\tOutput when backuping : '%s'" % "".join(cmd_out))
    else:
        error("\t\tNo output for command : '%s'" % cmd)
    verbose("\t\t-> elapsed time %s"%(datetime.now()-start))

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
        zopectlfilename = instdir + '/parts/instance/bin/zopectl'
        fspath = instdir + '/var/filestorage/'
    else:
        zodbfilename = instdir + '/etc/zope.conf'
        zopectlfilename = instdir + '/bin/zopectl'
        fspath = instdir + '/var/'

    # Getting some informations in config file
    (port, dbs) = treat_zopeconflines(zodbfilename)
    (zopepath, pythonfile) = read_zopectlfile(zopectlfilename)
    #verbose("repozo path='%s'"%zopepath)

    # Treating each db
    for db in dbs:
        packdb(port,db[0])
        backupdb(db[1], zopepath, fspath, pythonfile)

    for file in shutil.os.listdir(fspath):
        if file.endswith('.fs.old'):
            shutil.os.unlink(fspath + file)
            verbose("\t%s deleted" % (fspath + file))
        elif file.endswith('.fs.pack'):
            shutil.os.unlink(fspath + file)
            error("! .pack file found : pack not correctly ended")
            verbose("\t%s deleted" % (fspath + file))

#------------------------------------------------------------------------------

try:
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-i", "--infos", dest="infos",
                  default=None,
                  help="infos about instance formatted like: "
                       "\"instance_path;transactions_days_number;admin_user;admin_password\"")
    parser.add_option("-F", "--full", dest="fullbackup",
                  help="do a full backup, not an incremental one",
                  default=False, action="store_true")
    (options, args) = parser.parse_args()
    if options.infos.startswith('#'):
        sys.exit(0)
    instdir, days, user, pwd = options.infos.split(';')
except ValueError:
    error("Problem in parameters")
    parser.print_help()
    sys.exit(1)

if __name__ == '__main__':
    verbose("Start of packing, backuping %s, days=%s, full_backup=%s"%(instdir, days, options.fullbackup))
#    sys.exit(0)
    main()
    verbose("End of packing, backuping %s"%(instdir))
