#!/usr/bin/python
#
import datetime
import os


def verbose(*messages):
    print ">>", " ".join(messages)


def error(*messages):
    #    print >>sys.stderr, '!!', (' '.join(messages))
    print "!!", (" ".join(messages))


MAIL = "/usr/sbin/sendmail"
logfilenames = (
    "/var/log/cron_scripts.log",
    "/var/log/checkInstances.log",
    "/var/log/checkPoskey.log",
)
hostname = "mydomain.be"
today = datetime.date.today().strftime("%Y-%m-%d")
yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y-%m-%d")
header = (
    "To: server@communesplone.be",
    "From: root@%s" % hostname,
)


def read_log_file(filename, lines):
    """
        Read the log file
    """
    try:
        logfile = open(filename, "r")
        verbose("Reading file '%s'" % filename)
    except IOError:
        error("Cannot open %s file" % filename)
        return
    flag_tokeep = False
    for line in logfile.readlines():
        line = line.strip("\n\t ")
        # print line
        if line.startswith("##  %s, 23" % yesterday):
            flag_tokeep = True
        if line.startswith("##  %s," % today):
            flag_tokeep = True
        if flag_tokeep:
            lines.append(line)


verbose("Searching in log between %s and %s" % (yesterday, today))

for logfilename in logfilenames:
    bodylines = [""]
    read_log_file(logfilename, bodylines)
    # when logrotate is run, the logfile is cleared and
    # renamed in .1 (with 'delaycompress' option for logrotate)
    # we open the .1 file to get those lines
    if len(bodylines) < 10 and os.path.exists(logfilename + ".1"):
        rotatedlines = [""]
        read_log_file(logfilename + ".1", rotatedlines)
        bodylines[0:0] = rotatedlines

    # print '\n'.join(bodylines)
    # sys.exit(0)

    subject = "\nSubject: %s %s from %s" % (
        today,
        os.path.basename(logfilename),
        hostname,
    )

    # open a pipe to the mail program and
    # write the data to the pipe
    p = os.popen("%s -t" % MAIL, "w")
    #    p = open("%s"%os.path.basename(logfilename), 'w')  #testing
    p.write("\n".join(header))
    p.write(subject)
    p.write("\n".join(bodylines))
    exitcode = p.close()
    if exitcode:
        print "Exit code: %s" % exitcode
