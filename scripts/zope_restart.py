#!/usr/bin/python
#

import sys, os
import datetime
import shutil

buildout_inst_type = None #True for buildout, False for manual instance
was_running = True
backup_serveur = 'root@uvcwbac.all2all.org:/backup/villesetcommunes/files4'

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
        if 'daemon manager not running' in cmd_out:
            was_running = False
        elif 'daemon process stopped' in cmd_out:
            verbose('\t\tWell stopped')
        else:
            verbose("\t\tOutput when stopping instance : '%s'" % "".join(cmd_out))
    else:
        error("\t\tNo output for command : '%s'" % cmd)

#------------------------------------------------------------------------------

def backup_all_fs(path):
    """
        Copy the db files to the backup server. 
        This need that the instance must be stopped. 
        => Not efficient with larges fs.
        fs.old is backuped instead. 
    """
    cmd = 'rsync -aHuz --delete --inplace --include="*.fs" -e ssh '
    cmd += path + '/ ' + backup_serveur + path + '/'

    verbose("\tRunning command '%s'" % cmd)
    (cmd_out, cmd_err) = runCommand(cmd)

    if cmd_err:
        error("\t\tError when running rsync : '%s'" % "".join(cmd_err))
    elif cmd_out:
#         if 'daemon manager not running' in cmd_out:
#             was_running = False
#         elif 'daemon process stopped' in cmd_out:
#             verbose('\t\tWell stopped')
#         else:
        verbose("\t\tOutput when running rsync : '%s'" % "".join(cmd_out))
    else:
        error("\t\tNo output for command : '%s'" % cmd)

#------------------------------------------------------------------------------

def backup_new_fs(path):
    """
        Copy only new db files to the backup server. 
        Pack will not produce an fs.old file the first transaction days. 
        We will backup the fs if fs.old doesn't exist. 
        That's the fact for new db's => little fs => no large time to copy it
    """
    cmd = 'rsync -aHuz --delete --inplace --include="*.fs" -e ssh '
    cmd += path + '/ ' + backup_serveur + path + '/'

    verbose("\tRunning command '%s'" % cmd)
    return
    (cmd_out, cmd_err) = runCommand(cmd)

    if cmd_err:
        error("\t\tError when running rsync : '%s'" % "".join(cmd_err))
    elif cmd_out:
#         if 'daemon manager not running' in cmd_out:
#             was_running = False
#         elif 'daemon process stopped' in cmd_out:
#             verbose('\t\tWell stopped')
#         else:
        verbose("\t\tOutput when running rsync : '%s'" % "".join(cmd_out))
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
    #stop_instance(tmp)

    # 2. Copy all the fs to the backup server
    #backup_all_fs(tmp)
    # 2. Copy only new fs to the backup server
    backup_new_fs(tmp)

    # 3. Run logrotate on instance logs

    # 4. Restart the instance if it was running

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
