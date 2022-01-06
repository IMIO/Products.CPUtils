#!/usr/bin/python
#

import os
import sys


buildout_inst_type = None  # True for buildout, False for manual instance
zeo_type = False  # True for zeo
was_running = True
ROTATE_CONF_FILE = "logrotate.conf"
TMPDIR = "/tmp"


def verbose(*messages):
    print ">>", " ".join(messages)


def error(*messages):
    #    print >>sys.stderr, '!!', (' '.join(messages))
    print "!!", (" ".join(messages))


# ------------------------------------------------------------------------------


def runCommand(cmd):
    """ run an os command and get back the stdout and stderr outputs """
    outfile = os.path.join(TMPDIR, "_cmd_zr.out")
    errfile = os.path.join(TMPDIR, "_cmd_zr.err")
    os.system(cmd + " >%s 2>%s" % (outfile, errfile))
    stdout = stderr = []
    try:
        if os.path.exists(outfile):
            ofile = open(outfile, "r")
            stdout = ofile.readlines()
            ofile.close()
            os.remove(outfile)
        else:
            error("File %s does not exist" % outfile)
    except IOError:
        error("Cannot open %s file" % outfile)
    try:
        if os.path.exists(errfile):
            ifile = open(errfile, "r")
            stderr = ifile.readlines()
            ifile.close()
            os.remove(errfile)
        else:
            error("File %s does not exist" % errfile)
    except IOError:
        error("Cannot open %s file" % errfile)
    return (stdout, stderr)


# ------------------------------------------------------------------------------


def stop_instance(instance_section, path):
    """ Stop the instance """
    global was_running
    if buildout_inst_type:
        cmd = ""
        if zeo_type:
            cmd = path + "/bin/zeo stop;"
        cmd += path + "/bin/%s stop" % instance_section
    else:
        cmd = path + "/bin/zopectl stop"

    verbose("\tRunning command '%s'" % cmd)
    (cmd_out, cmd_err) = runCommand(cmd)

    if cmd_err:
        error("\t\tError when stopping instance : '%s'" % "".join(cmd_err))
    elif cmd_out:
        cmd_out = ("".join(cmd_out)).strip("\n ")
        if (
            "daemon process not running" in cmd_out
            or "daemon manager not running" in cmd_out
        ):
            was_running = False
            error("\t\tInstance not running")
        elif "daemon process stopped" in cmd_out:
            verbose("\t\tWell stopped")
        else:
            verbose("\t\tOutput when stopping instance : '%s'" % "".join(cmd_out))
    else:
        error("\t\tNo output for command : '%s'" % cmd)


# ------------------------------------------------------------------------------


def start_instance(instance_section, path):
    """ Start the instance """
    if not was_running:
        return
    if buildout_inst_type:
        cmd = ""
        if zeo_type:
            cmd = path + "/bin/zeo start;"
        cmd += path + "/bin/%s start" % instance_section
    else:
        cmd = path + "/bin/zopectl start"

    verbose("\tRunning command '%s'" % cmd)
    (cmd_out, cmd_err) = runCommand(cmd)

    if cmd_err:
        error("\t\tError when starting instance : '%s'" % "".join(cmd_err))
    elif cmd_out:
        cmd_out = ("".join(cmd_out)).strip("\n ")
        if "daemon process started" in cmd_out:
            verbose("\t\tWell started : %s" % cmd_out)
        else:
            verbose("\t\tOutput when starting instance : '%s'" % "".join(cmd_out))
    else:
        error("\t\tNo output for command : '%s'" % cmd)


# ------------------------------------------------------------------------------


def rotate_logs(path):
    """
        Rotate logs of the instance
    """
    verbose("\tLog rotation on %s" % path)
    rotate_conf = os.path.join(path, ROTATE_CONF_FILE)
    if not os.path.exists(rotate_conf):
        error("\t\tRotate conf file doesn't exist '%s'" % rotate_conf)
        return
    #    cmd = '/usr/sbin/logrotate -d ' #debug
    cmd = "/usr/sbin/logrotate "
    cmd += rotate_conf

    verbose("\tRunning command '%s'" % cmd)
    (cmd_out, cmd_err) = runCommand(cmd)

    if cmd_err:
        error("\t\tError when running logrotate : '%s'" % "".join(cmd_err))
    elif cmd_out:
        verbose("\t\tOutput when running logrotate : '%s'" % "".join(cmd_out))
    else:
        pass
        # error("\t\tNo output for command : '%s'" % cmd)


# ------------------------------------------------------------------------------


def main():
    global buildout_inst_type, zeo_type
    instance_section = "instance"

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
        if os.path.exists(os.path.join(tmp, "bin", "zeo")):
            zeo_type = True
            verbose("\tInstance is a zeo !")
        if os.path.exists(os.path.join(tmp, "bin", "instance1")):
            instance_section = "instance1"

    if not subcommand:
        # 1. Stop the instance if running
        stop_instance(instance_section, tmp)

        # 2. Rotate the logs of the instance
        rotate_logs(tmp)

        # 3. Restart the instance if it was running
        start_instance(instance_section, tmp)
    else:
        if buildout_inst_type:
            cmd = ""
            if zeo_type:
                cmd = tmp + "/bin/zeo %s;" % subcommand
            cmd += tmp + "/bin/%s %s" % (instance_section, subcommand)
        else:
            cmd = tmp + "/bin/zopectl %s" % subcommand

        verbose("\tRunning command '%s'" % cmd)
        (cmd_out, cmd_err) = runCommand(cmd)
        verbose("\toutput: '%s'" % "".join(cmd_out))


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
        "-c",
        "--command",
        dest="subcommand",
        help="subcommand name like: start, stop, restart, status",
        default="",
    )
    (options, args) = parser.parse_args()
    if options.infos.startswith("#"):
        sys.exit(0)
    instdir, days, user, pwd = options.infos.split(";")
    subcommand = options.subcommand
except ValueError:
    error("Problem in parameters")
    parser.print_help()
    sys.exit(1)

if __name__ == "__main__":
    main()
