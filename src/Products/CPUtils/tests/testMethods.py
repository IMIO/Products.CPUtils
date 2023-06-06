# -*- coding: utf-8 -*-
from Products.CPUtils.tests.CPUtilsTestCase import CPUtilsTestCase

import os
import sys


if __name__ == "__main__":
    execfile(os.path.join(sys.path[0], "framework.py"))


class testMethods(CPUtilsTestCase):
    """Test-cases for class(es) ."""

    def afterSetUp(self):
        """
        """
        CPUtilsTestCase.afterSetup(self)

        self.loginAsPortalOwner()

    # Manually created methods

    def test_audit_catalog(self):
        result = self.portal.cputils_audit_catalog()
        ok = result.startswith(
            "<h1>RESULTATS DE LA RECHERCHE</h1> <p>Recherche dans : /</p> <p>Nombre d'elements trouves :"
        )
        ok = ok and result.find("portal_type : getObjSize : url") > -1
        self.failUnless(ok)

    def test_change_authentication_plugins_param_doChange(self):
        result = self.app.cputils_change_authentication_plugins(self.app, "", "")
        ok = result.startswith(
            "The following changes are not applied: you must run the script with the parameter '...?dochange=1'"
        )
        result = self.app.cputils_change_authentication_plugins(self.app, 1, "")
        ok = ok and result.startswith(
            "The following changes are not applied: you must run the script with the parameter '...?dochange=1'"
        )
        self.failUnless(ok)

    def test_change_authentication_plugins_param_activate(self):
        result = self.app.cputils_change_authentication_plugins(self.app, "", 1)
        ok = result.startswith("Document '/authentication_plugins_sites' added")
        ok = ok and result.find("Desactivate plugins source_users") > -1
        result = self.app.cputils_change_authentication_plugins(self.app, 1, 1)
        ok = ok and result.find("site found plone")
        ok = ok and result.find("Activate plugins source_users") > -1
        self.failUnless(ok)

    def test_change_user_properties_no_param(self):
        result = self.portal.cputils_change_user_properties(self.portal, "", "")
        ok = (
            result.find("USER:'member'") > -1
            and result.find("USER:'admin'") > -1
            and result.find("USER:'anon'") > -1
        )
        self.failUnless(ok)

    def test_change_user_properties_param_visibleIDs(self):
        result = self.portal.cputils_change_user_properties(
            self.portal, "visible_ids:True", ""
        )
        ok = (
            result.find("USER:'member'") > -1
            and result.find("USER:'admin'") > -1
            and result.find("USER:'anon'") > -1
        )
        ok = ok and result.find(" all properties: visible_ids='False'")
        result = self.portal.cputils_change_user_properties(
            self.portal, "visible_ids:True", 1
        )
        ok = (
            result.find("USER:'member'") > -1
            and result.find("USER:'admin'") > -1
            and result.find("USER:'anon'") > -1
        )
        ok = ok and result.find(
            "old properties: visible_ids='False',<br/>->  new properties: visible_ids='True',"
        )
        self.failUnless(ok)

    def test_cpdb(self):
        print("push 'c' and then 'return' to pass the test")
        # self.portal.cputils_cpdb()
        "cputils_cpdb test passed"

    def old_test_desactivate_base2dom(self):
        result = self.app.cputils_desactivate_base2dom()
        ok = result.find("Disabled ++resource++base2-dom-fp.js for /plone") > -1
        self.failUnless(ok)

    def old_test_list_portlets(self):
        result = self.portal.cputils_list_portlets()
        ok = result.startswith(
            "left: {u'login': <Assignment at login>, u'navigation': <Assignment at navigation>}"
        )
        ok = ok and result.endswith(
            "right: {u'news': <Assignment at news>, u'review': <Assignment at review>, u'events': <Assignment at events>, u'calendar': <Assignment at calendar>}"
        )
        self.failUnless(ok)

    def old_test_list_users_param_sort(self):
        result = self.portal.cputils_list_users(self.portal, "csv", "users")
        ok = result.endswith(
            "<br />UserId,GroupId<br />admin,AuthenticatedUsers<br />member,AuthenticatedUsers<br />anon,AuthenticatedUsers<br />test_user_1_,AuthenticatedUsers"
        )
        # result = self.portal.cputils_list_users('csv','groups')
        self.failUnless(ok)

    def old_test_store_user_properties(self):
        self.portal.cputils_store_user_properties()
        ok = str(self.portal.users_properties).find("False	Kupu") > -1
        self.portal.cputils_change_user_properties(self.portal, "visible_ids:True", 1)
        self.portal.cputils_store_user_properties()
        ok = ok and str(self.portal.users_properties).find("True	Kupu") > -1
        self.failUnless(ok)


def test_suite():
    from unittest import makeSuite
    from unittest import TestSuite

    suite = TestSuite()
    suite.addTest(makeSuite(testMethods))
    return suite


if __name__ == "__main__":
    import framework
    framework()
