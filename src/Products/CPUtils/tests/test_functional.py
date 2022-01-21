# -*- coding: utf-8 -*-
from Globals import package_home
from Products.CMFPlone.tests import PloneTestCase
from Testing.ZopeTestCase import FunctionalDocFileSuite as Suite
from zope.testing import doctest

import glob
import os
import sys
import unittest


if __name__ == "__main__":
    execfile(os.path.join(sys.path[0], "framework.py"))

PACKAGE = "Products.CPUtils.tests"

REQUIRE_TESTBROWSER = ["tst_CPUtils.txt"]

OPTIONFLAGS = (
    doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE
)


def list_doctests():
    home = package_home(globals())
    print home
    return [filename for filename in glob.glob(os.path.sep.join([home, "*.txt"]))]


def list_nontestbrowser_tests():
    return [
        filename
        for filename in list_doctests()
        if os.path.basename(filename) not in REQUIRE_TESTBROWSER
    ]


def setUp(self):
    uf = self.portal.acl_users
    uf.userFolderAddUser("member", "member", ["Member", ], [])
    uf.userFolderAddUser("admin", "admin", ["Manager", "Member", ], [])
    uf.userFolderAddUser("anon", "anon", ["Anonymous", ], [])
    # we have to be logged as a Manager to run methods from exportimport
    self.login("admin")
    self.logout()
    return None


def test_suite():
    filenames = list_doctests()
    suites = [
        Suite(
            os.path.basename(filename),
            optionflags=OPTIONFLAGS,
            package=PACKAGE,
            setUp=setUp,
            test_class=PloneTestCase.FunctionalTestCase,
        )
        for filename in filenames
    ]

    # BBB: Fix for http://zope.org/Collectors/Zope/2178
    from Products.PloneTestCase import layer
    from Products.PloneTestCase import setup

    if setup.USELAYER:
        for s in suites:
            if not hasattr(s, "layer"):
                s.layer = layer.PloneSite

    return unittest.TestSuite(suites)


if __name__ == "__main__":
    import framework
    framework()
