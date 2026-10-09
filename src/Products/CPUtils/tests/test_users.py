# -*- coding: utf-8 -*-
from io import StringIO
from logging.handlers import BufferingHandler
from Missing import Value
from plone import api
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.base.utils import safe_text
from Products.CPUtils.Extensions.utils import check_role
from Products.CPUtils.Extensions.utils import check_zope_admin
from Products.CPUtils.Extensions.utils import delete_users
from Products.CPUtils.Extensions.utils import fileSize
from Products.CPUtils.Extensions.utils import get_user_pwd_hash
from Products.CPUtils.Extensions.utils import get_users
from Products.CPUtils.Extensions.utils import log_list
from Products.CPUtils.Extensions.utils import object_link
from Products.CPUtils.Extensions.utils import reset_passwords
from Products.CPUtils.Extensions.utils import search_users_by_name
from Products.CPUtils.Extensions.utils import set_user_pwd_hash
from Products.CPUtils.Extensions.utils import tobytes
from Products.CPUtils.tests.CPUtilsTestCase import CPUtilsTestCase
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin

import logging
import sys


NOT_ZOPE_ADMIN = "You must be a zope manager to run this script"
NOT_MANAGER = "You must have a manager role to run this script"
# methods added by install on Plone 4 and Plone 6 (configure_ckeditor left out: lost on Plone 6)
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


class TestUsers(CPUtilsTestCase):
    """Users related external methods and helpers of Extensions/utils.py."""

    def setUp(self):
        super(TestUsers, self).setUp()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        login(self.portal, TEST_USER_NAME)

    def tearDown(self):
        logout()

    def authenticated(self, user_login, password):
        """Return True if the login/password pair is accepted by the site."""
        return self.portal.acl_users.authenticate(user_login, password, self.request) is not None

    def test_change_authentication_plugins(self):
        plugins = self.portal.acl_users.plugins
        active = list(plugins.listPluginIds(IAuthenticationPlugin))
        self.assertIn("source_users", active)
        # a Plone Manager is not a Zope admin
        self.assertEqual(self.app.cputils_change_authentication_plugins(activate="0", dochange="1"), NOT_ZOPE_ADMIN)
        login(self.app, SITE_OWNER_NAME)
        # iA.Docs call (scripts/disable-authentication.py): plugins saved in a DTML document and deactivated
        result = self.app.cputils_change_authentication_plugins(activate="0", dochange="1")
        self.assertIn("Document '/authentication_plugins_sites' added", result)
        self.assertIn("Desactivate plugins source_users for plone", result)
        self.assertNotIn("The following changes are not applied", result)
        self.assertEqual(plugins.listPluginIds(IAuthenticationPlugin), ())
        self.assertFalse(self.authenticated("member", "password"))
        self.assertEqual(self.app.authentication_plugins_sites.read(), "\t".join(["plone"] + active))
        # reactivation without dochange: nothing changes
        result = self.app.cputils_change_authentication_plugins(activate="1")
        self.assertIn("The following changes are not applied", result)
        self.assertIn("Activate plugins source_users for plone", result)
        self.assertEqual(plugins.listPluginIds(IAuthenticationPlugin), ())
        # reactivation from the DTML document
        result = self.app.cputils_change_authentication_plugins(activate="1", dochange="1")
        self.assertIn("site found plone", result)
        self.assertIn("Activate plugins source_users for plone", result)
        self.assertEqual(sorted(plugins.listPluginIds(IAuthenticationPlugin)), sorted(active))
        self.assertTrue(self.authenticated("member", "password"))
        # Plone 4 bug: without the DTML document, the message is lost and None is returned
        self.app.manage_delObjects(["authentication_plugins_sites"])
        self.assertIsNone(self.app.cputils_change_authentication_plugins(activate="1", dochange="1"))

    def test_change_user_properties(self):
        member = api.user.get("member")
        # without dochange, the new values are only displayed
        result = self.portal.cputils_change_user_properties(kw="fullname:Jean Dupont", filter="userid:member")
        self.assertIn("<h2>Users : total=2, filtered=1</h2>", result)
        self.assertIn("USER:'member'", result)
        self.assertNotIn("USER:'%s'" % TEST_USER_ID, result)
        self.assertIn("->  new values after change: fullname='Jean Dupont'", result)
        self.assertEqual(member.getProperty("fullname"), "")
        # with dochange, the property is really changed, only for the filtered user
        result = self.portal.cputils_change_user_properties(
            kw="fullname:Jean Dupont", filter="userid:member", dochange="1"
        )
        self.assertIn("->  old properties: fullname='',<br/>->  new properties: fullname='Jean Dupont',", result)
        self.assertEqual(api.user.get("member").getProperty("fullname"), "Jean Dupont")
        self.assertEqual(api.user.get(TEST_USER_ID).getProperty("fullname"), "")
        # filter on a property value
        result = self.portal.cputils_change_user_properties(filter="email:member@example.com")
        self.assertIn("<h2>Users : total=2, filtered=1</h2>", result)
        self.assertIn("USER:'member'", result)
        # malformed parameters are reported (a value can't contain ':')
        result = self.portal.cputils_change_user_properties(kw="fullname=Jean|home_page:http://x.be")
        self.assertIn("problem in param 'fullname=Jean'", result)
        self.assertIn("problem in param 'home_page:http://x.be'", result)
        self.assertIn("New properties dictionary={}", result)
        login(self.portal, "member")
        self.assertEqual(self.portal.cputils_change_user_properties(), NOT_MANAGER)

    def test_store_user_properties(self):
        result = self.portal.cputils_store_user_properties()
        self.assertEqual(
            result.split("\n"),
            [
                "Document '/plone/users_properties' added",
                "Current member 'member'",
                "Current member '%s'" % TEST_USER_ID,
                "Document '/plone/users_properties' updated !",
            ],
        )
        lines = [line.split("\t") for line in self.portal.users_properties.read().split("\n")]
        header = lines[0]
        self.assertEqual(header[:2], ["Count", "User"])
        self.assertEqual(header[2:], sorted(header[2:]))
        self.assertTrue({"email", "fullname", "listed"}.issubset(header))
        rows = dict((line[1], dict(zip(header, line))) for line in lines[1:])
        self.assertEqual(sorted(rows), ["member", TEST_USER_ID])
        self.assertEqual(rows["member"]["Count"], "001")
        self.assertEqual(rows["member"]["email"], "member@example.com")
        self.assertEqual(rows["member"]["listed"], "True")
        # second call updates the document
        api.user.get("member").setMemberProperties({"email": "new@example.com"})
        result = self.portal.cputils_store_user_properties()
        self.assertNotIn("added", result)
        self.assertIn("member\t\tnew@example.com", self.portal.users_properties.read())
        login(self.portal, "member")
        self.assertEqual(self.portal.cputils_store_user_properties(), NOT_MANAGER)

    def test_list_users(self):
        api.group.add_user(groupname="Reviewers", username="member")
        # default: csv sorted by users, with group title
        lines = self.portal.cputils_list_users().split("<br />\n")
        self.assertEqual(lines[0], "<h2>Users list</h2>")
        self.assertEqual(
            lines[-3:],
            [
                "UserId;GroupId;GroupTitle;Username;Email;UserGlobalRoles;GroupGlobalRoles",
                "member;Reviewers;Reviewers;;member@example.com;Reviewer;Reviewer",
                "%s;aucun;;;;Manager;" % TEST_USER_ID,
            ],
        )
        # csv sorted by groups, without group title, other separator
        lines = self.portal.cputils_list_users(sort="groups", gtitle="0", separator=",").split("<br />\n")
        self.assertEqual(
            lines[-3:],
            [
                "GroupId,UserId,Username,Email,GroupGlobalRoles,UserGlobalRoles",
                "Reviewers,member,,member@example.com,Reviewer,Reviewer",
                "aucun,%s,,,,Manager" % TEST_USER_ID,
            ],
        )
        # no global roles columns
        lines = self.portal.cputils_list_users(ignored_global_roles="*").split("<br />\n")
        self.assertEqual(lines[-3], "UserId;GroupId;GroupTitle;Username;Email")
        # screen output
        lines = self.portal.cputils_list_users(output="screen", sort="groups").split("<br />\n")
        self.assertEqual(
            lines[-4:],
            [
                "- groupid: Reviewers, Reviewers, global roles: Reviewer",
                "&emsp;&emsp;&rArr; member, fullname: , email: member@example.com, global roles: Reviewer",
                "- groupid: aucun, , global roles: ",
                "&emsp;&emsp;&rArr; %s, fullname: , email: , global roles: Manager" % TEST_USER_ID,
            ],
        )
        lines = self.portal.cputils_list_users(output="screen").split("<br />\n")
        self.assertEqual(
            lines[-4:],
            [
                "- userid: member, fullname: , email: member@example.com, global roles: Reviewer",
                "&emsp;&emsp;&rArr; Reviewers, Reviewers, global roles: Reviewer",
                "- userid: %s, fullname: , email: , global roles: Manager" % TEST_USER_ID,
                "&emsp;&emsp;&rArr; aucun, , global roles: ",
            ],
        )
        # Plone 4 bug: invalid parameters return None, the message is lost
        self.assertIsNone(self.portal.cputils_list_users(sort="roles"))
        self.assertIsNone(self.portal.cputils_list_users(output="pdf"))
        login(self.portal, "member")
        self.assertEqual(self.portal.cputils_list_users(), NOT_MANAGER)

    def test_check_users(self):
        self.assertEqual(self.portal.cputils_check_users(), "Le userid '%s' n'a pas d'adresse email" % TEST_USER_ID)
        api.user.get("member").setMemberProperties({"email": "member.example.com"})
        self.assertEqual(
            self.portal.cputils_check_users().split("\n"),
            [
                "L'email 'member.example.com' du userid 'member' n'est pas valide",
                "Le userid '%s' n'a pas d'adresse email" % TEST_USER_ID,
            ],
        )
        login(self.portal, "member")
        self.assertEqual(self.portal.cputils_check_users(), NOT_MANAGER)

    def test_check_groups_users(self):
        # needs the iA.Docs packages (collective.contact.plonegroup, collective.wfadaptations, imio.dms.mail)
        self.assertRaises(ImportError, self.portal.cputils_check_groups_users)
        login(self.portal, "member")
        self.assertEqual(self.portal.cputils_check_groups_users(), NOT_MANAGER)

    def test_get_user_pwd_hash(self):
        self.assertEqual(get_user_pwd_hash(self.portal, "member"), NOT_ZOPE_ADMIN)
        login(self.app, SITE_OWNER_NAME)
        self.assertEqual(get_user_pwd_hash(self.portal, "nobody"), "Cannot find password for userid 'nobody'")
        result = get_user_pwd_hash(self.portal, "member")
        self.assertTrue(result.startswith("'member' = '{SSHA}"), result)
        pwd_hash = safe_text(self.portal.acl_users.source_users._user_passwords["member"])
        self.assertEqual(result, "'member' = '%s'" % pwd_hash)

    def test_set_user_pwd_hash(self):
        # hash of the test user password, as copied from get_user_pwd_hash
        pwd_hash = safe_text(self.portal.acl_users.source_users._user_passwords[TEST_USER_ID])
        self.assertEqual(set_user_pwd_hash(self.portal, "member", pwd_hash, "1"), NOT_ZOPE_ADMIN)
        login(self.app, SITE_OWNER_NAME)
        result = set_user_pwd_hash(self.portal, "nobody", pwd_hash, "1")
        self.assertTrue(result.startswith("call the script followed by needed parameters:"))
        self.assertTrue(result.endswith("\nCannot find userid 'nobody' in passwords"))
        self.assertTrue(set_user_pwd_hash(self.portal, "member", "secret", "1").endswith("\nPassword not hashed !"))
        result = set_user_pwd_hash(self.portal, "member", pwd_hash)
        self.assertTrue(
            result.endswith(
                "\n'member' passwd WILL be replaced with '%s'. Check if what's displayed is correct !" % pwd_hash
            )
        )
        self.assertTrue(self.authenticated("member", "password"))
        result = set_user_pwd_hash(self.portal, "member", pwd_hash, "1")
        self.assertTrue(result.endswith("\n'member' passwd is replaced with '%s'" % pwd_hash))
        self.assertFalse(self.authenticated("member", "password"))
        self.assertTrue(self.authenticated("member", TEST_USER_PASSWORD))

    def test_delete_users(self):
        api.user.create(username="gmailer", email="gmailer@gmail.com", password="password")
        expected = (
            "<h1>all Users</h1><br/>"
            "<span>gmailer, gmailer@gmail.com, kept</span><br/>"
            "<span>member, member@example.com, deleted</span><br/>"
            "<span>%s, , kept</span>" % TEST_USER_ID
        )
        self.assertEqual(delete_users(self.portal), expected)
        self.assertIsNotNone(api.user.get("member"))
        self.assertEqual(delete_users(self.portal, delete=True), expected)
        self.assertIsNone(api.user.get("member"))
        self.assertIsNotNone(api.user.get("gmailer"))
        login(self.portal, "gmailer")
        self.assertEqual(delete_users(self.portal), NOT_MANAGER)

    def test_reset_passwords(self):
        self.assertEqual(reset_passwords(self.portal), NOT_ZOPE_ADMIN)
        login(self.app, SITE_OWNER_NAME)
        result = reset_passwords(self.portal)
        self.assertIn("Userids exceptions: 'siteadmin'\nTotal users: 2\nTotal exceptions: 1\nIntersection: 0 => ", result)
        self.assertIn("Total reset: 2", result)
        self.assertTrue(result.endswith("\nReset not really done"))
        self.assertTrue(self.authenticated("member", "password"))
        result = reset_passwords(self.portal, not_for_ids=TEST_USER_ID, dochange="1")
        self.assertIn("Intersection: 1 => %s\nTotal reset: 1" % TEST_USER_ID, result)
        self.assertTrue(result.endswith("\nReset really done"))
        self.assertFalse(self.authenticated("member", "password"))
        self.assertTrue(self.authenticated(TEST_USER_NAME, TEST_USER_PASSWORD))

    def test_search_users_by_name(self):
        self.assertEqual(search_users_by_name(self.app, filter_login="mem"), NOT_ZOPE_ADMIN)
        api.user.get("member").setMemberProperties({"fullname": "Jean Dupont"})
        login(self.app, SITE_OWNER_NAME)
        member_line = "/plone, id: member, mail: member@example.com, fullname: Jean Dupont"
        # login filter matches Zope root users and site users, case insensitive
        lines = search_users_by_name(self.app, filter_login="MEM,adm").split("<br />\n")
        self.assertEqual(lines[0], "<strong>Search users </strong>")
        self.assertEqual(lines[-2:], ["Zope, id: admin", member_line])
        self.assertEqual(search_users_by_name(self.app, filter_name="dup").split("<br />\n")[-1], member_line)
        self.assertEqual(search_users_by_name(self.app, filter_mail="example").split("<br />\n")[-1], member_line)
        self.assertEqual(search_users_by_name(self.app).split("<br />\n")[-1], "")

    def test_install(self):
        login(self.portal, "member")
        self.assertEqual(self.app.cputils_install(), NOT_ZOPE_ADMIN)
        login(self.app, SITE_OWNER_NAME)
        # all methods are installed by the default profile
        self.assertEqual(self.app.cputils_install(), "<div>Those methods have been added: </div>")
        self.app.manage_delObjects(
            [oid for oid in self.app.objectIds() if oid.startswith("cputils_") and oid != "cputils_install"]
        )
        result = self.app.cputils_install()
        self.assertTrue(result.startswith("<div>Those methods have been added: cputils_add_subject<br />"))
        added = result[len("<div>Those methods have been added: "):-len("</div>")].split("<br />")
        self.assertTrue(set("cputils_" + name for name in INSTALLED_METHODS).issubset(added))
        self.assertTrue(set(added).issubset(self.app.objectIds()))
        self.assertEqual(self.app.cputils_install(), "<div>Those methods have been added: </div>")

    def test_check_zope_admin(self):
        # a Plone Manager is not a Zope admin
        self.assertFalse(check_zope_admin())
        login(self.portal, "member")
        self.assertFalse(check_zope_admin())
        login(self.app, SITE_OWNER_NAME)
        self.assertTrue(check_zope_admin())

    def test_log_list(self):
        lst = []
        stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            log_list(lst, "first line")
            log_list(lst, "error line", level="error")
            printed = sys.stdout.getvalue()
        finally:
            sys.stdout = stdout
        self.assertEqual(printed, ">> first line\n!! error line\n")
        logger = logging.getLogger("Products.CPUtils.tests")
        handler = BufferingHandler(10)
        logger.addHandler(handler)
        try:
            log_list(lst, "warning line", logger=logger, level="warn")
        finally:
            logger.removeHandler(handler)
        self.assertEqual([(rec.levelname, rec.getMessage()) for rec in handler.buffer], [("WARNING", "warning line")])
        self.assertEqual(lst, ["first line", "error line", "warning line"])

    def test_object_link(self):
        doc = api.content.create(container=self.portal, type="Document", id="doc", title="My document")
        self.assertEqual(object_link(doc), '<a href="http://nohost/plone/doc/view">My document</a>')
        self.assertEqual(object_link(doc, view=""), '<a href="http://nohost/plone/doc">My document</a>')
        self.assertEqual(object_link(doc, view="edit", attribute="id"), '<a href="http://nohost/plone/doc/edit">doc</a>')
        self.assertEqual(object_link(doc, attribute="unknown"), '<a href="http://nohost/plone/doc/view">My document</a>')
        self.assertEqual(
            object_link(doc, content="Open", target="_blank"),
            '<a href="http://nohost/plone/doc/view" target="_blank">Open</a>',
        )

    def test_get_users(self):
        self.assertEqual(get_users(self.portal, obj=False), ["member", TEST_USER_ID])
        self.assertEqual([member.getId() for member in get_users(self.portal)], ["member", TEST_USER_ID])
        self.assertEqual(get_users(self.portal)[0].getProperty("email"), "member@example.com")

    def test_check_role(self):
        doc = api.content.create(container=self.portal, type="Document", id="doc")
        doc.manage_setLocalRoles("member", ["Editor"])
        self.assertTrue(check_role(self.portal))
        self.assertFalse(check_role(self.portal, role="Reviewer"))
        login(self.portal, "member")
        self.assertFalse(check_role(self.portal))
        self.assertTrue(check_role(self.portal, role="Member"))
        self.assertFalse(check_role(self.portal, role="Editor"))
        self.assertTrue(check_role(self.portal, role="Editor", context=doc))

    def test_fileSize(self):
        self.assertEqual(fileSize(512), "0.5k")
        self.assertEqual(fileSize(1536), "1.5k")
        self.assertEqual(fileSize(1536, decimal=","), "1,5k")
        self.assertEqual(fileSize(5 * 1024 ** 2), "5.0M")
        self.assertEqual(fileSize(3 * 1024 ** 3), "3.0G")
        self.assertEqual(fileSize(5 * 1024 ** 2, as_size="k"), "5120.0k")
        self.assertEqual(fileSize(5 * 1024 ** 2, as_size="M", rm_sz=True), "5.0")
        # rm_sz needs as_size, an unknown as_size is ignored
        self.assertEqual(fileSize(5 * 1024 ** 2, rm_sz=True), "5.0M")
        self.assertEqual(fileSize(5 * 1024 ** 2, as_size="X"), "5.0M")
        # Plone 4 bug: the T unit is never used
        self.assertEqual(fileSize(3 * 1024 ** 4), "3072.0G")
        self.assertEqual(fileSize(3 * 1024 ** 4, as_size="T"), "3072.0G")

    def test_tobytes(self):
        self.assertEqual(tobytes(Value), "No object size in catalog")
        self.assertEqual(tobytes("1.5 KB"), 1536.0)
        self.assertEqual(tobytes("2 MB"), 2097152.0)
        self.assertEqual(tobytes("12"), "Problem when splitting '12' obj size in 2 parts")
        self.assertEqual(tobytes("abc KB"), "First part 'abc' of objsize 'abc KB' isn't float")
        # Plone 4 bug: other units return the split parts
        self.assertEqual(tobytes("1 GB"), ["1", "GB"])
