from optparse import OptionParser

import plone.recipe.zope2zeoserver.pack
import sys


parser = OptionParser()
parser.add_option("-c", "--cache", action="store", type="string", dest="cache")
parser.add_option("-i", "--instance", action="store", type="string", dest="instance")
parser.add_option("-s", "--storage", action="store", type="string", dest="storage")
parser.add_option("-d", "--days", action="store", type="string", dest="days")
parser.add_option("-p", "--port", action="store", type="string", dest="port")

(options, args) = parser.parse_args()
cache = options.cache
instance = options.instance
storage = options.storage
days = options.days
port = options.port


sys.path[0:0] = [
    cache + "/eggs/plone.recipe.zope2zeoserver-1.4-py2.4.egg",
    cache + "/eggs/zc.recipe.egg-1.2.2-py2.4.egg",
    cache + "/eggs/setuptools-0.6c11-py2.4.egg",
    cache + "/eggs/zc.buildout-1.4.4-py2.4.egg",
    instance + "/parts/zope2/lib/python",
]

username = None
blob_dir = None
realm = None
unix = None
host = "127.0.0.1"
password = None


if __name__ == "__main__":
    plone.recipe.zope2zeoserver.pack.main(
        host, port, unix, days, username, password, realm, blob_dir, storage
    )
