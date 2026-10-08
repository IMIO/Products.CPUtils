# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone import api
from plone.app.portlets.portlets import navigation
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import login
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.locking.interfaces import ILockable
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletManager
from Products.CPUtils.Extensions import utils
from Products.CPUtils.testing import FIXTURE
from Products.CPUtils.tests.CPUtilsTestCase import CPUtilsTestCase
from z3c.relationfield import RelationValue
from z3c.relationfield.event import _setRelation
from zope.component import getMultiAdapter
from zope.component import getSiteManager
from zope.component import getUtility
from zope.component.interface import provideInterface
from zope.interface import alsoProvides
from zope.interface import Interface
from zope.intid.interfaces import IIntIds

import plone.app.relationfield
import plone.behavior
import transaction


ZOPE_ADMIN_ONLY = "You must be a zope manager to run this script"
MANAGER_ONLY = "You must have a manager role to run this script"


class ILeftover(Interface):
    """Marker interface left by a product removed from the file system."""


class LeftoverAdapter(object):
    """Adapter left by a removed product."""

    def __init__(self, context):
        self.context = context


class LeftoverUtility(object):
    """Utility left by a removed product."""


class RelationsLayer(PloneSandboxLayer):
    """Intids and relation catalog on both Plone versions (Plone 4.3 has none by default)."""

    defaultBases = (FIXTURE,)

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=plone.behavior, name="meta.zcml")
        self.loadZCML(package=plone.app.relationfield)
        provideInterface("", ILeftover)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "plone.app.relationfield:default")


RELATIONS_FIXTURE = RelationsLayer(name="CPUtils:RelationsFixture")
CONTENT_INTEGRATION = IntegrationTesting(bases=(RELATIONS_FIXTURE,), name="CPUtils:ContentIntegration")
CONTENT_FUNCTIONAL = FunctionalTesting(bases=(RELATIONS_FIXTURE,), name="CPUtils:ContentFunctional")


class ContentTestCase(CPUtilsTestCase):
    """A folder with a document, created by the Zope admin."""

    layer = CONTENT_INTEGRATION

    def setUp(self):
        super(ContentTestCase, self).setUp()
        login(self.app, SITE_OWNER_NAME)
        self.folder = api.content.create(type="Folder", id="folder", title="Folder", container=self.portal)
        self.doc = api.content.create(type="Document", id="doc", title="My doc", container=self.folder)

    def assert_denied(self, method, message, *args, **kwargs):
        """A simple member gets the message instead of the result."""
        login(self.portal, TEST_USER_NAME)
        self.assertEqual(method(*args, **kwargs), message)
        login(self.app, SITE_OWNER_NAME)

    def add_portlet(self, context, column="plone.leftcolumn"):
        manager = getUtility(IPortletManager, name=column)
        getMultiAdapter((context, manager), IPortletAssignmentMapping)["navigation"] = navigation.Assignment()

    def relate(self, source, target):
        rel = RelationValue(getUtility(IIntIds).getId(target))
        _setRelation(source, "relatedItems", rel)
        return rel


class TestContent(ContentTestCase):
    """External methods acting on content."""

    def test_object_info(self):
        lines = self.doc.cputils_object_info().split("\n")
        self.assertEqual(lines[0], "current object path='/folder/doc'")
        self.assertEqual(lines[1], "current object id='doc'")
        self.assertEqual(lines[2], "current object UID='%s'" % self.doc.UID())
        self.assertEqual(lines[3], "current object externalIdentifier=''")
        self.assertTrue(lines[4].startswith("current object portal_type/meta_type/class='Document'/"))
        self.assertEqual(lines[5], "is folderish='0'")
        self.assertEqual(lines[6], "creator='admin'")
        self.assertIn("> workflows='-'", lines)
        self.assertIn("> state='-'", lines)
        self.assertIn("\t'admin' has roles 'Owner'", lines)
        # release 1.26: external identifier of imported objects
        self.doc.externalIdentifier = "ext-123"
        self.assertIn("current object externalIdentifier='ext-123'", self.doc.cputils_object_info())
        # with a workflow
        self.wft.setChainForPortalTypes(("Document",), ("simple_publication_workflow",))
        doc2 = api.content.create(type="Document", id="doc2", title="Other doc", container=self.folder)
        lines = doc2.cputils_object_info().split("\n")
        self.assertIn("> workflows='simple_publication_workflow'", lines)
        self.assertIn("> state='private'", lines)
        self.assertIn("> Permissions info for state 'private' in workflow 'simple_publication_workflow'", lines)
        self.assertIn(
            "\t'View' for 'Manager, Owner, Editor, Reader, Contributor, Site Administrator', acquired=0", lines
        )
        # local roles
        api.user.grant_roles(username="member", obj=doc2, roles=["Editor"])
        self.assertIn("\t'member' has roles 'Editor'", doc2.cputils_object_info().split("\n"))

    def test_audit_catalog(self):
        result = self.portal.cputils_audit_catalog()
        self.assertIn(" : Document : ", result)
        self.assertIn('<a href="http://nohost/plone/folder/doc/view">http://nohost/plone/folder/doc/view</a>', result)
        self.assertTrue(result.endswith("<br /><br />FIN"))
        self.assert_denied(self.portal.cputils_audit_catalog, MANAGER_ONLY)

    def test_add_subject(self):
        add_subject = self.portal.cputils_add_subject
        self.assertIn("!! You must give the subject name with 'subject' parameter", add_subject())
        result = add_subject(type="Document", subject="archives")
        self.assertIn("Count of objects:1", result)
        self.assertIn("/plone/folder/doc -> will add subject to subjects:'archives'", result)
        self.assertEqual(self.doc.Subject(), ())
        result = add_subject(dochange="1", type="Document", subject="archives")
        self.assertIn("/plone/folder/doc -> added subject to subjects:'archives'", result)
        self.assertEqual(self.doc.Subject(), ("archives",))
        self.assertEqual(len(api.content.find(Subject="archives")), 1)
        result = add_subject(dochange="1", type="Document", subject="archives")
        self.assertIn("/plone/folder/doc -> subject already in subjects:'archives'", result)
        # path filter: nothing in another folder
        api.content.create(type="Folder", id="other", title="Other", container=self.portal)
        self.assertIn("Count of objects:0", add_subject(path="other", type="Document", subject="archives"))
        self.assert_denied(add_subject, MANAGER_ONLY)

    def test_creators(self):
        self.assertIn("!! value is mandatory", self.doc.cputils_creators())
        self.assertIn("!! value 'unknown' is not a user", self.doc.cputils_creators(value="unknown"))
        result = self.doc.cputils_creators(value="member")
        self.assertIn("New val set '['member']' for <a href='http://nohost/plone/folder/doc'>My doc</a>", result)
        self.assertEqual(self.doc.listCreators(), ("admin",))
        self.doc.cputils_creators(value="member", dochange="1")
        self.assertEqual(self.doc.listCreators(), ("member",))
        self.assertIn("Old val kept", self.doc.cputils_creators(value="member"))
        # insertion in the existing list
        self.doc.cputils_creators(value=TEST_USER_ID, replace="", add="0", dochange="1")
        self.assertEqual(self.doc.listCreators(), (TEST_USER_ID, "member"))
        # recursively: the folder and its document
        result = self.folder.cputils_creators(value="member", recursive="1", dochange="1")
        self.assertEqual(result.count("New val set"), 2)
        self.assertEqual(self.folder.listCreators(), ("member",))
        self.assertEqual(self.doc.listCreators(), ("member",))
        self.assertEqual(api.content.find(UID=self.doc.UID())[0].Creator, "member")
        self.assert_denied(self.doc.cputils_creators, MANAGER_ONLY, value="member")

    def test_del_object(self):
        result = self.doc.cputils_del_object()
        self.assertIn(
            '<span>/plone/folder/doc</span>, <a href="http://nohost/plone/folder/doc/view">My doc</a>', result
        )
        self.assertIn("doc", self.folder.objectIds())
        self.doc.cputils_del_object(doit="1")
        self.assertNotIn("doc", self.folder.objectIds())
        # non-empty folder (Plone 4 bug: KeyError, nothing deleted)
        api.content.create(type="Document", id="doc2", title="Other doc", container=self.folder)
        self.assertIn("<span>/plone/folder/doc2</span>", self.folder.cputils_del_object(doit="1"))
        self.assertNotIn("folder", self.portal.objectIds())
        self.assert_denied(self.folder.cputils_del_object, ZOPE_ADMIN_ONLY, doit="1")

    def test_del_objects(self):
        api.content.create(type="Folder", id="sub", title="Sub", container=self.folder)
        result = self.folder.cputils_del_objects(types="Document")
        self.assertIn("Types: ['Document']", result)
        self.assertIn("Link integrity: True", result)
        self.assertIn("Apply: ", result)
        self.assertIn('<a href="http://nohost/plone/folder/doc">/plone/folder/doc &nbsp;=>&nbsp; "My doc"</a>', result)
        self.assertNotIn("/plone/folder/sub", result)
        self.assertEqual(sorted(self.folder.objectIds()), ["doc", "sub"])
        result = self.folder.cputils_del_objects(types="Document", linki="0", doit="1")
        self.assertIn("Link integrity: False", result)
        self.assertEqual(self.folder.objectIds(), ["sub"])
        self.assert_denied(self.folder.cputils_del_objects, ZOPE_ADMIN_ONLY, types="Folder", doit="1")

    def test_set_attr(self):
        set_attr = self.doc.cputils_set_attr
        self.assertIn("attr parameter is mandatory !", set_attr())
        self.assertIn("Attr 'unknown' doesn't exist !", set_attr(attr="unknown"))
        result = set_attr(attr="creation_date")
        self.assertIn("Current value type=", result)
        self.assertIn("value parameter is mandatory !", result)
        self.assertIn("Given typ 'float' not in good types !", set_attr(attr="creation_date", value="1", typ="float"))
        self.assertIn("Cannot cast value type to 'int'", set_attr(attr="creation_date", value="abc", typ="int"))
        old = self.doc.creation_date
        result = set_attr(attr="creation_date", value="2017-10-13 9:00 GMT+1", typ="DateTime")
        self.assertIn("Attr 'creation_date' set to '2017/10/13 09:00:00 GMT+1' (from '%s')" % old, result)
        self.assertEqual(self.doc.creation_date, DateTime("2017-10-13 9:00 GMT+1"))
        self.assertEqual(api.content.find(UID=self.doc.UID())[0].created, DateTime("2017-10-13 9:00 GMT+1"))
        set_attr(attr="title", value="New title")
        self.assertEqual(self.doc.title, "New title")
        set_attr(attr="title", value="None", typ="None")
        self.assertIsNone(self.doc.title)
        self.assert_denied(set_attr, ZOPE_ADMIN_ONLY, attr="title", value="x")

    def test_uid(self):
        self.assertEqual(self.doc.cputils_uid(), self.doc.UID())
        self.assert_denied(self.doc.cputils_uid, MANAGER_ONLY)

    def test_obj_from_uid(self):
        obj_from_uid = self.portal.cputils_obj_from_uid
        self.assertEqual(obj_from_uid(), "uid parameter is mandatory !")
        self.assertEqual(obj_from_uid(uid="unknown"), "No object found for uid 'unknown'")
        self.assertEqual(obj_from_uid(uid=self.doc.UID()), '<a href="http://nohost/plone/folder/doc/view">My doc</a>')
        self.assert_denied(obj_from_uid, ZOPE_ADMIN_ONLY, uid=self.doc.UID())

    def test_move_copy_objects(self):
        api.content.create(type="Document", id="doc2", title="Other doc", container=self.folder)
        api.content.create(type="Folder", id="sub", title="Sub", container=self.folder)
        archives = api.content.create(type="Folder", id="archives", title="Archives", container=self.portal)
        transaction.savepoint(optimistic=True)  # cut/copy needs persisted objects
        move = self.folder.cputils_move_copy_objects
        self.assertIn("!! You must give the dest path", move())
        self.assertIn("!! The dest path 'nowhere' isn't correct", move(dest="nowhere"))
        self.assertIn("isn't folderish", move(dest="folder/doc"))
        result = move(dest="archives", types="Document")
        self.assertIn("Existing types: Document", result)
        self.assertIn("Will move: doc, doc2", result)
        self.assertEqual(archives.objectIds(), [])
        move(dest="/archives", types="Document", doit="1")
        self.assertEqual(archives.objectIds(), ["doc", "doc2"])
        self.assertEqual(self.folder.objectIds(), ["sub"])
        result = archives.cputils_move_copy_objects(action="copy", dest="folder/sub", doit="1")
        self.assertIn("Will copy: doc, doc2", result)
        self.assertEqual(archives.objectIds(), ["doc", "doc2"])
        self.assertEqual(self.folder.sub.objectIds(), ["doc", "doc2"])
        self.assert_denied(move, MANAGER_ONLY, dest="archives")

    def test_move_item(self):
        api.content.create(type="Document", id="doc2", title="Other doc", container=self.folder)
        api.content.create(type="Document", id="doc3", title="Third doc", container=self.folder)
        self.assertIsNone(self.folder.doc3.cputils_move_item())
        self.assertEqual(self.folder.objectIds(), ["doc", "doc3", "doc2"])
        self.folder.doc.cputils_move_item(delta="2")
        self.assertEqual(self.folder.objectIds(), ["doc3", "doc2", "doc"])
        self.assert_denied(self.folder.doc.cputils_move_item, MANAGER_ONLY)

    def test_order_folder(self):
        self.doc.setTitle("B doc")
        api.content.create(type="Document", id="doc2", title="C doc", container=self.folder)
        api.content.create(type="Document", id="doc3", title="A doc", container=self.folder)
        result = self.folder.cputils_order_folder(verbose="1")
        self.assertIn("Re-ordered by 'title' in normal order", result)
        self.assertEqual(self.folder.objectIds(), ["doc3", "doc", "doc2"])
        result = self.folder.cputils_order_folder(reverse="1", verbose="1")
        self.assertIn("Re-ordered by 'title' in reverse order", result)
        self.assertEqual(self.folder.objectIds(), ["doc2", "doc", "doc3"])
        # not verbose: redirect to the folder
        self.folder.cputils_order_folder(key="id")
        self.assertEqual(self.folder.objectIds(), ["doc", "doc2", "doc3"])
        self.assertEqual(self.request.RESPONSE.getHeader("location"), "http://nohost/plone/folder")
        self.assert_denied(self.folder.cputils_order_folder, MANAGER_ONLY)

    def test_list_objects(self):
        self.assertEqual(
            self.portal.cputils_list_objects("Document"),
            "<a href=  http://nohost/plone/folder/doc > http://nohost/plone/folder/doc </a> "
            "&nbsp;<a href= http://nohost/plone/folder/doc/cputils_object_info>(more info)</a>",
        )
        self.assertEqual(self.portal.cputils_list_objects("News Item"), "")
        self.assert_denied(self.portal.cputils_list_objects, MANAGER_ONLY, "Document")

    def test_objects_stats(self):
        api.content.create(type="Document", id="doc2", title="Other doc", container=self.folder)
        result = self.portal.cputils_objects_stats()
        self.assertIn(
            'Document: 2, 0.0M (<a href="http://nohost/plone/cputils_list_objects?type=Document">+</a>)', result
        )
        self.assertIn("Folder: 1, ", result)
        lines = self.portal.cputils_objects_stats(csv="1").split("\n")
        self.assertEqual(lines[0], "Type\tNumber\tSize (Mb)")
        self.assertIn("Document\t2\t0,0", lines)
        self.assert_denied(self.portal.cputils_objects_stats, MANAGER_ONLY)

    def test_list_local_roles(self):
        self.assertEqual(self.portal.cputils_list_local_roles(), "<h1>List of defined local roles</h1>")
        api.user.grant_roles(username="member", obj=self.folder, roles=["Editor"])
        self.doc.__ac_local_roles_block__ = True
        self.doc.reindexObjectSecurity()
        lines = self.portal.cputils_list_local_roles().split("<br />\n")
        self.assertEqual(
            lines[1:],
            [
                '<a href="http://nohost/plone/folder/@@sharing">/folder</a> :  ',
                ".. user 'member' => Editor",
                '<a href="http://nohost/plone/folder/doc/@@sharing">/folder/doc</a> : '
                '<span style="color:red">acquisition disabled !</span>',
            ],
        )
        self.assert_denied(self.portal.cputils_list_local_roles, MANAGER_ONLY)

    def test_unlock_webdav_objects(self):
        result = self.folder.cputils_unlock_webdav_objects()
        self.assertTrue(result.endswith("<h1>Locked objects in '/plone/folder'</h1>"))
        ILockable(self.doc).lock()
        self.assertTrue(self.doc.wl_isLocked())
        result = self.portal.cputils_unlock_webdav_objects()
        self.assertIn("http://nohost/plone/folder/doc is locked", result)
        self.assertTrue(self.doc.wl_isLocked())
        result = self.doc.cputils_unlock_webdav_objects(dochange="1")
        self.assertIn("http://nohost/plone/folder/doc is locked", result)
        self.assertNotIn("ERROR", result)
        self.assertFalse(self.doc.wl_isLocked())
        self.assert_denied(self.portal.cputils_unlock_webdav_objects, MANAGER_ONLY)

    def test_relation_infos(self):
        doc2 = api.content.create(type="Document", id="doc2", title="Other doc", container=self.folder)
        rel = self.relate(self.doc, doc2)
        intids = getUtility(IIntIds)
        infos = utils.relation_infos(rel)
        self.assertFalse(infos["br"])
        self.assertEqual(infos["fr_i"], intids.getId(self.doc))
        self.assertEqual(infos["fr_o"], self.doc)
        self.assertEqual(infos["fr_a"], "relatedItems")
        self.assertEqual(infos["fr_p"], "/plone/folder/doc")
        self.assertEqual(infos["to_i"], intids.getId(doc2))
        self.assertEqual(infos["to_o"], doc2)
        self.assertEqual(infos["to_p"], "/plone/folder/doc2")

    def test_check_relations(self):
        doc2 = api.content.create(type="Document", id="doc2", title="Other doc", container=self.folder)
        self.relate(self.doc, doc2)
        self.assertEqual(utils.check_relations(self.portal), "check_intids\n\nNo problem found")
        getUtility(IIntIds).unregister(doc2)
        result = utils.check_relations(self.portal)
        self.assertIn("Missing to_id {", result)
        self.assertIn("'fr_p': '/plone/folder/doc'", result)
        self.assert_denied(utils.check_relations, ZOPE_ADMIN_ONLY, self.portal)

    def test_show_object_relations(self):
        self.assertEqual(self.doc.cputils_show_object_relations(), "Way = from\nWay = to")
        doc2 = api.content.create(type="Document", id="doc2", title="Other doc", container=self.folder)
        self.relate(self.doc, doc2)
        lines = self.doc.cputils_show_object_relations().split("\n")
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[2], "Way = to")
        self.assertIn("'to_p': '/plone/folder/doc2'", lines[1])
        lines = doc2.cputils_show_object_relations().split("\n")
        self.assertEqual(lines[:2], ["Way = from", "Way = to"])
        self.assertIn("'fr_p': '/plone/folder/doc'", lines[2])
        self.assert_denied(self.doc.cputils_show_object_relations, ZOPE_ADMIN_ONLY)

    def test_list_used_views(self):
        self.assertIn("Document : document_view (1)", self.portal.cputils_list_used_views())
        result = self.portal.cputils_list_used_views(specific_view="document_view")
        self.assertIn("<html><b><u>Objects using the 'document_view' layout</u></b><br /><br />", result)
        self.assertIn("Document : <a href='http://nohost/plone/folder/doc'>/plone/folder/doc</a>", result)
        self.assertTrue(result.endswith("</html>"))
        self.assert_denied(self.portal.cputils_list_used_views, MANAGER_ONLY)

    def test_list_portlets(self):
        # no portlet ever assigned on the context: KeyError
        self.assertRaises(KeyError, self.folder.cputils_list_portlets)
        self.add_portlet(self.folder)
        lines = self.folder.cputils_list_portlets().split("\n")
        self.assertTrue(lines[0].startswith("left: {'navigation': <"))
        self.assertEqual(lines[1], "right: {}")
        self.assert_denied(self.folder.cputils_list_portlets, "checkInstance run with a non admin user: we go out")

    def test_list_context_portlets_by_name(self):
        by_name = self.portal.cputils_list_context_portlets_by_name
        self.assertTrue(by_name().startswith("You MUST provide a portlet_name to query for."))
        self.assertEqual(by_name(portlet_name="unknown"), 'Nothing found with search parameter "unknown"')
        self.add_portlet(self.folder, column="plone.rightcolumn")
        result = by_name(portlet_name="navigation")
        self.assertIn(
            '<td width=50%>right_column</td><td width=50%><a href="http://nohost/plone/folder">'
            "http://nohost/plone/folder</a></td></tr>",
            result,
        )
        self.assertNotIn('<a href="http://nohost/plone/folder/doc">', result)
        self.assertIn(
            '<td width=20%>right_column</td><td width=60%><a href="http://nohost/plone/folder">'
            "http://nohost/plone/folder</a></td><td width=20%>navigation</td></tr>",
            by_name(portlet_name="*"),
        )
        self.assert_denied(by_name, ZOPE_ADMIN_ONLY, portlet_name="*")

    def test_remove_dependency_step(self):
        result = utils.remove_dependency_step(self.portal, step="import-relations-utils", dependency="toolset")
        self.assertIn("<br /><b>Available steps in 'getImportStepRegistry'</b>", result)
        self.assertIn("<br /><b>Available steps in '_import_step_registry'</b>", result)
        self.assertIn("<b>Available dependencies</b> for import-relations-utils: [", result)
        self.assertIn("<b>New dependencies</b>: []", result)
        self.assertNotIn("<b>New value applied</b>", result)
        self.assert_denied(utils.remove_dependency_step, MANAGER_ONLY, self.portal)

    def test_unregister_adapter(self):
        self.assertIn("plone.leftcolumn", utils.unregister_adapter(self.portal).split("\n"))
        sm = getSiteManager(self.portal)
        sm.registerAdapter(LeftoverAdapter, (Interface,), ILeftover, name="leftover")
        self.assertIn("leftover", utils.unregister_adapter(self.portal).split("\n"))
        result = utils.unregister_adapter(self.portal, unregister="leftover")
        self.assertIn("Adapter 'leftover' unregistered", result)
        self.assertNotIn("leftover", [reg.name for reg in sm.registeredAdapters()])
        result = utils.unregister_adapter(self.portal, unregister="leftover")
        self.assertIn("Adapter 'leftover' not unregistered : list index out of range", result)
        self.assert_denied(utils.unregister_adapter, ZOPE_ADMIN_ONLY, self.portal)

    def test_change_uuid(self):
        old_uid = self.doc.UID()
        result = utils.change_uuid(self.doc)
        self.assertIn("/plone/folder/doc, old='%s', new='" % old_uid, result)
        self.assertEqual(self.doc.UID(), old_uid)
        utils.change_uuid(self.doc, dochange="1")
        new_uid = self.doc.UID()
        self.assertNotEqual(new_uid, old_uid)
        self.assertEqual(api.content.find(UID=new_uid)[0].getPath(), "/plone/folder/doc")
        self.assertEqual(len(api.content.find(UID=old_uid)), 0)
        # recursively: the folder and its document
        result = utils.change_uuid(self.folder, recursive="1")
        self.assertIn("/plone/folder, old='%s'" % self.folder.UID(), result)
        self.assertIn("/plone/folder/doc, old='%s'" % new_uid, result)
        self.assert_denied(utils.change_uuid, MANAGER_ONLY, self.doc)

    def test_correct_intids(self):
        result = utils.correct_intids(self.portal)
        values = dict(part.split("=") for part in result.split(", "))
        self.assertEqual(values["errors"], "0")
        self.assertEqual(values["ids bef"], values["ids aft"])
        self.assertEqual(values["refs bef"], values["walked"])
        self.assert_denied(utils.correct_intids, ZOPE_ADMIN_ONLY, self.portal)

    def test_register_intid(self):
        intids = getUtility(IIntIds)
        self.assertEqual(
            utils.register_intid(self.doc),
            "Check intid registration for 'http://nohost/plone/folder/doc'\n<br />"
            "obj already registered with intid '%s'" % intids.getId(self.doc),
        )
        intids.unregister(self.doc)
        self.assertIn("!! Missing intid !!", utils.register_intid(self.doc))
        self.assertIsNone(intids.queryId(self.doc))
        result = utils.register_intid(self.doc, dochange="1")
        self.assertIn("obj now registered with intid '%s'" % intids.getId(self.doc), result)
        self.assert_denied(utils.register_intid, ZOPE_ADMIN_ONLY, self.doc)

    def test_check_all_catalog_intids(self):
        intids = getUtility(IIntIds)
        intids.unregister(self.doc)
        result = utils.check_all_catalog_intids(self.portal)
        self.assertIn("number of missing intid : 1;", result)
        self.assertIn("portal_types : ['Document']", result)
        self.assertIn(
            "!! Missing intid !! portal_type : Document, absolute_url : http://nohost/plone/folder/doc", result
        )
        self.assertIn("obj already registered with intid %s" % intids.getId(self.folder), result)
        self.assertIsNone(intids.queryId(self.doc))
        result = utils.check_all_catalog_intids(self.portal, dochange="1")
        self.assertIn("obj now registered with intid '%s'" % intids.getId(self.doc), result)
        self.assertIn("number of missing intid : 0;", utils.check_all_catalog_intids(self.portal))
        self.assert_denied(utils.check_all_catalog_intids, ZOPE_ADMIN_ONLY, self.portal)

    def test_load_site(self):
        self.assertIsNone(utils.load_site(self.portal, duration="0"))
        self.assert_denied(utils.load_site, ZOPE_ADMIN_ONLY, self.portal)


class TestContentCommit(ContentTestCase):
    """External methods committing the transaction themselves."""

    layer = CONTENT_FUNCTIONAL

    def test_removeStep(self):
        result = self.portal.cputils_removeStep(step="installCPUtils")
        before, after = result.split("after delete")
        self.assertIn("installCPUtils", before)
        self.assertNotIn("installCPUtils", after)
        setup = self.portal.portal_setup
        self.assertNotIn("installCPUtils", setup.getImportStepRegistry().listSteps())
        # saved (Plone 4 bug: lost when reloaded from the ZODB)
        setup._p_invalidate()
        self.assertNotIn("installCPUtils", setup.getImportStepRegistry().listSteps())
        self.assertIn("after delete", self.portal.cputils_removeStep(step="unknown"))
        self.assert_denied(self.portal.cputils_removeStep, MANAGER_ONLY, step="portal-transforms-various")

    def test_removeRegisteredTool(self):
        result = utils.removeRegisteredTool(self.portal, tool="portal_diff")
        before, after = result.split("after delete")
        self.assertIn("portal_diff", before)
        self.assertNotIn("portal_diff", after)
        setup = self.portal.portal_setup
        self.assertNotIn("portal_diff", setup.getToolsetRegistry().listRequiredTools())
        # saved (Plone 4 bug: lost when reloaded from the ZODB)
        setup._p_invalidate()
        self.assertNotIn("portal_diff", setup.getToolsetRegistry().listRequiredTools())
        self.assert_denied(utils.removeRegisteredTool, MANAGER_ONLY, self.portal, tool="portal_url")

    def test_clean_provides_for(self):
        name = ILeftover.__identifier__
        clean = self.portal.cputils_clean_provides_for
        self.assertTrue(clean().startswith("You must provide an interface_name argument"))
        self.assertEqual(clean(interface_name=name), "No elements provides '%s'" % name)
        alsoProvides(self.doc, ILeftover)
        self.doc.reindexObject(idxs=["object_provides"])
        self.assertEqual(
            clean(interface_name=name),
            "Following object no longer provides '%s' interface :\n\nhttp://nohost/plone/folder/doc" % name,
        )
        self.assertFalse(ILeftover.providedBy(self.doc))
        self.assertEqual(len(api.content.find(object_provides=name)), 0)
        self.assert_denied(clean, MANAGER_ONLY, interface_name=name)

    def test_clean_utilities_for(self):
        name = ILeftover.__identifier__
        clean = self.portal.cputils_clean_utilities_for
        self.assertTrue(clean().startswith("You must provide an interface_name argument"))
        self.assertEqual(
            clean(interface_name=name), "Interface not found in adapters\nInterface not found in subscribers"
        )
        self.assert_denied(clean, MANAGER_ONLY, interface_name=name)
        sm = getSiteManager(self.portal)
        sm.registerUtility(LeftoverUtility(), ILeftover)
        transaction.commit()
        self.assertEqual(clean(interface_name=name), "Corrected adapters\nCorrected subscribers")
        self.assertNotIn(ILeftover, sm.utilities._adapters[0])
        # saved (Plone 4 bug: lost when reloaded from the ZODB)
        sm.utilities._p_invalidate()
        self.assertNotIn(ILeftover, sm.utilities._adapters[0])

    def test_remove_empty_related_items(self):
        doc2 = api.content.create(type="Document", id="doc2", title="Other doc", container=self.folder)
        doc3 = api.content.create(type="Document", id="doc3", title="Third doc", container=self.folder)
        self.doc.relatedItems = [self.relate(self.doc, doc2), self.relate(self.doc, doc3)]
        api.content.delete(obj=doc2, check_linkintegrity=False)
        self.assertEqual([rel.isBroken() for rel in self.doc.relatedItems], [True, False])
        self.assertEqual(utils.remove_empty_related_items(self.doc), "This object has now 1 related items (before: 2")
        self.assertEqual([rel.to_object for rel in self.doc.relatedItems], [doc3])
        self.assert_denied(utils.remove_empty_related_items, ZOPE_ADMIN_ONLY, self.doc)

