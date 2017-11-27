# -*- coding: utf-8 -*-
#
# File: CPUtilsTestCase.py
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

__author__ = """Stephan GEULETTE <stephan.geulette@uvcw.be>"""
__docformat__ = 'plaintext'

#
# Base TestCase for contacts
#

import os, sys, code
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

##code-section module-header #fill in your manual code here
from Products.CMFCore.utils import getToolByName
from Products.CPUtils.config import *
from sets import Set

##/code-section module-header

from Testing import ZopeTestCase
from Products.PloneTestCase import PloneTestCase
ZopeTestCase.installProduct(PROJECTNAME)

PRODUCTS = list()
PRODUCTS.append(PROJECTNAME)

testcase = PloneTestCase.PloneTestCase

##code-section module-before-plone-site-setup #fill in your manual code here
##/code-section module-before-plone-site-setup

#Extension profile doesn't work because appinstall of ts appears to be not run
#PloneTestCase.setupPloneSite(products=PRODUCTS, extension_profiles=EXTENSION_PROFILES)
PloneTestCase.setupPloneSite(products=PRODUCTS)

class CPUtilsTestCase(testcase):
    """Base TestCase for contacts."""

    ##code-section class-header_CPUtilsTestCase #fill in your manual code here
    def afterSetup(self):
        """
        Manage users and permissions
        """
        self.wft = self.portal.portal_workflow
        uf = self.portal.acl_users
        uf.userFolderAddUser('member', 'member', ['Member', ], [])
        uf.userFolderAddUser('admin', 'admin', ['Manager', 'Member', ], [])
        uf.userFolderAddUser('anon', 'anon', ['Anonymous', ], [])
        #we have to be logged as a Manager to run methods from exportimport
        self.login('admin')
        #we run every import steps
#        self.portal.portal_setup.setImportContext("profile-Products.CPSkin2:default")
#        self.portal.portal_setup.runImportStep(step_id="createstructure-cpskin2")
#        self.portal.portal_setup.runImportStep(step_id="fillinleftslots-cpskin2")
        self.logout()

    def invokeFactoryC(self, type_name, id, path, **dict):
        path.invokeFactory(type_name=type_name, id=id, **dict)
        return getattr(path, id)

    def checkActionList(self, object, actions):
        """ Compare un set d'action de sorte que ['corriger', 'attendre'] soit egal a ['attendre', 'corriger'] """
        obj_actions = self.getActionList(object)
        self.assertEquals(Set(obj_actions), Set(actions))

    def getActionList(self, object):
        return [action_dict['name'] for action_dict in self.wft.getTransitionsFor(object)]


    ##/code-section class-header_CPUtilsTestCase

    # Commented out for now, it gets blasted at the moment anyway.
    # Place it in the protected section if you need it.
    #def afterSetup(self):
    #    """
    #    """
    #    pass

    def interact(self, locals=None):
        """Provides an interactive shell aka console inside your testcase.

        It looks exact like in a doctestcase and you can copy and paste
        code from the shell into your doctest. The locals in the testcase are
        available, becasue you are in the testcase.

        In your testcase or doctest you can invoke the shell at any point by
        calling::

            >>> self.interact( locals() )

        locals -- passed to InteractiveInterpreter.__init__()
        """
        savestdout = sys.stdout
        sys.stdout = sys.stderr
        sys.stderr.write('='*70)
        console = code.InteractiveConsole(locals)
        console.interact("""
ZopeTestCase Interactive Console
(c) BlueDynamics Alliance, Austria - 2005

Note: You have the same locals available as in your test-case.
""")
        sys.stdout.write('\nend of ZopeTestCase Interactive Console session\n')
        sys.stdout.write('='*70+'\n')
        sys.stdout = savestdout


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(CPUtilsTestCase))
    return suite

##code-section module-footer #fill in your manual code here
##/code-section module-footer

if __name__ == '__main__':
    framework()


