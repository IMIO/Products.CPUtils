# -*- coding: utf-8 -*-

from plone import api
from plone.app.testing import login, logout, TEST_USER_ID, TEST_USER_NAME, setRoles
from Products.CPUtils.tests.CPUtilsTestCase import CPUtilsTestCase
from Products.CPUtils.Extensions.utils import folder_position


class testMethods(CPUtilsTestCase):
    """Test-cases for class(es) ."""

    def setUp(self):
        super().setUp()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)

    def tearDown(self):
        logout()

    def test_audit_catalog(self):
        result = self.portal.cputils_audit_catalog()
        ok = result.startswith(
            "<h1>RESULTATS DE LA RECHERCHE</h1> <p>Recherche dans : /</p> <p>Nombre d'elements trouves :"
        )
        ok = ok and result.find("portal_type : getObjSize : url") > -1
        self.assertTrue(ok)

    def test_change_authentication_plugins_param_doChange(self):
        login(self.app, "admin")
        result = self.app.cputils_change_authentication_plugins(self.app, "", "")
        ok = result.startswith(
            "The following changes are not applied: you must run the script with the parameter '...?dochange=1'"
        )
        result = self.app.cputils_change_authentication_plugins(self.app, 1, "")
        ok = ok and result.startswith(
            "The following changes are not applied: you must run the script with the parameter '...?dochange=1'"
        )
        self.assertTrue(ok)

    def test_change_authentication_plugins_param_activate(self):
        login(self.app, "admin")
        result = self.app.cputils_change_authentication_plugins(self.app, "", 1)
        ok = result.startswith("Document '/authentication_plugins_sites' added")
        ok = ok and result.find("Desactivate plugins source_users") > -1
        result = self.app.cputils_change_authentication_plugins(self.app, 1, 1)
        ok = ok and result.find("site found plone")
        ok = ok and result.find("Activate plugins source_users") > -1
        self.assertTrue(ok)

    def test_change_user_properties_no_param(self):
        result = self.portal.cputils_change_user_properties(self.portal, "", "")
        ok = (
            result.find("USER:'member'") > -1
            and result.find(f"USER:'{TEST_USER_ID}'") > -1
        )
        self.assertTrue(ok)

    def test_change_user_properties_param_visibleIDs(self):
        result = self.portal.cputils_change_user_properties(
            self.portal, "visible_ids:True", ""
        )
        ok = (
            result.find("USER:'member'") > -1
            and result.find(f"USER:'{TEST_USER_ID}'") > -1
        )
        ok = ok and result.find(" all properties: visible_ids='False'")
        result = self.portal.cputils_change_user_properties(
            self.portal, "visible_ids:True", 1
        )
        ok = (
            result.find("USER:'member'") > -1
            and result.find(f"USER:'{TEST_USER_ID}'") > -1
        )
        ok = ok and result.find(
            "old properties: visible_ids='False',<br/>->  new properties: visible_ids='True',"
        )
        self.assertTrue(ok)

    def test_cpdb(self):
        print("push 'c' and then 'return' to pass the test")
        # self.portal.cputils_cpdb()
        "cputils_cpdb test passed"

    def test_folder_position(self):
        folder = api.content.create(type="Folder", id="container", container=self.portal)
        api.content.create(type="Document", id="d1", container=folder)
        api.content.create(type="Document", id="d2", container=folder)
        api.content.create(type="Document", id="d3", container=folder)
        api.content.create(type="Document", id="d4", container=folder)
        self.assertEqual(["d1", "d2", "d3", "d4"], folder.objectIds())
        folder_position(folder, "down", "d1")
        self.assertEqual(["d2", "d1", "d3", "d4"], folder.objectIds())
        folder_position(folder, "down", "d4")
        self.assertEqual(["d2", "d1", "d3", "d4"], folder.objectIds())
        folder_position(folder, "bottom", "d1")
        self.assertEqual(["d2", "d3", "d4", "d1"], folder.objectIds())
        folder_position(folder, "bottom", "d1")
        self.assertEqual(["d2", "d3", "d4", "d1"], folder.objectIds())
        folder_position(folder, "up", "d1")
        self.assertEqual(["d2", "d3", "d1", "d4"], folder.objectIds())
        folder_position(folder, "up", "d2")
        self.assertEqual(["d2", "d3", "d1", "d4"], folder.objectIds())
        folder_position(folder, "top", "d1")
        self.assertEqual(["d1", "d2", "d3", "d4"], folder.objectIds())
        folder_position(folder, "top", "d1")
        self.assertEqual(["d1", "d2", "d3", "d4"], folder.objectIds())

    def test_folder_position_typeaware(self):
        folder = api.content.create(type="Folder", id="container", container=self.portal)
        api.content.create(type="Folder", id="f1", container=folder)
        api.content.create(type="Document", id="d1", container=folder)
        api.content.create(type="Document", id="d2", container=folder)
        api.content.create(type="Folder", id="f2", container=folder)
        api.content.create(type="Document", id="d3", container=folder)
        self.assertEqual(["f1", "d1", "d2", "f2", "d3"], folder.objectIds())
        folder_position(folder, "down", "f1", typeaware=True)
        self.assertEqual(["d1", "d2", "f2", "f1", "d3"], folder.objectIds())
        folder_position(folder, "up", "d3", typeaware=True)
        self.assertEqual(["d1", "d3", "d2", "f2", "f1"], folder.objectIds())
        folder_position(folder, "top", "f1", typeaware=True)
        self.assertEqual(["f1", "d1", "d3", "d2", "f2"], folder.objectIds())
        folder_position(folder, "bottom", "d1", typeaware=True)
        self.assertEqual(["f1", "d3", "d2", "f2", "d1"], folder.objectIds())
