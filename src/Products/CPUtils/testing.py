# -*- coding: utf-8 -*-
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer

import Products.CPUtils
import unittest


try:
    from plone.testing.zope import WSGI_SERVER_FIXTURE as SERVER_FIXTURE
except ImportError:  # Plone 4
    from plone.testing.z2 import ZSERVER_FIXTURE as SERVER_FIXTURE


try:
    from importlib.metadata import version
except ImportError:  # Python 2
    from pkg_resources import get_distribution

    def version(name):
        return get_distribution(name).version


PLONE_MAJOR = int(version("Products.CMFPlone").split(".")[0])


def plone6_bug(func):
    """Plone 4 behaviour pinned by the test, broken on Plone 6: fixed in the Plone 6 phase."""
    return unittest.expectedFailure(func) if PLONE_MAJOR >= 5 else func


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
    bases=(FIXTURE, REMOTE_LIBRARY_BUNDLE_FIXTURE, SERVER_FIXTURE),
    name="CPUtils:Acceptance",
)
