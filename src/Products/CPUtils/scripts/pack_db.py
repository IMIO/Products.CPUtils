#!/usr/bin/python
from utils import error
from utils import packdb
from utils import read_zopeconffile
from utils import verbose

import os
import shutil
import sys


buildout_inst_type = None  # True for buildout, False for manual instance


def main():
    global buildout_inst_type

    tmp = instdir
    if tmp.endswith("/"):
        tmp = tmp[0:-1]
    verbose("Working on instance %s" % tmp)

    if os.path.exists(os.path.join(tmp, "parts")):
        buildout_inst_type = True
        verbose("\tInstance is a buildout !")
    elif os.path.exists(os.path.join(tmp, "etc")):
        buildout_inst_type = False
        verbose("\tInstance is a manual installation !")
    elif not os.path.exists(tmp) or True:
        error("! Invalid instance path '%s' or instance type not detected" % tmp)
        sys.exit(1)

    if buildout_inst_type:
        zodbfilename = instdir + "/parts/instance/etc/zope.conf"
    else:
        zodbfilename = instdir + "/etc/zope.conf"

    lines = []
    read_zopeconffile(zodbfilename, lines)

    port = ""
    httpflag = False
    dbs = []
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
            dbname = line.split()[1]
            dbname = dbname.rstrip(">")
            if dbname != "temporary":
                dbs.append(dbname)
    verbose("\tport='%s', dbs='%s'" % (port, ";".join(dbs)))

    if not port:
        error("! the port was not found in the config file '%s'" % zodbfilename)

    packdb(port, dbs, days, "cputils_pack_db", "CPUtils.utils", "pack_db")

    # we delete every .old created during packing in the /var directory of the zope instance
    if buildout_inst_type:
        dir_path = instdir + "/var/filestorage/"
    else:
        dir_path = instdir + "/var/"

    for file in shutil.os.listdir(dir_path):
        if file.endswith(".fs.old"):
            # we do no more delete fs.old to safely backup this file as zodb file
            # shutil.os.unlink(dir_path + file)
            # verbose("\t%s deleted" % (dir_path + file))
            pass
        elif file.endswith(".fs.pack"):
            shutil.os.unlink(dir_path + file)
            error("! .pack file found : pack not correctly ended")
            verbose("\t%s deleted" % (dir_path + file))


# ------------------------------------------------------------------------------

try:
    arg = sys.argv[1]
    if arg.startswith("#"):
        sys.exit(0)
    instdir, days, user, pwd = arg.split(";")
    verbose("Start of packing %s, days=%s" % (instdir, days))
except IndexError:
    error("No parameter found")
    sys.exit(1)
except ValueError:
    error("No enough parameters")
    sys.exit(1)

if __name__ == "__main__":
    main()
    verbose("End of packing %s" % (instdir))
