#!/usr/bin/python
#

import sys, os
import datetime
import shutil

buildout_inst_type = None #True for buildout, False for manual instance
was_running = True
ROTATE_CONF_FILE = 'logrotate.conf'

def verbose(*messages):
    print '>>', ' '.join(messages)
def error(*messages):
    print >>sys.stderr, '!!', (' '.join(messages))

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

def stop_instance(path):
    """ Stop the instance """
    global was_running
    if buildout_inst_type:
        cmd = path + '/bin/instance stop'
    else:
        cmd = path + '/bin/zopectl stop'

    verbose("\tRunning command '%s'" % cmd)
    (cmd_out, cmd_err) = runCommand(cmd)

    if cmd_err:
        error("\t\tError when stopping instance : '%s'" % "".join(cmd_err))
    elif cmd_out:
        cmd_out = ''.join(cmd_out)
        if 'daemon manager not running' in cmd_out:
            was_running = False
            error('\t\tInstance not running')
        elif 'daemon process stopped' in cmd_out:
            verbose('\t\tWell stopped')
        else:
            verbose("\t\tOutput when stopping instance : '%s'" % "".join(cmd_out))
    else:
        error("\t\tNo output for command : '%s'" % cmd)

#------------------------------------------------------------------------------

def start_instance(path):
    """ Start the instance """
    if buildout_inst_type:
        cmd = path + '/bin/instance start'
    else:
        cmd = path + '/bin/zopectl start'

    verbose("\tRunning command '%s'" % cmd)
    (cmd_out, cmd_err) = runCommand(cmd)

    if cmd_err:
        error("\t\tError when starting instance : '%s'" % "".join(cmd_err))
    elif cmd_out:
        cmd_out = ''.join(cmd_out)
        if 'daemon process started' in cmd_out:
            verbose('\t\tWell started')
        else:
            verbose("\t\tOutput when starting instance : '%s'" % "".join(cmd_out))
    else:
        error("\t\tNo output for command : '%s'" % cmd)

#------------------------------------------------------------------------------

def rotate_logs(path):
    """
        Rotate logs of the instance
    """
    verbose("\tLog rotation on %s"%path)
    rotate_conf = os.path.join(path, ROTATE_CONF_FILE)
    if not os.path.exists(rotate_conf):
        error("\t\tRotate conf file doesn't exist '%s'"%rotate_conf)
        return
#    cmd = '/usr/sbin/logrotate -d ' #debug
    cmd = '/usr/sbin/logrotate '
    cmd += rotate_conf

    verbose("\tRunning command '%s'" % cmd)
    (cmd_out, cmd_err) = runCommand(cmd)

    if cmd_err:
        error("\t\tError when running logrotate : '%s'" % "".join(cmd_err))
    elif cmd_out:
        verbose("\t\tOutput when running logrotate : '%s'" % "".join(cmd_out))
    else:
        error("\t\tNo output for command : '%s'" % cmd)

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

    # 1. Stop the instance if running
    stop_instance(tmp)

    # 2. Rotate the logs of the instance
    rotate_logs(tmp)

    # 3. Restart the instance if it was running
    start_instance(tmp)

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
