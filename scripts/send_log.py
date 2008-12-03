#!/usr/bin/python
#
"""
    This script reads the log file of all scripts and send a mail with the day content.
"""

import os
import datetime

def verbose(*messages):
    print '>>', ' '.join(messages)
def error(*messages):
#    print >>sys.stderr, '!!', (' '.join(messages))
    print '!!', (' '.join(messages))

#------------------------------------------------------------------------------

MAIL = "/usr/sbin/sendmail"
logfilename = '/var/log/cron_scripts.log'
hostname = 'mydomain.be'
today = datetime.date.today().strftime("%Y-%m-%d")
yesterday = (datetime.date.today()-datetime.timedelta(1)).strftime("%Y-%m-%d")
header = (  'To: sge@uvcw.be', 
            'From: root@%s'%hostname,
            'Subject: %s cron_scripts.log from %s'%(today,hostname) )
bodylines = []

#------------------------------------------------------------------------------

def read_log_file(filename, lines):
    """
        Read the log file
    """
    try:
        logfile = open( filename, 'r')
        verbose("Reading file '%s'"%filename)
    except IOError:
        error("Cannot open %s file" % filename)
        return
    flag_tokeep = False
    flag_yesterday = False
    for line in logfile.readlines():
        line = line.strip('\n\t ')
        #print line
        if line.startswith("##  %s, 23"%yesterday):
            flag_yesterday = True
            flag_tokeep = True
        if line.startswith("##  %s,"%today):
#            if not flag_yesterday:
#                read_log_file(filename+'.1', lines)
            flag_tokeep = True
        if flag_tokeep:
            lines.append(line)
#    if not flag_tokeep:
#        read_log_file(filename+'.1', lines)

#------------------------------------------------------------------------------

verbose("Start of send_log.py")
verbose("Searching in log between %s and %s"%(yesterday, today))

read_log_file(logfilename, bodylines)

# open a pipe to the mail program and
# write the data to the pipe
p = os.popen("%s -t" % MAIL, 'w')
p.write('\n'.join(header))
p.write('\n'.join(bodylines))
exitcode = p.close()
if exitcode:
    print "Exit code: %s" % exitcode

