#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Script to create and update a repository on zope instances
# Stéphan Geulette <stephan.geulette@uvcw.be>, UVCW
# From original script "recover.py" ()
#
from Products.CPUtils.scripts.utils import CreateAndCallExternalMethod
from Products.CPUtils.scripts.utils import trace
from Products.CPUtils.scripts.utils import treat_zopeconflines
from utils import datetime
from utils import error
from utils import verbose

import os
import socket
import sys


buildout_inst_type = None  # True for buildout, False for manual instance
tempdir = ""
now = datetime(1973, 02, 12).now()
pfolders = {}
temp_added = False


def main():
    global instdir, tempdir, buildout_inst_type, user, pwd

    instdir = instdir.rstrip("/")
    verbose(
        "Working on instance %s" % instdir
    )  # must be commented when CPUtils updated in all instances

    # Finding the instance type (buildout or manual)
    if os.path.exists(os.path.join(instdir, "parts")):
        buildout_inst_type = True
        # verbose("\tInstance is a buildout !")
    elif os.path.exists(os.path.join(instdir, "etc")):
        buildout_inst_type = False
        verbose("%s, manual installation !" % instdir)
    elif not os.path.exists(instdir) or True:
        error("%s, Invalid instance path or instance type not detected" % instdir)
        sys.exit(1)

    if buildout_inst_type:
        zodbfilename = os.path.join(instdir, "parts/instance/etc/zope.conf")
        fspath = os.path.join(instdir, "var/filestorage/")
    else:
        zodbfilename = os.path.join(instdir, "etc/zope.conf")
        fspath = os.path.join(instdir, "var/")

    instance = os.path.basename(instdir)
    if not tempdir:
        tempdir = os.path.join(instdir, "temp")
    hostname = socket.gethostname()

    port = treat_zopeconflines(zodbfilename, fspath)

    trace("host='%s', inst='%s'" % (hostname, instance))

    param = "?instdir=%s" % instdir
    if instance.find("test") < 0:
        param += "&isProductInstance=1"
    CreateAndCallExternalMethod(
        port, user, pwd, "cputils_checkInstance", "utils.py", "checkInstance", param
    )


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
    (options, args) = parser.parse_args()
    if options.infos.startswith("#"):
        sys.exit(0)
    instdir, days, user, pwd = options.infos.split(";")
except ValueError:
    error("Problem in parameters")
    parser.print_help()
    sys.exit(1)

if __name__ == "__main__":
    # verbose("Begin of %s"%sys.argv[0])
    main()
    # verbose("End of %s"%sys.argv[0])
