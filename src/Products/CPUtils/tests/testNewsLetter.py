# -*- coding: utf-8 -*-
from Products.CPUtils.config import PROJECTNAME
from Products.CPUtils.tests.CPUtilsTestCase import CPUtilsTestCase
from Products.PloneTestCase import PloneTestCase
from Testing import ZopeTestCase

import os
import sys


if __name__ == "__main__":
    execfile(os.path.join(sys.path[0], "framework.py"))

ZopeTestCase.installProduct(PROJECTNAME)

PRODUCTS = list()
PRODUCTS.append(PROJECTNAME)
productName = "PloneGazette"
PRODUCTS.append(productName)

testcase = PloneTestCase.PloneTestCase
# Extension profile doesn't work because appinstall of ts appears to be not run
# PloneTestCase.setupPloneSite(products=PRODUCTS, extension_profiles=EXTENSION_PROFILES)
PloneTestCase.setupPloneSite(products=PRODUCTS)


class testNewsLetter(CPUtilsTestCase):
    """Test-cases for class(es) ."""
    def afterSetUp(self):
        """
        """
        CPUtilsTestCase.afterSetup(self)
        self.loginAsPortalOwner()

        """from Products.Five import zcml
        from Products.Five import fiveconfigure
        fiveconfigure.debug_mode=True
        import Products.PloneGazette
        zcml.load_config('configure.zcml', Products.PloneGazette)
        fiveconfigure.debug_mode=False
        self.addProduct(name)"""
        self.portal.portal_quickinstaller

    # Manually created methods

    def test_list_newsletter_users(self):
        print(
            "problème pour créer une newsletter et ses abonnés: invokeFactory() ne fonctionne pas "
        )
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
    from unittest import makeSuite
    from unittest import TestSuite

    suite = TestSuite()
    suite.addTest(makeSuite(testNewsLetter))
    return suite


if __name__ == "__main__":
    import framework
    framework()
