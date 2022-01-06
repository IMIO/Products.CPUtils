#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# André NUYENS <andre.nuyens@uvcw.be>, UVCW
#

from datetime import datetime

import os
import sys
import urllib


TRACE = False


def verbose(*messages):
    print ">>", " ".join(messages)


def error(*messages):
    print "!!", (" ".join(messages))


def trace(*messages):
    if not TRACE:
        return
    print "TRACE:", " ".join(messages)


# ------------------------------------------------------------------------------


def read_zopectlfile(zopectlfilename):
    """ read the zopectl file to find the zope path """
    try:
        zfile = open(zopectlfilename, "r")
    except IOError:
        error("! Cannot open %s file" % zopectlfilename)
        return
    zopepath = ""
    pythonfile = ""
    for line in zfile.readlines():
        line = line.strip("\n\t ")
        if line.startswith("ZOPE_HOME"):
            zopepath = line.split("=")[1]
            zopepath = zopepath.strip("\"' ")
        elif line.startswith("PYTHON="):
            pythonfile = line.split("=")[1]
            pythonfile = pythonfile.strip("\"' ")
    return (zopepath, pythonfile)


# ------------------------------------------------------------------------------


def read_zopeconffile(zodbfilename, lines):
    """ read the zope conf filename and include subfile """
    try:
        zfile = open(zodbfilename, "r")
    except IOError:
        error("! Cannot open %s file" % zodbfilename)
        return
    for line in zfile.readlines():
        line = line.strip("\n\t ")
        if line.startswith("%include"):
            otherfilename = line.split()[1]
            read_zopeconffile(otherfilename, lines)
            continue
        lines.append(line)
    zfile.close()


# ------------------------------------------------------------------------------


def treat_zopeconflines(zodbfilename, fspath):
    """
        read zope configuration lines to get informations
    """
    lines = []
    read_zopeconffile(zodbfilename, lines)

    httpflag = False
    mp_name = mp_path = mp_fs = mp_fspath = None
    for line in lines:
        line = line.strip()
        if line.startswith("<http-server>"):
            httpflag = True
            continue
        if line.startswith("<zodb_db "):
            # <zodb_db main>
            if mp_name:
                error(
                    "\tnext db found while end tag not found: previous dbname '%s', current line '%s'"
                    % (mp_name, line)
                )
            mp_name = line.split()[1]
            mp_name = mp_name.strip("> ")
            if mp_name == "temporary":
                mp_name = None
            continue
        if mp_name and line.startswith("</zodb_db>"):
            mp_name = None
            continue
        if mp_name and line.startswith("path "):
            # path $INSTANCE/var/Data.fs
            mp_fs = os.path.basename(line.split()[1])
            if not mp_fs.endswith(".fs"):
                error("Error getting fs name in '%s'" % line)
            mp_fspath = os.path.join(fspath, mp_fs)
            if os.path.exists(mp_fspath):
                int(os.path.getsize(mp_fspath) / 1048576)
            else:
                error("Db file '%s' doesn't exist" % mp_fspath)
            continue
        if mp_name and line.startswith("mount-point "):
            # mount-point /
            mp_path = line.split()[1]
            if not mp_path.startswith("/"):
                error("Error getting path name in '%s'" % line)
            continue
        if httpflag and line.startswith("address"):
            port = line.split()[1]
    return port


class MyUrlOpener(urllib.FancyURLopener):
    """ redefinition of this class to give the user and password"""

    def prompt_user_passwd(self, host, realm):
        return (user, pwd)

    def __init__(self, *args):
        self.version = "Zope Packer"
        urllib.FancyURLopener.__init__(self, *args)


# ------------------------------------------------------------------------------


def packdb(port, db, days, method, module, function, user_, pwd_):
    global user, pwd
    user = user_
    pwd = pwd_
    host = "http://localhost:%s" % port
    urllib._urlopener = MyUrlOpener()
    start = datetime.now()
    verbose("\tPacking db '%s' for instance %s (%s days)" % (db, host, days))
    url_spd = "%s/Control_Panel/Database/%s/%s?days:float=%s" % (host, db, method, days)
    # verbose("url='%s'"%url_spd)
    try:
        ret_html = urllib.urlopen(url_spd).read()
        if (
            "the requested resource does not exist" in ret_html
            or "error was encountered while publishing this resource" in ret_html
        ):
            verbose("\texternal method %s not exist : we will create it" % method)
            url_em = (
                "%s/manage_addProduct/ExternalMethod/manage_addExternalMethod?id=%s&module=%s&function=%s&title="
                % (host, method, module, function)
            )
            try:
                ret_html = urllib.urlopen(url_em).read()
                if (
                    "the requested resource does not exist" in ret_html
                    or "error was encountered while publishing this resource"
                    in ret_html
                ):
                    error("! Cannot create external method in zope")
                elif "The specified module," in ret_html:
                    error(
                        "! The specified module %s is not present in the instance"
                        % module
                    )
                else:
                    try:
                        ret_html = urllib.urlopen(url_spd).read()
                        #                            if "/Control_Panel/Database/%s"%db not in ret_html:
                        #                                error("Problem during compression of %s"%db)
                        #                                log.debug(ret_html)
                        verbose("\t%s" % ret_html)
                    except IOError, msg:
                        error("! Cannot open URL %s, aborting : %s" % (url_spd, msg))
            except Exception, msg:
                error("! Cannot open URL %s, aborting : %s" % (url_em, msg))
        else:
            verbose("\t%s" % ret_html)
    except IOError, msg:
        error("! Cannot open URL %s, aborting : %s" % (url_spd, msg))
    verbose("\t\t-> elapsed time %s" % (datetime.now() - start))


# ------------------------------------------------------------------------------


def CreateAndCallExternalMethod(
    port, user_, pwd_, ext_method, ext_filename, function, param=""
):
    # creating and calling external method in zope
    global instdir, tempdir, buildout_inst_type, user, pwd
    host = "http://localhost:%s" % port
    user = user_
    pwd = pwd_
    urllib._urlopener = MyUrlOpener()
    url_pv = "%s/%s%s" % (host, ext_method, param)
    current_url = url_pv
    try:
        # verbose("Running '%s'"%current_url)
        ret_html = urllib.urlopen(current_url).read()
        if "the requested resource does not exist" in ret_html:
            verbose("external method %s not exist : we will create it" % ext_method)
            (module, extension) = os.path.splitext(ext_filename)
            module = "CPUtils." + module
            current_url = (
                "%s/manage_addProduct/ExternalMethod/manage_addExternalMethod?id=%s&module=%s&function=%s&title="
                % (host, ext_method, module, function)
            )
            # verbose("Running now '%s'"%current_url)
            ret_html = urllib.urlopen(current_url).read()
            if "the requested resource does not exist" in ret_html or (
                "The specified module" in ret_html and "couldn't be found" in ret_html
            ):
                error("Cannot create external method in zope : '%s'" % ret_html)
                sys.exit(1)
            else:
                current_url = "%s/%s/valid_roles" % (host, ext_method)
                # verbose("Running now '%s'"%current_url)
                ret_html = urllib.urlopen(current_url).read()
                if not ret_html[0] == "(":
                    error("error with valid_roles return: '%s'" % ret_html)
                    sys.exit(1)
                valid_roles = list(eval(ret_html))
                managerindex = valid_roles.index("Manager")
                current_url = "%s/%s/permission_settings" % (host, ext_method)
                # verbose("Running now '%s'"%current_url)
                ret_html = urllib.urlopen(current_url).read()
                if not ret_html[0] == "[":
                    error("error with permission_settings return: '%s'" % ret_html)
                    sys.exit(1)
                permission_settings = eval(ret_html)
                params = {}
                count = 0
                for perm in permission_settings:
                    if perm["name"] in ("Access contents information", "View"):
                        params["p%dr%d" % (count, managerindex)] = "on"
                    else:
                        params["a%d" % count] = "on"
                    count += 1
                current_url = "%s/%s/manage_changePermissions" % (host, ext_method)
                # verbose("Running now '%s'"%current_url)
                # params example                       params = {  'permission_to_manage':'View',
                #                                    'roles':['Manager'], }
                data = urllib.urlencode(params)
                ret_html = urllib.urlopen(current_url, data).read()
                if "Your changes have been saved" not in ret_html:
                    error(
                        "Error changing permissions with URL '%s', data '%s'"
                        % (current_url, str(data))
                    )
                    sys.exit(1)
                current_url = url_pv
                # verbose("Running again '%s'"%current_url)
                ret_html = urllib.urlopen(current_url).read()
        # verbose("callAndCreateExternalMethod : \n%s"%ret_html)
        if ret_html:
            verbose("%s" % ret_html)
    except Exception, msg:
        error("Cannot open URL %s, aborting: '%s'" % (current_url, msg))
        sys.exit(1)
