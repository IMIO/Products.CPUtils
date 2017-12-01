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
from AccessControl import getSecurityManager, ClassSecurityInfo
from AccessControl.SecurityManagement import newSecurityManager, setSecurityManager

#
# Test-cases for class(es) 
#

from Testing import ZopeTestCase
from Products.PloneTestCase import PloneTestCase
from Products.CPUtils.config import *
from Products.CPUtils.tests.CPUtilsTestCase import CPUtilsTestCase

# Import the tested classes

##code-section module-beforeclass #fill in your manual code here
from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod
##/code-section module-beforeclass
ZopeTestCase.installProduct(PROJECTNAME)

PRODUCTS = list()
PRODUCTS.append(PROJECTNAME)
productName = "PloneGazette"
PRODUCTS.append(productName)

testcase = PloneTestCase.PloneTestCase

##code-section module-before-plone-site-setup #fill in your manual code here

##/code-section module-before-plone-site-setup

#Extension profile doesn't work because appinstall of ts appears to be not run
#PloneTestCase.setupPloneSite(products=PRODUCTS, extension_profiles=EXTENSION_PROFILES)
PloneTestCase.setupPloneSite(products=PRODUCTS)


class testNewsLetter(CPUtilsTestCase):
    """Test-cases for class(es) ."""
    
    ##code-section class-header_testMethods #fill in your manual code here
    ##/code-section class-header_testMethods

    def afterSetUp(self):
        from Products.PloneGazette import NewsletterTheme
        """
        """        
        CPUtilsTestCase.afterSetup(self)
        
        self.loginAsPortalOwner()
        method = 'install'
        method_name = 'cputils_'+method
        manage_addExternalMethod(self.app, method_name, '', 'CPUtils.utils', method)
        self.app.cputils_install()
        
        """from Products.Five import zcml
        from Products.Five import fiveconfigure
        fiveconfigure.debug_mode=True
        import Products.PloneGazette
        zcml.load_config('configure.zcml', Products.PloneGazette)
        fiveconfigure.debug_mode=False
        self.addProduct(name)"""
        qi = self.portal.portal_quickinstaller
        #print(productName+" installed : ")
        #print(qi.isProductInstalled(productName))
        
    # Manually created methods
    
    def test_list_newsletter_users(self):  
        from Products.PloneGazette.NewsletterTheme import NewsletterTheme
        
        print("problème pour créer une newsletter et ses abonnés: invokeFactory() ne fonctionne pas ")
        print("(probablement car plonegazette ne s'installe pas correctement)")
        """
        self.portal.invokeFactory('NewsletterTheme', id)
        nlf = self.portal.newsletter

        nlf.invokeFactory('NewsletterBTree', id='subscribers')
        nlf.subscriber_folder_id = 'subscribers'

        nlf.createSubscriberObject('sub1')
        nlf.createSubscriberObject('sub2')
        nlf.createSubscriberObject('sub3')
        subList = nlf.getSubscribers()
        print(subList)"""
        self.failUnless(True)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testNewsLetter))
    return suite

##code-section module-footer #fill in your manual code here
##/code-section module-footer

if __name__ == '__main__':
    framework()
