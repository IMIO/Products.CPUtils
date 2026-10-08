# -*- coding: utf-8 -*-
from plone.app.testing import applyProfile
from Products.CPUtils.testing import CPUTILS_FUNCTIONAL_TESTING
from Products.CPUtils.tests.CPUtilsTestCase import CPUtilsTestCase

import transaction
import unittest


try:
    from plone.testing.zope import Browser
except ImportError:  # Plone 4
    from plone.testing.z2 import Browser

# methods installed by cputils_install on Plone 4 and 6
INSTALLED_METHODS = (
    "add_subject",
    "audit_catalog",
    "change_authentication_plugins",
    "change_user_properties",
    "check_groups_users",
    "check_users",
    "clean_provides_for",
    "clean_utilities_for",
    "cpdb",
    "creators",
    "del_object",
    "del_objects",
    "list_context_portlets_by_name",
    "list_local_roles",
    "list_objects",
    "list_portlets",
    "list_used_views",
    "list_users",
    "move_copy_objects",
    "move_item",
    "obj_from_uid",
    "object_info",
    "objects_stats",
    "order_folder",
    "removeStep",
    "set_attr",
    "show_object_relations",
    "store_user_properties",
    "uid",
    "unlock_webdav_objects",
)


class TestDefaultProfile(CPUtilsTestCase):

    def test_default_profile(self):
        self.assertEqual(self.app.cputils_install.meta_type, "External Method")
        for method in INSTALLED_METHODS:
            self.assertEqual(getattr(self.app, "cputils_" + method).meta_type, "External Method")
        # the methods are acquired from the Zope root
        self.assertIn("current object id='plone'", self.portal.cputils_object_info())


class TestRobotsProfile(unittest.TestCase):

    layer = CPUTILS_FUNCTIONAL_TESTING

    def robots_lines(self):
        """robots.txt as anonymous gets it"""
        browser = Browser(self.layer["app"])
        browser.open(self.layer["portal"].absolute_url() + "/robots.txt")
        return [line.strip() for line in browser.contents.splitlines()]

    def test_robots_profile(self):
        self.assertNotIn("Disallow: /", self.robots_lines())
        applyProfile(self.layer["portal"], "Products.CPUtils:robots")
        transaction.commit()
        lines = self.robots_lines()
        self.assertIn("User-agent: *", lines)
        self.assertIn("Disallow: /", lines)
