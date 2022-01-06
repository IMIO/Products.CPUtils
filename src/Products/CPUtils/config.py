# -*- coding: utf-8 -*-
#
# File: CPUtils.py
#
# Copyright (c) 2008 by CommunesPlone
# Generator: ArchGenXML Version 1.5.2
#            http://plone.org/products/archgenxml
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

__author__ = """Stephan GEULETTE <stephan.geulette@uvcw.be>"""
__docformat__ = "plaintext"


# Product configuration.
#
# The contents of this module will be imported into __init__.py, the
# workflow configuration and every content type module.
#
# If you wish to perform custom configuration, you may put a file
# AppConfig.py in your product's root directory. This will be included
# in this file if found.
import os


try:  # New CMF
    from Products.CMFCore.permissions import setDefaultRoles
except ImportError:  # Old CMF
    from Products.CMFCore.CMFCorePermissions import setDefaultRoles


PROJECTNAME = "CPUtils"

# Permissions
DEFAULT_ADD_CONTENT_PERMISSION = "Add portal content"
setDefaultRoles(DEFAULT_ADD_CONTENT_PERMISSION, ("Manager", "Owner"))

product_globals = globals()

# Dependencies of Products to be installed by quick-installer
# override in custom configuration
DEPENDENCIES = []

# Dependend products - not quick-installed - used in testcase
# override in custom configuration
PRODUCT_DEPENDENCIES = []

# You can overwrite these two in an AppConfig.py:
# STYLESHEETS = [{'id': 'my_global_stylesheet.css'},
#                {'id': 'my_contenttype.css',
#                 'expression': 'python:object.getTypeInfo().getId() == "MyType"'}]
# You can do the same with JAVASCRIPTS.
STYLESHEETS = []
JAVASCRIPTS = []

PRODUCT_FOLDER = os.path.dirname(__file__)
FILES_FOLDER = os.path.join(PRODUCT_FOLDER, "data")


def getPloneVersion():
    import Products.CMFPlone as cmfp

    plonedir = cmfp.__path__[0]
    # 2.5, 3 version
    if os.path.exists(plonedir):
        for name in ("version.txt", "VERSION.txt", "VERSION.TXT"):
            versionfile = os.path.join(plonedir, name)
            if os.path.exists(versionfile):
                file = open(versionfile, "r")
                data = file.readline()
                file.close()
                return data.strip()
    # 4 version
    import pkg_resources

    return pkg_resources.get_distribution("Products.CMFPlone").version


PLONE_VERSION = getPloneVersion()
