#!/usr/bin/python
#
"""
    Restore of zope fs file backuped with the script pack_backup_db.py.
    This restore is done on a backup system where all instances files are copied in a RSYNCDIR dir
    Zope must be installed exactly at the same place on the main server and backup server
"""

import sys, urllib, os
import datetime
import shutil
from datetime import datetime 

buildout_inst_type = None #True for buildout, False for manual instance
BACKUP_DIR = '/srv/backups/zope'
RSYNCDIR = '' # prefix dir containing the copy of the rsync command
FSTEST = True
FSREFS = False
OVW_FS = False # overwrite fs file when restoring if already exist
PYTHONBIN = ''

def verbose(*messages):
    print '>>', ' '.join(messages)
def error(*messages):
#    print >>sys.stderr, '!!', (' '.join(messages))
    print '!!', (' '.join(messages))

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
            if RSYNCDIR:
                if otherfilename.startswith('/'):
                    otherfilename = otherfilename[1:]
                otherfilename = os.path.join(RSYNCDIR, otherfilename)
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
    for line in zfile.readlines():
        line = line.strip('\n\t ')
        if line.startswith('ZOPE_HOME'):
            zopepath = line.split('=')[1]
            zopepath = zopepath.strip('"\' ')
            return zopepath
    return ''

#------------------------------------------------------------------------------

def read_buildoutfile(buildoutfilename):
    """ read the buildout file to find the python path """
    try:
        zfile = open( buildoutfilename, 'r')
    except IOError:
        error("! Cannot open %s file" % buildoutfilename)
        return
    for line in zfile.readlines():
        line = line.strip('\n\t ')
        if line.startswith('#!'):
            zfile.close()
            return line.strip('#! ')
    return PYTHONBIN

#------------------------------------------------------------------------------

def restoredb(fs, zopepath, fspath):
    """ call the repozo script to restore fs """
    repozofilename = os.path.join(zopepath, 'bin', 'repozo.py')
    pythonpath = os.path.join(zopepath, 'lib', 'python')
    if not os.path.exists(repozofilename):
        repozofilename = os.path.join(instdir, 'bin', 'repozo')
    elif not os.path.exists(repozofilename):
        repozofilename = os.path.join(zopepath, 'utilities', 'ZODBTools', 'repozo.py')
    elif not os.path.exists(repozofilename):
        repozofilename = os.path.join(pythonpath, 'ZODB', 'scripts', 'repozo.py')
    restorecmd = "env PYTHONPATH=%s %s %s -Rv "%(pythonpath, PYTHONBIN, repozofilename)
    # -B / -R : backup or recover
    # -r backupdir
    # -F : full backup
    # -f fs file to backup
    # -D date to restore
    # -o restored file name
    start = datetime.now()
    fsfilename = os.path.join(fspath, fs)
    backupdir = os.path.join(BACKUP_DIR, os.path.basename(instdir), os.path.splitext(fs)[0]) 
    if not OVW_FS and os.path.exists(fsfilename):
        error("\tfs file '%s' already exists ! Restoring in backup dir '%s' ..."%(fsfilename, backupdir))
        fsfilename = os.path.join(backupdir, fs)
        #return
    verbose("\tRestore of '%s'" % (fsfilename))    
    cmd = restorecmd + '-r %s -o %s' % (backupdir, fsfilename)
    verbose("\tRunning command '%s'" % cmd)
    (cmd_out, cmd_err) = runCommand(cmd)

    if cmd_err:
        verbose("\t\tOutput/Error when restoring : '%s'" % "".join(cmd_err))
    elif cmd_out:
        verbose("\t\tOutput when restoring : '%s'" % "".join(cmd_out))
    else:
        error("\t\tNo output for command : '%s'" % cmd)
    verbose("\t\t-> elapsed time %s"%(datetime.now()-start))

    if FSTEST:
        fstestfilename = os.path.join(zopepath, 'bin', 'fstest.py')
        if not os.path.exists(fstestfilename):
            fstestfilename = os.path.join(zopepath, 'utilities', 'ZODBTools', 'fstest.py')
        elif not os.path.exists(fstestfilename):
            fstestfilename = os.path.join(pythonpath, 'ZODB', 'scripts', 'fstest.py')
        fstestcmd = "env PYTHONPATH=%s %s %s "%(pythonpath, PYTHONBIN, fstestfilename)
        # -v : print a line by transaction
        # -vv : print a line by object
        start = datetime.now()
        verbose("\tTest of '%s'" % (fsfilename))
        cmd = fstestcmd + '%s' % (fsfilename)
        verbose("\tRunning command '%s'" % cmd)
        (cmd_out, cmd_err) = runCommand(cmd)

        if cmd_err:
            error("\t\tError when testing : '%s'" % "".join(cmd_err))
        elif cmd_out:
            error("\t\tError when testing : '%s'" % "".join(cmd_out))
        else:
            verbose("\t\tAll seems OK")
        verbose("\t\t-> elapsed time %s"%(datetime.now()-start))

    if FSREFS:
        fsrefsfilename = os.path.join(zopepath, 'bin', 'fsrefs.py')
        if not os.path.exists(fsrefsfilename):
            fsrefsfilename = os.path.join(zopepath, 'utilities', 'ZODBTools', 'fsrefs.py')
        elif not os.path.exists(fsrefsfilename):
            fsrefsfilename = os.path.join(pythonpath, 'ZODB', 'scripts', 'fsrefs.py')
        fsrefscmd = "env PYTHONPATH=%s %s %s "%(pythonpath, PYTHONBIN, fsrefsfilename)
        # -v : print a line by transaction
        # -vv : print a line by object
        start = datetime.now()
        verbose("\tTest of '%s'" % (fsfilename))
        cmd = fsrefscmd + '%s' % (fsfilename)
        verbose("\tRunning command '%s'" % cmd)
        (cmd_out, cmd_err) = runCommand(cmd)

        if cmd_err:
            verbose("\t\tError when testing : '%s'" % "".join(cmd_err))
        elif cmd_out:
            verbose("\t\tError when testing : '%s'" % "".join(cmd_out))
        verbose("\t\t-> elapsed time %s"%(datetime.now()-start))

#------------------------------------------------------------------------------

def copyfs(fs, fspath):
    """ copy the fs file in the right place """
    start = datetime.now()
    fsfilename = os.path.join(fspath, fs)
    backupdir = os.path.join(BACKUP_DIR, os.path.basename(instdir), os.path.splitext(fs)[0])
    backupfile = os.path.join(backupdir,fs)
#    if not os.path.exists(backupfile):
#        for filename in os.listdir(backupdir):
#            filepath = os.path.join(backupdir, filename)
#            if filepath.endswith('.fs'):
#                backupfile = filepath
#                break

#    if os.path.exists(fsfilename):
#        error("\tfs file '%s' already exists !"%(fsfilename))
#        return
    verbose("\tCopy of '%s' to '%s'" % (backupfile, fsfilename))    
    cmd = 'cp %s %s' % (backupfile, fsfilename)
    verbose("\tRunning command '%s'" % cmd)
    (cmd_out, cmd_err) = runCommand(cmd)
    if cmd_err:
        verbose("\t\tError when copying : '%s'" % "".join(cmd_err))
    elif cmd_out:
        verbose("\t\tError when copying : '%s'" % "".join(cmd_out))
    verbose("\t\t-> elapsed time %s"%(datetime.now()-start))

#------------------------------------------------------------------------------

def main():
    global buildout_inst_type, PYTHONBIN

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
        PYTHONBIN = read_buildoutfile(os.path.join(instdir, 'bin', 'buildout'))
    else:
        zodbfilename = instdir + '/etc/zope.conf'
        zopectlfilename = instdir + '/bin/zopectl'
        fspath = instdir + '/var/'

    # Getting some informations in config file
    (port, dbs) = treat_zopeconflines(zodbfilename)
    zopepath = read_zopectlfile(zopectlfilename)
    if RSYNCDIR:
        if zopepath.startswith('/'):
            zopepath = zopepath[1:]
        zopepath = os.path.join(RSYNCDIR, zopepath)
    verbose("zope path='%s'"%zopepath)

    # Treating each db
    for db in dbs:
        if RSYNCDIR:
            copyfs(db[1], fspath)
        else:
            restoredb(db[1], zopepath, fspath)

#------------------------------------------------------------------------------

try:
    arg = sys.argv[1]
    if arg.startswith('#'):
        sys.exit(0)
    instdir, days, user, pwd = arg.split(';')
    if RSYNCDIR:
        if instdir.startswith('/'):
            instdir = instdir[1:]
        instdir = os.path.join(RSYNCDIR, instdir)
    verbose("Start of restoring dbs of %s"%(instdir))
except IndexError:
    error("No parameter found")
    sys.exit(1)
except ValueError:
    error("No enough parameters")
    sys.exit(1)

if __name__ == '__main__':
    main()
    verbose("End of restoring dbs of %s"%(instdir))
