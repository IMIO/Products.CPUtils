# -*- coding: utf-8 -*-

from plone import api
from Products.CMFCore.utils import getToolByName
from Products.CPUtils.testing import CPUTILS_INTEGRATION_TESTING

import unittest


class CPUtilsTestCase(unittest.TestCase):
    """Base TestCase for CPUtils."""

    layer = CPUTILS_INTEGRATION_TESTING

    def setUp(self):
        """
        Manage users and permissions
        """
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.wft = getToolByName(self.portal, "portal_workflow")
        api.user.create(
            username="member",
            email="member@example.com",
            roles=("Member",),
            password="password",
        )
