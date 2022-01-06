#!/usr/bin/python
#
"""
    This script reads awstats conf files and updates stats with all apache log files (archived too).
"""

import datetime
import os
import shutil
import sys


def verbose(*messages):
    print ">>", " ".join(messages)


def error(*messages):
    #    print >>sys.stderr, '!!', (' '.join(messages))
    print "!!", (" ".join(messages))


def debug(*messages):
    if not TRACE:
        return
    print "TRACE:", " ".join(messages)


# ------------------------------------------------------------------------------

# CONF_DIR = '/etc/awstats'
CONF_DIR = "/home/srv/temp/awstats"
# APACHE_DIR = '/var/log/apache2'
APACHE_DIR = "/home/srv/temp/apache2_logs"
INCLUDE_ARCHIVED = False
AWSTATS_CMD = "/usr/lib/cgi-bin/awstats.pl"
TRACE = False
TEMP_DIR = "/tmp/"
gunzip = "gunzip"

# ------------------------------------------------------------------------------


def getFiles(dirpath, extensions, namestart, sort=False):
    """ Read the dir and return some files """
    files = []
    for filename in os.listdir(dirpath):
        debug("filename='%s'" % filename)
        if filename in (".", ".."):
            continue
        extension = os.path.splitext(filename)[1].strip(".")
        debug("extension='%s'" % extension)
        if not extension:
            continue
        if extensions and extension not in extensions:
            continue
        if namestart and not filename.startswith(namestart):
            continue
        debug("Kept '%s'" % filename)
        filepath = os.path.join(dirpath, filename)
        files.append(filepath)
    if sort:
        files.sort(compare_file_modiftime)
    return files


# -------------------------------------------------


def readFile(filename, lines):
    """ read the filename and return lines """
    try:
        zfile = open(filename, "r")
    except IOError:
        error("! Cannot open %s file" % filename)
        return
    #    lines = zfile.readlines()
    for line in zfile.readlines():
        line = line.strip("\n\t ")
        lines.append(line)
    zfile.close()


def runCommand(cmd):
    """ run an os command and get back the stdout and stderr outputs """
    os.system(cmd + " >_cmd_pv.out 2>_cmd_pv.err")
    stdout = stderr = []
    try:
        if os.path.exists("_cmd_pv.out"):
            ofile = open("_cmd_pv.out", "r")
            stdout = ofile.readlines()
            ofile.close()
            os.remove("_cmd_pv.out")
        else:
            error("File %s does not exist" % "_cmd_pv.out")
    except IOError:
        error("Cannot open %s file" % "_cmd_pv.out")
    try:
        if os.path.exists("_cmd_pv.err"):
            ifile = open("_cmd_pv.err", "r")
            stderr = ifile.readlines()
            ifile.close()
            os.remove("_cmd_pv.err")
        else:
            error("File %s does not exist" % "_cmd_pv.err")
    except IOError:
        error("Cannot open %s file" % "_cmd_pv.err")
    return (stdout, stderr)


# ------------------------------------------------------------------------------


def compare_file_modiftime(file1, file2):
    """ compare file in function of modification time """
    date1 = datetime.datetime.fromtimestamp(os.stat(file1).st_mtime)
    date2 = datetime.datetime.fromtimestamp(os.stat(file2).st_mtime)
    return cmp(date1, date2)


# ------------------------------------------------------------------------------


def main():
    verbose("Reading conf files")
    for conffilepath in getFiles(CONF_DIR, ("conf",), "", sort=True):
        conffile = os.path.basename(conffilepath)
        verbose("Reading %s" % conffile)
        lines = []
        readFile(conffilepath, lines)
        for line in lines:
            line = line.strip("\n\t ")
            #            debug("line '%s'"%line)
            if line.startswith("LogFile"):
                line = line[7:].strip('=" ')
                # to avoid line like LogFile="/usr/share/doc/awstats/examples/logresolvemerge.pl /srv/apache/apache2_logs/*_access.log |"
                if line.find("|") >= 0:
                    break
                logfilename = os.path.basename(line)
                verbose("\tFound apache log name '%s'" % logfilename)
                logfiles = getFiles(APACHE_DIR, [], logfilename, sort=True)
                if not logfiles:
                    error("No log files found in '%s'" % APACHE_DIR)
                # we remove begin and end: awstats. xxx .conf
                configname = conffile[8:-5]
                verbose("\tconfig name = '%s'" % configname)
                for logfilepath in logfiles:
                    logfile = os.path.basename(logfilepath)
                    if not (
                        logfile.endswith(".log")
                        or logfile.endswith(".log.1")
                        or logfile.endswith(".gz")
                    ):
                        error("Logfile found but not recognized '%s'" % logfile)
                        continue
                    verbose("\tLogfile found '%s'" % logfile)
                    if logfile.endswith(".gz"):
                        # we need to decompress the file
                        destination = os.path.join(TEMP_DIR, logfile)
                        try:
                            shutil.copyfile(logfilepath, destination)
                            verbose(
                                "\t'%s' copied to '%s'" % (logfilepath, destination)
                            )
                        except Exception, errmsg:
                            error(
                                "'%s' NOT COPIED to '%s'" % (logfilepath, destination)
                            )
                            error(str(errmsg))
                        command = "%s -f %s" % (gunzip, destination)
                        (cmd_out, cmd_err) = runCommand(command)
                        if cmd_err:
                            error(
                                "error running command %s : %s"
                                % (command, "".join(cmd_err))
                            )
                        logfilepath = destination[:-3]
                    command = "%s -config=%s -Logfile=%s -update" % (
                        AWSTATS_CMD,
                        configname,
                        logfilepath,
                    )
                    verbose("\t>> Running '%s'" % command)
                    (cmd_out, cmd_err) = runCommand(command)
                    if cmd_err:
                        error(
                            "error running command %s : %s"
                            % (command, "".join(cmd_err))
                        )
                    if cmd_out:
                        verbose("\t>>OUTPUT: %s" % ("".join(cmd_out)))
                    if logfile.endswith(".gz"):
                        os.remove(logfilepath)
                        verbose("\t'%s' deleted" % logfilepath)
                break
    verbose("End of script")


# ------------------------------------------------------------------------------

try:
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option(
        "-a",
        "--archived",
        dest="archived",
        default=False,
        help="Include archived logs or not. Default=False",
    )
    (options, args) = parser.parse_args()
    INCLUDE_ARCHIVED = options.archived
except ValueError:
    error("Problem in parameters")
    parser.print_help()
    sys.exit(1)

if __name__ == "__main__":
    main()
