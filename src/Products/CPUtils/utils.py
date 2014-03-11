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
    stdout = []
    stderr = []

    def get_output(osfile, result):
        try:
            if os.path.exists(osfile):
                ofile = open(osfile, 'r')
                result += ofile.readlines()
                ofile.close()
                os.remove(osfile)
            else:
                error("File %s does not exist" % osfile)
        except IOError:
            error("Cannot open %s file" % osfile)

    get_output('_cmd_pv.out', stdout)
    get_output('_cmd_pv.err', stderr)
    return(stdout, stderr)

#------------------------------------------------------------------------------
