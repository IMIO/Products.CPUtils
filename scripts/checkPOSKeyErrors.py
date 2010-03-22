#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Script to create and update a repository on zope instances
# Stéphan Geulette <stephan.geulette@uvcw.be>, UVCW
# From original script "recover.py" ()
#

import os, sys
import urllib
from datetime import datetime, timedelta
import socket

def verbose(*messages):
    print '>>', ' '.join(messages)
def error(*messages):
    print '!!', (' '.join(messages))
def trace(*messages):
    if not TRACE:
        return
    print 'TRACE:', ' '.join(messages)

buildout_inst_type = None #True for buildout, False for manual instance
tempdir = ''
now = datetime(1973,02,12).now()
pfolders = {}
temp_added = False
ext_method = 'cputils_checkPOSKey'
ext_filename = 'utils.py'
function = 'checkPOSKey'
TRACE = False

###############################################################################

def main():
    global instdir, tempdir, buildout_inst_type, user, pwd
    try:
        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option("-i", "--infos", dest="infos",
                      default=None,
                      help="infos about instance formatted like: "
                           "\"instance_path;transactions_days_number;admin_user;admin_password\"")
        (options, args) = parser.parse_args()
        if options.infos.startswith('#'):
            sys.exit(0)
        instdir, days, user, pwd = options.infos.split(';')
    except ValueError:
        error("Problem in parameters")
        parser.print_help()
        sys.exit(1)

#    import pdb; pdb.set_trace()
    instdir = instdir.rstrip('/')
    verbose("Working on instance %s" % instdir)

    # Finding the instance type (buildout or manual)
    if os.path.exists(os.path.join(instdir,'parts')):
        buildout_inst_type = True
        verbose("\tInstance is a buildout !")
    elif os.path.exists(os.path.join(instdir,'etc')):
        buildout_inst_type = False
        verbose("\tInstance is a manual installation !")
    elif not os.path.exists(instdir) or True:
        error("! Invalid instance path '%s' or instance type not detected"%instdir)
        sys.exit(1)

    if buildout_inst_type:
        inst_type = 'buildout'
        zodbfilename = os.path.join(instdir, 'parts/instance/etc/zope.conf')
        fspath = os.path.join(instdir, 'var/filestorage/')
    else:
        inst_type = 'manual'
        zodbfilename = os.path.join(instdir, 'etc/zope.conf')
        fspath = os.path.join(instdir, 'var/')

    instance = os.path.basename(instdir)
    if not tempdir:
        tempdir = os.path.join(instdir, 'temp')
    hostname = socket.gethostname()

    port = treat_zopeconflines(zodbfilename, fspath)

    trace("host='%s', inst='%s'"%(hostname, instance))

    #creating and calling external method in zope
    host = "http://localhost:%s" % port
    urllib._urlopener = MyUrlOpener()
    url_pv = "%s/%s" % (host, ext_method)
    current_url = url_pv
    try:
        verbose("Running '%s'"%current_url)
        ret_html = urllib.urlopen(current_url).read()
        if 'the requested resource does not exist' in ret_html:
            verbose('external method %s not exist : we will create it'%ext_method)
            (module, extension) = os.path.splitext(ext_filename)
            module = 'CPUtils.' + module
            current_url = "%s/manage_addProduct/ExternalMethod/manage_addExternalMethod?id=%s&module=%s&function=%s&title="%(host, ext_method, module, function)
            verbose("Running now '%s'"%current_url)
            ret_html = urllib.urlopen(current_url).read()
            if 'the requested resource does not exist' in ret_html or \
                ('The specified module' in ret_html and "couldn't be found" in ret_html):
                error("Cannot create external method in zope : '%s'"%ret_html)
                sys.exit(1)
            else:
                current_url = "%s/%s/valid_roles" % (host, ext_method)
                verbose("Running now '%s'"%current_url)
                ret_html = urllib.urlopen(current_url).read()
                if not ret_html[0] == '(':
                    error("error with valid_roles return: '%s'"%ret_html)
                    sys.exit(1)
                valid_roles = list(eval(ret_html))
                managerindex = valid_roles.index('Manager')
                current_url = "%s/%s/permission_settings" % (host, ext_method)
                verbose("Running now '%s'"%current_url)
                ret_html = urllib.urlopen(current_url).read()
                if not ret_html[0] == '[':
                    error("error with permission_settings return: '%s'"%ret_html)
                    sys.exit(1)
                permission_settings = eval(ret_html)
                params = {}
                count = 0
                for perm in permission_settings:
                    if perm['name'] in ('Access contents information','View'):
                        params['p%dr%d'%(count,managerindex)] = 'on'
                    else:
                        params['a%d'%count] = 'on'
                    count += 1
                current_url = "%s/%s/manage_changePermissions" % (host, ext_method)
                verbose("Running now '%s'"%current_url)
# params example                       params = {  'permission_to_manage':'View', 
#                                    'roles':['Manager'], }
                data = urllib.urlencode(params)
                ret_html = urllib.urlopen(current_url, data).read()
                if 'Your changes have been saved' not in ret_html:
                    error("Error changing permissions with URL '%s', data '%s'" % (current_url,str(data)))
                    sys.exit(1)
                current_url = url_pv
                verbose("Running again '%s'"%current_url)
                ret_html = urllib.urlopen(current_url).read()
        verbose("checkPOSKey html return = '%s'"%ret_html)
    except Exception, msg:
        error("Cannot open URL %s, aborting: '%s'" % (current_url,msg))
        sys.exit(1)

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
    zfile.close()

#------------------------------------------------------------------------------

def treat_zopeconflines(zodbfilename, fspath):
    """
        read zope configuration lines to get informations
    """
    lines = []
    read_zopeconffile(zodbfilename, lines)

    httpflag = False
    mp_name = mp_path = mp_fs = mp_fspath = None
    mp_size = 0
    for line in lines:
        line = line.strip()
        if line.startswith('<http-server>'):
            httpflag = True
            continue
        if line.startswith('<zodb_db '):
            #<zodb_db main>
            if mp_name:
                error("\tnext db found while end tag not found: previous dbname '%s', current line '%s'"%(mp_name, line))
            mp_name = line.split()[1]
            mp_name = mp_name.strip('> ')
            if mp_name == 'temporary':
                mp_name = None
            continue
        if mp_name and line.startswith('</zodb_db>'):
            mp_name = mp_path = mp_fs = mp_fspath = None
            mp_size = 0
            continue
        if mp_name and line.startswith('path '):
            #path $INSTANCE/var/Data.fs
            mp_fs = os.path.basename(line.split()[1])
            if not mp_fs.endswith('.fs'):
                error("Error getting fs name in '%s'"%line)
            mp_fspath = os.path.join(fspath, mp_fs)
            if os.path.exists(mp_fspath):
                mp_size = int(os.path.getsize(mp_fspath)/1048576)
            else:
                error("Db file '%s' doesn't exist"%mp_fspath)
                mp_fspath = ''
            continue
        if mp_name and line.startswith('mount-point '):
            #mount-point /
            mp_path = line.split()[1]
            if not mp_path.startswith('/'):
                error("Error getting path name in '%s'"%line)
            continue
        if httpflag and line.startswith('address'):
            port = line.split()[1]
    return port

#------------------------------------------------------------------------------

class MyUrlOpener(urllib.FancyURLopener):
    """ redefinition of this class to give the user and password"""
    def prompt_user_passwd(self, host, realm):
        return (user,pwd)
    def __init__(self, *args):
        self.version = "Zope Packer"
        urllib.FancyURLopener.__init__(self, *args)

#------------------------------------------------------------------------------

def _checkAttributes(obj, errors):
    from ZODB.POSException import POSKeyError
    # very dumb checks for list and dict (like) attributes
    # is very slow but ensures that all attributes are checked
    for k,v in obj.__dict__.items():
       if hasattr(v, 'values') and hasattr(v, 'keys'):
           try:
               data = [val for val in v.values()]
               data = [val for val in v.keys()]
           except POSKeyError, ex:
               error('Error %s on DICT-LIKE attribute %s (%s)' \
                     % (str(ex), k, '/'.join(obj.getPhysicalPath())))
               errors.append('Error %s on DICT-LIKE attribute %s (%s)' \
                     % (str(ex), k, '/'.join(obj.getPhysicalPath())))

       if hasattr(v, 'append'):
           try:
               data = [val for val in v]
           except POSKeyError, ex:
               error('Error %s on LIST-LIKE attribute %s (%s)' \
                     % (str(ex), k, '/'.join(obj.getPhysicalPath())))
               errors.append('Error %s on LIST-LIKE attribute %s (%s)' \
                     % (str(ex), k, '/'.join(obj.getPhysicalPath())))

#------------------------------------------------------------------------------

def _sub(master, errors):
    from ZODB.POSException import POSKeyError
    for oid in master.objectIds():
       try:
           obj = getattr(master, oid)
           trace('%s->%s' % ('/'.join(master.getPhysicalPath()), obj.getId()))
           #output.append('%s->%s' % ('/'.join(master.getPhysicalPath()), obj.getId()))
           if hasattr(obj, 'objectIds') and obj.getId() != 'Control_Panel':
               _sub(obj, errors)

           # check catalog explicitly
           if obj.meta_type in ['ZCatalog', 'Catalog', 'Plone Catalog Tool'] \
               or hasattr(obj, '_catalog'):
                   for idxid in obj._catalog.indexes.keys():
                       try:
                           index = obj._catalog.indexes.get(idxid)
                           trace('%s->INDEX: %s' % ('/'.join(obj.getPhysicalPath()), idxid))
                           #output.append('%s->INDEX: %s' % ('/'.join(obj.getPhysicalPath()), idxid))

                           _checkAttributes(index, errors)

                       except POSKeyError, ex:
                           error('Error %s on INDEX %s (%s)' % (str(ex), idxid, '/'.join(obj.getPhysicalPath())))
                           errors.append('Error %s on INDEX %s (%s)' % (str(ex), idxid, '/'.join(obj.getPhysicalPath())))

                   # support for lexicon
                   for lexid in obj.objectIds():
                       _checkAttributes(getattr(obj, lexid), errors)
                      
       except POSKeyError, ex:
           error('Error %s on %s (%s)' % (str(ex), oid, '/'.join(master.getPhysicalPath())))
           errors.append('Error %s on %s (%s)' % (str(ex), oid, '/'.join(master.getPhysicalPath())))

#------------------------------------------------------------------------------

def check(app, errors=[]):
    verbose("Begin of POSKey check")
    sys.setrecursionlimit(20000)
    _sub(app, errors)
    verbose("End of POSKey check")

#------------------------------------------------------------------------------


if __name__ == '__main__':
    verbose("Begin of %s"%sys.argv[0])
#    sys.exit(0)
    main()
    verbose("End of %s"%sys.argv[0])
