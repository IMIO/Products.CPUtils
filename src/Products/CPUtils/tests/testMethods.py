# -*- coding: utf-8 -*-
#
# File: testMethods.py
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

__author__ = """Stephan Geulette <stephan.geulette@uvcw.be>"""
__docformat__ = 'plaintext'

import os, sys
from zExceptions import NotFound
from Products.ExternalMethod.ExternalMethod import ExternalMethod
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))
import transaction
##code-section module-header #fill in your manual code here
##/code-section module-header

#
# Test-cases for class(es) 
#

from Testing import ZopeTestCase
from Products.PloneTestCase import PloneTestCase
from Products.CPUtils.config import *
from Products.CPUtils.tests.CPUtilsTestCase import CPUtilsTestCase

# Import the tested classes

##code-section module-beforeclass #fill in your manual code here
from sets import Set
from AccessControl.SecurityManagement import getSecurityManager
from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod
##/code-section module-beforeclass


class testMethods(CPUtilsTestCase):
    """Test-cases for class(es) ."""

    ##code-section class-header_testMethods #fill in your manual code here
    ##/code-section class-header_testMethods

    def afterSetUp(self):
        """
        """        
        CPUtilsTestCase.afterSetup(self)
        
        self.loginAsPortalOwner()
        method = 'install'
        method_name = 'cputils_'+method
        manage_addExternalMethod(self.app, method_name, '', 'CPUtils.utils', method)
        self.app.cputils_install()
        
    # Manually created methods
    
        
    def test_audit_catalog(self):
        result = self.portal.cputils_audit_catalog()
        ok = result.startswith("<h1>RESULTATS DE LA RECHERCHE</h1> <p>Recherche dans : /</p> <p>Nombre d'elements trouves :")
        ok = ok and result.find("portal_type : getObjSize : url") > -1
        self.failUnless(ok)        
        
    def test_change_authentication_plugins_param_doChange (self):
        result = self.app.cputils_change_authentication_plugins(self.app,'','')
        ok = result.startswith("The following changes are not applied: you must run the script with the parameter '...?dochange=1'")
        result = self.app.cputils_change_authentication_plugins(self.app,1,'')
        ok = ok and result.startswith("The following changes are not applied: you must run the script with the parameter '...?dochange=1'")
        self.failUnless(ok)
        
    def test_change_authentication_plugins_param_activate (self):
        result = self.app.cputils_change_authentication_plugins(self.app,'',1)
        ok = result.startswith("Document '/authentication_plugins_sites' added")
        ok = ok and result.find("Desactivate plugins source_users") > -1 
        result = self.app.cputils_change_authentication_plugins(self.app,1,1)
        ok = ok and result.find("site found plone")
        ok = ok and result.find("Activate plugins source_users") > -1
        self.failUnless(ok)
        
    def test_change_user_properties_no_param(self):
        result = self.portal.cputils_change_user_properties(self.portal,'','')
        ok = result.find("USER:'member'") > -1 and result.find("USER:'admin'") > -1 and result.find("USER:'anon'") > -1
        self.failUnless(ok)
        
    def test_change_user_properties_param_visibleIDs(self):
        result = self.portal.cputils_change_user_properties(self.portal,'visible_ids:True','')
        ok = result.find("USER:'member'") > -1 and result.find("USER:'admin'") > -1 and result.find("USER:'anon'") > -1
        ok = ok and result.find(" all properties: visible_ids='False'")
        result = self.portal.cputils_change_user_properties(self.portal,'visible_ids:True',1)
        ok = result.find("USER:'member'") > -1 and result.find("USER:'admin'") > -1 and result.find("USER:'anon'") > -1
        ok = ok and result.find("old properties: visible_ids='False',<br/>->  new properties: visible_ids='True',") 
        self.failUnless(ok)
        
    """def test_checkInstance(self):
        result = self.portal.cputils_checkInstance()
        self.failUnless(ok)
    
    def test_checkPOSKey(self):
        self.failUnless(False)
        
    def test_configure_fckeditor(self):
            self.failUnless(False)
        
    def test_copy_image_attribute(self):
        self.failUnless(False)"""
        
    def test_cpdb(self):
        print("push 'c' and then 'return' to pass the test")
        self.portal.cputils_cpdb()
        "cputils_cpdb test passed"
        
    def test_desactivate_base2dom(self):
        result = self.app.cputils_desactivate_base2dom()
        ok = result.find("Disabled ++resource++base2-dom-fp.js for /plone") > -1
        self.failUnless(ok)
        
    def test_install_plone_product(self):
        #TEST_INSTALL_PLONE_PRODUCT
        #DEPRECATION WARNING: QUICKINSTALLER WILL BE UNSUPORTED IN THE NEXT VERSIONS
        self.failUnless(True)
        
    def test_list_portlets(self):
        result = self.portal.cputils_list_portlets()
        ok = result.startswith("left: {u'login': <Assignment at login>, u'navigation': <Assignment at navigation>}")
        ok = ok and result.endswith("right: {u'news': <Assignment at news>, u'review': <Assignment at review>, u'events': <Assignment at events>, u'calendar': <Assignment at calendar>}")
        self.failUnless(ok)
        
    def test_list_users_param_sort(self):
        result = self.portal.cputils_list_users(self.portal,'csv','users')
        ok = result.endswith("<br />UserId,GroupId<br />admin,AuthenticatedUsers<br />member,AuthenticatedUsers<br />anon,AuthenticatedUsers<br />test_user_1_,AuthenticatedUsers")
        #result = self.portal.cputils_list_users('csv','groups')
        self.failUnless(ok)
        
    """def test_load_user_properties(self):
        self.failUnless(False)
        
    def test_object_info(self):
        self.failUnless(False)
        
    def test_recreate_users_groups(self):
        self.failUnless(False)
        
    def test_rename_long_ids(self):
        self.failUnless(False)
        
    def test_send_adminMail(self):
        self.failUnless(False)"""
            
    def test_store_user_properties(self): 
        result = self.portal.cputils_store_user_properties()
        ok = str(self.portal.users_properties).find("False	Kupu") > -1
        self.portal.cputils_change_user_properties(self.portal,'visible_ids:True',1)
        result = self.portal.cputils_store_user_properties()
        ok = ok and str(self.portal.users_properties).find("True	Kupu") > -1
        self.failUnless(ok)
        
    """def test_sync_properties(self):
        self.failUnless(False)  """   


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMethods))
    return suite

##code-section module-footer #fill in your manual code here
##/code-section module-footer

if __name__ == '__main__':
    framework()


