# -*- coding: utf-8 -*-
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing.zope import WSGI_SERVER_FIXTURE

import Products.CPUtils


class CPUtilsLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=Products.CPUtils)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "Products.CPUtils:default")


FIXTURE = CPUtilsLayer(name="CPUtils:Fixture")

CPUTILS_INTEGRATION_TESTING = IntegrationTesting(bases=(FIXTURE,), name="CPUtils:Integration")

CPUTILS_FUNCTIONAL_TESTING = FunctionalTesting(bases=(FIXTURE,), name="CPUtils:Functional")

ACCEPTANCE = FunctionalTesting(
    bases=(FIXTURE, REMOTE_LIBRARY_BUNDLE_FIXTURE, WSGI_SERVER_FIXTURE),
    name="CPUtils:Acceptance",
)
