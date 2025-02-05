# -*- coding: utf-8 -*-

import unittest

from plone import api
from plone.app.testing import (
    PLONE_FIXTURE,
    PloneSandboxLayer,
    IntegrationTesting,
    applyProfile,
)
from Products.CMFCore.utils import getToolByName
import Products.CPUtils


class CPUtilsLayer(PloneSandboxLayer):
    """"""

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=Products.CPUtils)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "Products.CPUtils:default")


CPUTILS_INTEGRATION_TESTING = IntegrationTesting(
    bases=(CPUtilsLayer(),),
    name="CPUtils:Integration",
)


class CPUtilsTestCase(unittest.TestCase):
    """Base TestCase for contacts."""

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


def test_suite():
    from unittest import makeSuite
    from unittest import TestSuite

    suite = TestSuite()
    suite.addTest(makeSuite(CPUtilsTestCase))
    return suite
