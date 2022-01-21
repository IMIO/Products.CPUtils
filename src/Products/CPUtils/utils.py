# -*- coding: utf-8 -*-

from functools import partial

import collections
import os


def verbose(*messages):
    print ">>", " ".join(messages)


def error(*messages):
    #    print >>sys.stderr, '!!', (' '.join(messages))
    print "!!", (" ".join(messages))


# ------------------------------------------------------------------------------


def runCommand(cmd):
    """ run an os command and get back the stdout and stderr outputs """
    os.system(cmd + " >_cmd_pv.out 2>_cmd_pv.err")
    stdout = []
    stderr = []

    def get_output(osfile, result):
        try:
            if os.path.exists(osfile):
                ofile = open(osfile, "r")
                result += ofile.readlines()
                ofile.close()
                os.remove(osfile)
            else:
                error("File %s does not exist" % osfile)
        except IOError:
            error("Cannot open %s file" % osfile)

    get_output("_cmd_pv.out", stdout)
    get_output("_cmd_pv.err", stderr)
    return (stdout, stderr)


# ------------------------------------------------------------------------------


def writeTo(filepath, data, replace=True):
    """
        Write the data in the file
    """
    if os.path.exists(filepath) and not replace:
        return verbose("%s already exists" % filepath)
    ofile = open(filepath, "w")
    if isinstance(data, list):
        for line in data:
            ofile.write(
                "%s\n" % (isinstance(line, unicode) and line.encode("utf8") or line)
            )
    elif isinstance(data, str):
        ofile.write(data)
    elif isinstance(data, unicode):
        ofile.write(data.encode("utf8"))
    ofile.close()


# ------------------------------------------------------------------------------


def encodeData(data, encoding="utf8"):
    """
        Encode any data to the specified encoding
    """
    if isinstance(data, unicode):
        return data.encode(encoding)
    elif isinstance(data, collections.Mapping):
        mapfunc = partial(encodeData, encoding=encoding)
        return dict(map(mapfunc, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        mapfunc = partial(encodeData, encoding=encoding)
        return type(data)(map(mapfunc, data))
    else:
        return data
