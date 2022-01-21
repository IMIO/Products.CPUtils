#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Script to create and update a repository on zope instances
# Stéphan Geulette <stephan.geulette@uvcw.be>, UVCW
# From original script "recover.py" ()
#

from OFS.Application import Application
from Products.CPUtils.scripts.utils import CreateAndCallExternalMethod
from Products.CPUtils.scripts.utils import error
from Products.CPUtils.scripts.utils import trace
from Products.CPUtils.scripts.utils import treat_zopeconflines
from Products.CPUtils.scripts.utils import verbose
from utils import datetime
from zope.component import getSiteManager
from zope.component import getUtilitiesFor

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

    instdir = instdir.rstrip("/")
    verbose("Working on instance %s" % instdir)

    # Finding the instance type (buildout or manual)
    if os.path.exists(os.path.join(instdir, "parts")):
        buildout_inst_type = True
        # verbose("\tInstance is a buildout !")
    elif os.path.exists(os.path.join(instdir, "etc")):
        buildout_inst_type = False
        verbose("\tInstance is a manual installation !")
    elif not os.path.exists(instdir) or True:
        error("! Invalid instance path '%s' or instance type not detected" % instdir)
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

    CreateAndCallExternalMethod(
        port, user, pwd, "cputils_checkPOSKey", "utils.py", "checkPOSKey"
    )


def _checkAttributes(obj, errors, context=None):
    from ZODB.POSException import POSKeyError

    # very dumb checks for list and dict (like) attributes
    # is very slow but ensures that all attributes are checked
    for k, v in obj.__dict__.items():
        if hasattr(v, "values") and hasattr(v, "keys"):
            try:
                [repr(val) for val in v.values()]
                [repr(val) for val in v.keys()]
            except POSKeyError as ex:
                if hasattr(obj, "getPhysicalPath"):
                    path = "/".join(obj.getPhysicalPath())
                elif context:
                    path = "Utility: %s in %s" % (
                        repr(obj),
                        "/".join(context.getPhysicalPath()),
                    )
                else:
                    path = "Utility: %s" % (repr(obj))

                error("Error %s on DICT-LIKE attribute %s (%s)" % (str(ex), k, path))
                errors.append(
                    "Error %s on DICT-LIKE attribute %s (%s)" % (str(ex), k, path)
                )

        if hasattr(v, "append"):
            try:
                [val for val in v]
            except POSKeyError as ex:
                error(
                    "Error %s on LIST-LIKE attribute %s (%s)"
                    % (str(ex), k, "/".join(obj.getPhysicalPath()))
                )
                errors.append(
                    "Error %s on LIST-LIKE attribute %s (%s)"
                    % (str(ex), k, "/".join(obj.getPhysicalPath()))
                )


# ------------------------------------------------------------------------------


def _sub(master, errors):
    from ZODB.POSException import POSKeyError

    def check_utilities(sm, master, errors):
        for one in sm.utilities._subscribers:
            for interface in one.keys():
                try:
                    for util_tup in getUtilitiesFor(interface, context=master):
                        utility = util_tup[1]
                        _checkAttributes(utility, errors, context=master)
                except TypeError as msg:
                    error(
                        "Cannot get utilities for interface '%s' : %s"
                        % (str(interface), msg)
                    )

    # check site utilities
    if master.meta_type == "Plone Site":
        from Products.CMFCore.PortalObject import PortalObjectBase

        sm = PortalObjectBase.getSiteManager(master)
        check_utilities(sm, master, errors)

    if master.__class__ == Application:
        sm = getSiteManager()
        check_utilities(sm, master, errors)

    for oid in master.objectIds():
        try:
            obj = getattr(master, oid)
            trace("%s->%s" % ("/".join(master.getPhysicalPath()), obj.getId()))
            # output.append('%s->%s' % ('/'.join(master.getPhysicalPath()), obj.getId()))
            if hasattr(obj, "objectIds") and obj.getId() != "Control_Panel":
                _sub(obj, errors)

            # check catalog explicitly
            if obj.meta_type in [
                "ZCatalog",
                "Catalog",
                "Plone Catalog Tool",
            ] or hasattr(obj, "_catalog"):
                for idxid in obj._catalog.indexes.keys():
                    try:
                        index = obj._catalog.indexes.get(idxid)
                        trace(
                            "%s->INDEX: %s" % ("/".join(obj.getPhysicalPath()), idxid)
                        )
                        # output.append('%s->INDEX: %s' % ('/'.join(obj.getPhysicalPath()), idxid))

                        _checkAttributes(index, errors)

                    except POSKeyError as ex:
                        error(
                            "Error %s on INDEX %s (%s)"
                            % (str(ex), idxid, "/".join(obj.getPhysicalPath()))
                        )
                        errors.append(
                            "Error %s on INDEX %s (%s)"
                            % (str(ex), idxid, "/".join(obj.getPhysicalPath()))
                        )

                # support for lexicon
                for lexid in obj.objectIds():
                    _checkAttributes(getattr(obj, lexid), errors)

        except POSKeyError as ex:
            error(
                "Error %s on %s (%s)"
                % (str(ex), oid, "/".join(master.getPhysicalPath()))
            )
            errors.append(
                "Error %s on %s (%s)"
                % (str(ex), oid, "/".join(master.getPhysicalPath()))
            )


def check(app, errors=[]):
    # verbose("Begin of POSKey check")
    sys.setrecursionlimit(20000)
    _sub(app, errors)
    # verbose("End of POSKey check")


if __name__ == "__main__":
    # verbose("Begin of %s"%sys.argv[0])
    main()
    # verbose("End of %s"%sys.argv[0])
