#!/usr/bin/python
#
"""
    This script treats dbs of a zope instance :
    * packing each db
    * backuping with repozo each fs file
"""
from Products.CPUtils.scripts.utils import packdb
from Products.CPUtils.scripts.utils import read_zopectlfile
from Products.CPUtils.utils import verbose
from utils import error
from utils import read_zopeconffile

import datetime
import os
import shutil
import sys


buildout_inst_type = None  # True for buildout, False for manual instance
zeo_type = False  # True for zeo
BACKUP_DIR = "/srv/backups/zope"

# ------------------------------------------------------------------------------


def runCommand(cmd):
    """ run an os command and get back the stdout and stderr outputs """
    os.system(cmd + " >_cmd_zr.out 2>_cmd_zr.err")
    stdout = stderr = []
    try:
        if os.path.exists("_cmd_zr.out"):
            ofile = open("_cmd_zr.out", "r")
            stdout = ofile.readlines()
            ofile.close()
            os.remove("_cmd_zr.out")
        else:
            error("File %s does not exist" % "_cmd_zr.out")
    except IOError:
        error("Cannot open %s file" % "_cmd_zr.out")
    try:
        if os.path.exists("_cmd_zr.err"):
            ifile = open("_cmd_zr.err", "r")
            stderr = ifile.readlines()
            ifile.close()
            os.remove("_cmd_zr.err")
        else:
            error("File %s does not exist" % "_cmd_zr.err")
    except IOError:
        error("Cannot open %s file" % "_cmd_zr.err")
    return (stdout, stderr)


def treat_zopeconflines(zodbfilename):
    """
        read zope configuration lines to get informations
    """
    lines = []
    read_zopeconffile(zodbfilename, lines)
    zeo_fs = {}
    if zeo_type:
        zeoconffile = os.path.join(instdir, "parts", "zeo", "etc", "zeo.conf")
        lines2 = []
        read_zopeconffile(zeoconffile, lines2)
        fsflag = False
        fsnb = 0
        for line in lines2:
            if line.startswith("<filestorage "):
                fsflag = True
                fsnb = line.split()[1].strip(" >")
                # verbose("fsnb '%s'"%fsnb)
                continue
            if fsflag and line.startswith("path "):
                fsflag = False
                fs = line.split()[1]
                fs = os.path.basename(fs)
                # verbose("fs '%s'"%fs)
                if fsnb in zeo_fs:
                    error("Filestorage number '%s' already found" % fsnb)
                else:
                    zeo_fs[fsnb] = fs
                fsflag = False
                fsnb = 0
                continue
    port = ""
    httpflag = False
    fsflag = False
    dbs = []
    dbname = ""
    for line in lines:
        # verbose("=>'%s'"%line)
        if line.startswith("<http-server>"):
            httpflag = True
            continue
        if httpflag and line.startswith("address"):
            port = line.split()[1]
            httpflag = False
            continue
        if line.startswith("<zodb_db"):
            if dbname:
                error(
                    "\tnext db found while fs not found: previous dbname '%s', current line '%s'"
                    % (dbname, line)
                )
            dbname = line.split()[1]
            dbname = dbname.rstrip(">")
            if dbname == "temporary":
                dbname = ""
        if line.startswith("storage "):  # ZEO
            fsnb = line.split()[1]
            if fsnb in zeo_fs:
                dbs.append([dbname, zeo_fs[fsnb]])
            else:
                error("Filestorage number '%s' not found in zeo.conf ?" % fsnb)
            dbname = ""
            continue
        if line.startswith("<filestorage>"):  # NOT ZEO
            fsflag = True
            continue
        if fsflag and line.startswith("path"):  # NOT ZEO
            fsflag = False
            fs = line.split()[1]
            fs = os.path.basename(fs)
            dbs.append([dbname, fs])
            dbname = ""
            continue
    verbose(
        "\tport='%s', dbs='%s'" % (port, ";".join([",".join(dbinfo) for dbinfo in dbs]))
    )

    if not port:
        error("! the port was not found in the config file '%s'" % zodbfilename)

    return (port, dbs)


# ------------------------------------------------------------------------------


def backupdb(fs, zopepath, fspath, pythonfile):
    """ call the repozo script to backup file """
    repozofilename = os.path.join(zopepath, "bin", "repozo.py")
    pythonpath = os.path.join(zopepath, "lib", "python")
    if not os.path.exists(repozofilename):
        repozofilename = os.path.join(instdir, "bin", "repozo")
    elif not os.path.exists(repozofilename):
        repozofilename = os.path.join(zopepath, "utilities", "ZODBTools", "repozo.py")
    elif not os.path.exists(repozofilename):
        repozofilename = os.path.join(pythonpath, "ZODB", "scripts", "repozo.py")
    backupcmd = "env PYTHONPATH=%s %s %s -Bv " % (
        pythonpath,
        pythonfile,
        repozofilename,
    )
    if options.fullbackup:
        backupcmd += "-F "
    # -B / -R : backup or recover
    # -r backupdir
    # -F : full backup
    # -f fs file
    start = datetime.now()
    fsfilename = os.path.join(fspath, fs)
    #        backupdir = os.path.join(BACKUP_DIR, os.path.basename(instdir))
    #        if not os.path.exists(backupdir):
    #            os.mkdir(backupdir)
    backupdir = os.path.join(
        BACKUP_DIR, os.path.basename(instdir), os.path.splitext(fs)[0]
    )
    if os.path.exists(backupdir) and options.fullbackup:
        for file in shutil.os.listdir(backupdir):
            shutil.os.unlink(os.path.join(backupdir, file))
            verbose(
                "\t%s deleted because we do a full backup"
                % (os.path.join(backupdir, file))
            )
    if not os.path.exists(backupdir):
        os.makedirs(backupdir)
    verbose("\tBackup of '%s' with script '%s'" % (fsfilename, repozofilename))
    cmd = backupcmd + " -r %s -f %s" % (backupdir, fsfilename)
    verbose("\tRunning command '%s'" % cmd)
    (cmd_out, cmd_err) = runCommand(cmd)

    if cmd_err:
        verbose("\t\tOutput/Error when backuping : '%s'" % "".join(cmd_err))
    elif cmd_out:
        verbose("\t\tOutput when backuping : '%s'" % "".join(cmd_out))
    else:
        error("\t\tNo output for command : '%s'" % cmd)
    verbose("\t\t-> elapsed time %s" % (datetime.now() - start))


# ------------------------------------------------------------------------------


def main():
    global buildout_inst_type, zeo_type, instdir
    instance_section = "instance"

    if instdir.endswith("/"):
        instdir = instdir[0:-1]
    verbose("Working on instance %s" % instdir)

    if os.path.exists(os.path.join(instdir, "parts")):
        buildout_inst_type = True
        verbose("\tInstance is a buildout !")
    elif os.path.exists(os.path.join(instdir, "etc")):
        buildout_inst_type = False
        verbose("\tInstance is a manual installation !")
    elif not os.path.exists(instdir) or True:
        error("! Invalid instance path '%s' or instance type not detected" % instdir)
        sys.exit(1)

    if buildout_inst_type:
        if os.path.exists(os.path.join(instdir, "bin", "zeo")):
            zeo_type = True
            verbose("\tInstance is a zeo !")
        if os.path.exists(os.path.join(instdir, "bin", "instance1")):
            instance_section = "instance1"
        zodbfilename = instdir + "/parts/%s/etc/zope.conf" % instance_section
        zopectlfilename = instdir + "/parts/%s/bin/zopectl" % instance_section
        fspath = instdir + "/var/filestorage/"
    else:
        zodbfilename = instdir + "/etc/zope.conf"
        zopectlfilename = instdir + "/bin/zopectl"
        fspath = instdir + "/var/"

    # Getting some informations in config file
    (port, dbs) = treat_zopeconflines(zodbfilename)
    (zopepath, pythonfile) = read_zopectlfile(zopectlfilename)
    # verbose("repozo path='%s'"%zopepath)

    # We remove the folder containing all instance dbs in case of a full backup
    # It's necessary to avoid keeping old files to safe disk space
    if options.fullbackup:
        backupdir = os.path.join(BACKUP_DIR, os.path.basename(instdir))
        if os.path.exists(backupdir):
            shutil.rmtree(backupdir)
            verbose("\t%s deleted when full backup" % (backupdir))
    # Treating each db
    for db in dbs:
        packdb(
            port, db[0], days, "cputils_pack_db", "CPUtils.utils", "pack_db", user, pwd
        )
        # backupdb(db[1], zopepath, fspath, pythonfile)

    for file in shutil.os.listdir(fspath):
        if file.endswith(".fs.old"):
            shutil.os.unlink(fspath + file)
            verbose("\t%s deleted" % (fspath + file))
        elif file.endswith(".fs.pack"):
            shutil.os.unlink(fspath + file)
            error("! .pack file found : pack not correctly ended")
            verbose("\t%s deleted" % (fspath + file))


# ------------------------------------------------------------------------------

try:
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option(
        "-i",
        "--infos",
        dest="infos",
        default=None,
        help="infos about instance formatted like: "
        '"instance_path;transactions_days_number;admin_user;admin_password"',
    )
    parser.add_option(
        "-F",
        "--full",
        dest="fullbackup",
        help="do a full backup, not an incremental one",
        default=False,
        action="store_true",
    )
    (options, args) = parser.parse_args()
    if options.infos.startswith("#"):
        sys.exit(0)
    instdir, days, user, pwd = options.infos.split(";")
except ValueError:
    error("Problem in parameters")
    parser.print_help()
    sys.exit(1)

if __name__ == "__main__":
    verbose(
        "Start of packing, backuping %s, days=%s, full_backup=%s"
        % (instdir, days, options.fullbackup)
    )
    #    sys.exit(0)
    main()
    verbose("End of packing, backuping %s" % (instdir))
