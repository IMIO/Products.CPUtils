# -*- coding: utf-8 -*-
#
# File: test_functional.py
#
# Copyright (c) 2007 by CommunesPlone
# Generator: ArchGenXML Version 1.5.1-svn
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
# functional doctests.  This module collects all *.txt
# files in the tests directory and runs them.

__author__ = """Stephan Geulette <stephan.geulette@uvcw.be>"""
__docformat__ = 'plaintext'

import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import glob
from zope.testing import doctest
import unittest
from Globals import package_home
from Testing.ZopeTestCase import FunctionalDocTestSuite
from Testing.ZopeTestCase import FunctionalDocFileSuite as Suite
from Products.CMFPlone.tests import PloneTestCase
from Testing import ZopeTestCase
from Products.CPUtils.tests.CPUtilsTestCase import CPUtilsTestCase

PACKAGE = 'Products.CPUtils.tests'

REQUIRE_TESTBROWSER = ['tst_CPUtils.txt']

OPTIONFLAGS = (doctest.REPORT_ONLY_FIRST_FAILURE |
               doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)

def list_doctests():
    home = package_home(globals())
    print home
    return [filename for filename in
            glob.glob(os.path.sep.join([home, '*.txt']))]

def list_nontestbrowser_tests():
    return [filename for filename in list_doctests()
            if os.path.basename(filename) not in REQUIRE_TESTBROWSER]

def setUp(self):
    uf = self.portal.acl_users
    uf.userFolderAddUser('member', 'member', ['Member', ], [])
    uf.userFolderAddUser('admin', 'admin', ['Manager', 'Member', ], [])
    uf.userFolderAddUser('anon', 'anon', ['Anonymous', ], [])
    #we have to be logged as a Manager to run methods from exportimport
    self.login('admin')
    self.logout()
    return None

def test_suite():
    # BBB: We can obviously remove this when testbrowser is Plone
    #      mainstream, read: with Five 1.4.
    try:
        import Products.Five.testbrowser
    except ImportError:
        print >> sys.stderr, ("testbrowser not found; "
                              "testbrowser tests skipped")
        filenames = list_nontestbrowser_tests()
    else:
        filenames = list_doctests()

    suites = [
              Suite(os.path.basename(filename),
               optionflags=OPTIONFLAGS,
               package=PACKAGE,
               setUp=setUp,
               test_class=PloneTestCase.FunctionalTestCase,)
              for filename in filenames]

    # BBB: Fix for http://zope.org/Collectors/Zope/2178
    from Products.PloneTestCase import layer
    from Products.PloneTestCase import setup

    if setup.USELAYER:
        for s in suites:
            if not hasattr(s, 'layer'):
                s.layer = layer.PloneSite

    return unittest.TestSuite(suites)

if __name__ == '__main__':
    framework()

