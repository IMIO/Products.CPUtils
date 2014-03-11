# -*- coding: utf-8 -*-

import os


def verbose(*messages):
    print '>>', ' '.join(messages)


def error(*messages):
#    print >>sys.stderr, '!!', (' '.join(messages))
    print '!!', (' '.join(messages))


#------------------------------------------------------------------------------

def runCommand(cmd):
    """ run an os command and get back the stdout and stderr outputs """
    os.system(cmd + ' >_cmd_pv.out 2>_cmd_pv.err')
    stdout = stderr = []
    try:
        if os.path.exists('_cmd_pv.out'):
            ofile = open('_cmd_pv.out', 'r')
            stdout = ofile.readlines()
            ofile.close()
            os.remove('_cmd_pv.out')
        else:
            error("File %s does not exist" % '_cmd_pv.out')
    except IOError:
        error("Cannot open %s file" % '_cmd_pv.out')
    try:
        if os.path.exists('_cmd_pv.err'):
            ifile = open('_cmd_pv.err', 'r')
            stderr = ifile.readlines()
            ifile.close()
            os.remove('_cmd_pv.err')
        else:
            error("File %s does not exist" % '_cmd_pv.err')
    except IOError:
        error("Cannot open %s file" % '_cmd_pv.err')
    return(stdout, stderr)

#------------------------------------------------------------------------------
