from Products.CMFCore.utils import getToolByName

from zope.i18nmessageid import MessageFactory
_ = MessageFactory('CPUtils')

from Products.CMFPlone.utils import base_hasattr
from Products.CPUtils.config import *

def setRobots(context):
    """
        Copy a robots.txt file from files dir to portal_skins/custom
    """
    if context.readDataFile('cputils_robots.txt') is None:
        return

    portal = context.getSite()
    output = []

    # Add additional setup code here

    zopeFolder = portal.portal_skins.custom

    filename = name = 'robots.txt'
    path = os.path.join(FILES_FOLDER, filename)
    fd = open(path, 'r')
    data = fd.read()
    fd.close()

    # if the file exists and title starts with Remove ..., we replace the file
    if base_hasattr(zopeFolder, name):
        rf = getattr(zopeFolder, name)
        if rf.title.startswith('Remove this file in production mode!'):
            zopeFolder.manage_delObjects([name])

    if not base_hasattr(zopeFolder, name):
        output.append("Creating file '%s' in '%s'"%(name, 'portal_skins/custom'))
        zopeFolder.manage_addProduct['OFSP'].manage_addFile(id=name, file=data, title='Remove this file in production mode! A effacer une fois le site en production!')
        if name in zopeFolder.objectIds():
            output.append("File created")
        else:
            output.append("File NOT created")
    else:
        output.append("File '%s' in '%s' already exists"%(name, 'portal_skins/custom'))

    return '\n'.join(output)
