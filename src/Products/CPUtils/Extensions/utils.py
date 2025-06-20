# -*- coding: utf-8 -*-
# utilities

from imio.helpers.security import check_zope_admin
from imio.pyutils.utils import safe_encode
from plone.app.uuid.utils import uuidToObject
from plone.registry.interfaces import IRegistry
from zope.component import getUtility


def get_users(self, obj=True):
    from Products.CMFCore.utils import getToolByName

    portal = getToolByName(self, "portal_url").getPortalObject()
    users = []
    for user in portal.acl_users.searchUsers():
        if user["pluginid"] == "source_users":
            if obj:
                users.append(portal.portal_membership.getMemberById(user["userid"]))
            else:
                users.append(user["userid"])
    return users


def check_role(self, role="Manager", context=None):
    from Products.CMFCore.utils import getToolByName

    pms = getToolByName(self, "portal_membership")
    return pms.getAuthenticatedMember().has_role(role, context)


def fileSize(nb, as_size="", decimal="", rm_sz=False):
    """
        Convert bytes nb in formatted string.
        as_size : force size k, M, G or T
        decimal : replace . decimal by given one
        rm_sz : remove letter size
    """
    sizeletter = {1: "k", 2: "M", 3: "G", 4: "T"}
    if as_size and as_size not in sizeletter.values():
        as_size = ""
    if rm_sz and not as_size:
        rm_sz = False
    for x in range(1, 4):
        quot = nb // 1024 ** x
        if as_size == sizeletter[x] or (not as_size and quot < 1024):
            break
    res = "%.1f%s" % (float(nb) / 1024 ** x, (not rm_sz and sizeletter[x] or ""))
    if decimal:
        return res.replace(".", decimal)
    return res


def tobytes(objsize):
    """ Transform getObjSize metadata to bytes value """
    from Missing import Value

    if objsize is Value:
        return "No object size in catalog"
    parts = objsize.split()
    if len(parts) != 2:
        return "Problem when splitting '%s' obj size in 2 parts" % objsize
    try:
        lfsize = float(parts[0])
    except Exception:
        return "First part '%s' of objsize '%s' isn't float" % (parts[0], objsize)
    if parts[1] == "KB":
        return lfsize * 1024
    elif parts[1] == "MB":
        return lfsize * 1024 ** 2
    else:
        return parts


def get_all_site_objects(self):
    allSiteObj = []
    for objid in self.objectIds(("Plone Site", "Folder")):
        obj = getattr(self, objid)
        if obj.meta_type == "Folder":
            for sobjid in obj.objectIds("Plone Site"):
                sobj = getattr(obj, sobjid)
                allSiteObj.append(sobj)
        elif obj.meta_type == "Plone Site":
            allSiteObj.append(obj)
    return allSiteObj


def sendmail(self, mfrom="", to="", body="", subject="", cc="", bcc=""):
    """
        send a mail
    """
    from email.Header import Header
    from Products.CMFCore.utils import getToolByName
    from Products.CMFPlone.utils import safe_unicode
    from Products.CPUtils.config import PLONE_VERSION

    import email.Message
    import email.Utils

    portal = getToolByName(self, "portal_url").getPortalObject()

    mailMsg = email.Message.Message()
    mailMsg["To"] = to
    mailMsg["From"] = mfrom
    mailMsg["CC"] = cc
    mailMsg["BCC"] = bcc
    mailMsg["Subject"] = str(Header(safe_unicode(subject), "utf-8"))
    mailMsg["Date"] = email.Utils.formatdate(localtime=1)
    mailMsg["Message-ID"] = email.Utils.make_msgid()
    mailMsg["Mime-version"] = "1.0"
    mailMsg["Content-type"] = "text/plain"
    mailMsg.set_payload(safe_unicode(body).encode("utf-8"), "utf-8")
    mailMsg.epilogue = "\n"  # To ensure that message ends with newline
    mail_host = getattr(portal, "MailHost", None)
    try:
        if PLONE_VERSION.startswith("4."):
            return mail_host.send(mailMsg, mto=to, mfrom=mfrom, subject=subject)
        else:
            return mail_host.secureSend(mailMsg, to, mfrom, subject=subject)
    except Exception, msg:
        return msg


def log_list(lst, line, logger=None, level="info"):
    levels = {"info": ">>", "warn": "??", "error": "!!"}
    if logger:
        getattr(logger, level)(line)
    else:
        print "%s %s" % (levels[level], line)
    lst.append(line)


def object_link(obj, view="view", attribute="Title", content="", target=""):
    """ Returns an html link for the given object """
    from Products.CMFPlone.utils import safe_unicode

    href = view and "%s/%s" % (obj.absolute_url(), view) or obj.absolute_url()
    if not content:
        if not hasattr(obj, attribute):
            attribute = "Title"
        content = getattr(obj, attribute)
        if callable(content):
            content = content()
    if target:
        target = ' target="{}"'.format(target)
    return u'<a href="%s"%s>%s</a>' % (href, target, safe_unicode(content))


def install(self):
    """
        Install cputils methods where the user is (root of zope?)
    """
    from Products.CMFPlone.utils import base_hasattr
    from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod

    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    methods = []
    for method in (
        "add_subject",
        "audit_catalog",
        "change_authentication_plugins",
        "change_user_properties",
        "check_groups_users",
        "check_users",
        "clean_provides_for",
        "clean_utilities_for",
        "configure_ckeditor",
        "copy_image_attribute",
        "cpdb",
        "creators",
        "del_bad_portlet",
        "del_object",
        "del_objects",
        "desactivate_base2dom",
        "export_subscribers_csv",
        "install_plone_product",
        "list_context_portlets_by_name",
        "list_local_roles",
        "list_newsletter_users",
        "list_objects",
        "list_portlets",
        "list_used_views",
        "list_users",
        "load_user_properties",
        "move_copy_objects",
        "move_item",
        "obj_from_uid",
        "object_info",
        "objects_stats",
        "order_folder",
        "recreate_users_groups",
        "reftooltoobjects",
        "removeStep",
        "rename_long_ids",
        "resources_order",
        "send_adminMail",
        "set_attr",
        "show_object_relations",
        "store_user_properties",
        "sync_properties",
        "uid",
        "unlock_webdav_objects",
        "zmi",
    ):
        method_name = "cputils_" + method
        if not base_hasattr(self, method_name):
            manage_addExternalMethod(self, method_name, "", "CPUtils.utils", method)
            methods.append(method_name)
    return "<div>Those methods have been added: %s</div>" % ("<br />".join(methods))


def pack_db(self, days=0):
    """
        pack a db of the zope instance
    """
    out = []
    # The user running this via urllib is not manager !!!!
    #    if not check_role(self):
    #        return "You must have a manager role to run this script"
    import time

    t = time.time() - days * 86400
    db = self._p_jar.db()
    sz_bef = db.getSize()
    t = db.pack(t)
    sz_aft = db.getSize()
    out.append("Size %s => %s" % (fileSize(sz_bef), fileSize(sz_aft)))
    out.append("well packed")
    return ", ".join(out)


def cpdb(self):
    """
        run pdb on current context
    """
    if not check_zope_admin():
        return "You must have a zope manager to run this script"
    import pdb

    pdb.set_trace()


def object_info(self):
    """
        return various information on the current object
    """
    #    if not check_role(self):
    #        return "You must have a manager role to run this script"
    out = []
    from Products.CMFCore.utils import getToolByName
    from Products.CMFCore.WorkflowCore import WorkflowException

    try:
        purl = getToolByName(self, "portal_url")
        wtool = getToolByName(self, "portal_workflow")
        putils = getToolByName(self, "plone_utils")
        #        out.append("portal path='%s'" % purl.getPortalPath())
        out.append(
            "current object path='/%s'" % "/".join(purl.getRelativeContentPath(self))
        )
        out.append("current object id='%s'" % self.getId())
        out.append("current object UID='%s'" % self.UID())
        out.append("current object externalIdentifier='%s'" % getattr(self, 'externalIdentifier', ''))
        out.append(
            "current object portal_type/meta_type/class='%s'/'%s'/'%s'"
            % (self.getPortalTypeName(), self.meta_type, self.__class__.__name__)
        )
        out.append("is folderish='%s'" % self.isPrincipiaFolderish)
        out.append("creator='%s'" % self.Creator())
        workflow = False
        try:
            workflows = [wfw.getId() for wfw in wtool.getWorkflowsFor(self)]
            state = wtool.getInfoFor(self, "review_state")
            transitions = ";".join(
                [trans["name"] for trans in wtool.getTransitionsFor(self)]
            )
            workflow = True
        except WorkflowException:
            workflows = ["-"]
            state = "-"
            transitions = "-"
        out.append("\nAbout workflows:")
        out.append("> workflows='%s'" % ";".join(workflows))
        out.append("> state='%s'" % state)
        out.append("> transitions='%s'" % transitions)
        if workflow:
            for wfid in workflows:
                out.append(
                    "> Permissions info for state '%s' in workflow '%s'" % (state, wfid)
                )
                wf = wtool.getWorkflowById(wfid)
                if hasattr(wf.states, state):
                    st = getattr(wf.states, state)
                    permissions = st.getManagedPermissions()
                    if permissions:
                        for permission in permissions:
                            dic = st.getPermissionInfo(permission)
                            out.append(
                                "\t'%s' for '%s', acquired=%s"
                                % (permission, ", ".join(dic["roles"]), dic["acquired"])
                            )
                    else:
                        out.append("\tno permissions redefined on this state !")
        out.append("\nAbout local roles:")
        out.append("> acquisition set='%s'" % putils.isLocalRoleAcquired(self))
        localroles = self.get_local_roles()
        if len(localroles):
            out.append("> local roles :")
        else:
            out.append("> local roles : Nothing defined !")
        for principalId, lr in localroles:
            out.append("\t'%s' has roles '%s'" % (principalId, ";".join(lr)))
        inhlocalroles = putils.getInheritedLocalRoles(self)
        if len(inhlocalroles) and putils.isLocalRoleAcquired(self):
            out.append("> inherited local roles :")
            for principalId, lr, pType, pId in inhlocalroles:
                out.append(
                    "\t%s '%s' has roles '%s'" % (pType, principalId, ";".join(lr))
                )
        else:
            out.append("> inherited local roles : none !")
    except Exception, msg:
        out.append("! EXCEPTION !:%s" % msg)
    return "\n".join(out)


def audit_catalog(self):
    from Products.CMFCore.utils import getToolByName

    if not check_role(self):
        return "You must have a manager role to run this script"

    portal_url = getToolByName(self, "portal_url")
    portal = portal_url.getPortalObject()

    kw = {}
    # kw['portal_type'] = ('Document','Link','Image','File','Folder','Large Plone Folder','Wrapper','Topic')
    # kw['review_state'] = ('private',) #'published'
    # kw['path'] = '/' # '/'.join(context.getPhysicalPath())
    # kw['sort_on'] = 'created'
    # kw['sort_order'] = 'reverse'

    results = portal.portal_catalog.searchResults(kw)

    header = (
        "<h1>RESULTATS DE LA RECHERCHE</h1> <p>Recherche dans : %s</p> <p>Nombre d'elements trouves : %d </p>"
        % ("/", len(results))
    )
    out = [header]

    res = []
    out.append("""counter : %s : %s : %s""" % ("portal_type", "getObjSize", "url"))
    for result in results:
        res.append(
            (
                result.portal_type,
                result.getObjSize,
                result.getURL() + "/view",
                tobytes(result.getObjSize),
            )
        )

    def sortBySize(row1, row2):
        size1 = row1[-1]
        size2 = row2[-1]
        # reverse order
        return cmp(size1, size2)

    res.sort(sortBySize, reverse=True)

    count = 0
    for row in res:
        (ptype, size, url, bytes) = row
        count += 1
        out.append(
            """%d : %s : %s : <a href="%s">%s</a>""" % (count, ptype, size, url, url)
        )

    out.append("<br />FIN")
    return "<br />".join(out)


def delete_subscribers(self, delete=False):
    """
        delete inactive subscribers (maybe robots) of PloneGazette.
        script to be run on the subscriber's folder context
    """
    if not check_role(self):
        return "You must have a manager role to run this script"
    ids = []
    out = ["<h1>Inactive subscribers</h1>"]
    for obj in self.objectValues():
        if obj.meta_type == "Subscriber" and not obj.active:
            out.append(obj.Title())
            ids.append(obj.getId())
    if delete:
        self.manage_delObjects(ids)
    return "<br />".join(out)


def export_subscribers_csv(self):
    """
        Export in csv all subscribers for a NewsLetter Theme
        script to be run on the subscriber's folder context
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    out = ['"email","active","format"']

    for obj in self.objectValues():
        if obj.meta_type != "Subscriber":
            continue
        try:
            ligne = '"%s","%s","%s"' % (
                obj.Title().encode("utf8"),
                obj.active and "1" or "0",
                obj.format.encode("utf8"),
            )
            out.append(ligne)
        except BaseException:
            continue
    return "\n".join(out)


def delete_users(self, delete=False):
    """
        delete users added by robots.
    """
    if not check_role(self):
        return "You must have a manager role to run this script"
    from Products.CMFCore.utils import getToolByName

    portal = getToolByName(self, "portal_url").getPortalObject()
    out = ["<h1>all Users</h1>"]
    i = 0
    for member in get_users(self):
        i += 1
        #  if i >100:
        #    break
        u_id = member.id
        email = member.getProperty("email")
        if email.endswith(".com") and not (
            email.endswith("gmail.com") or email.endswith("hotmail.com")
        ):
            out.append("<span>%s, %s, deleted</span>" % (u_id, email))
            if delete:
                portal.portal_membership.deleteMembers(
                    [u_id], delete_memberareas=1, delete_localroles=0
                )
        else:
            out.append("<span>%s, %s, kept</span>" % (u_id, email))
    return "<br/>".join(out)


def change_user_properties(self, kw="", dochange="", filter=""):
    """
        change user properties with parameter like
        kw=wysiwyg_editor:FCKeditor|nationalregister=00000000097
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    def return_properties(dic, member):
        ret = ""
        for key in dic.keys():
            if member.hasProperty(key):
                ret += "%s='%s'," % (key, member.getProperty(key))
            else:
                ret += "%s not found," % (key)
        return ret

    from Products.CMFCore.utils import getToolByName

    portal = getToolByName(self, "portal_url").getPortalObject()
    out = []
    #    if not kw:
    # out.append("available properties:%s" % portal.portal_memberdata.propertyItems())
    out.append("call the script followed by needed parameters:")
    out.append("-> kw=propertyname1:value1|propertyname2:value2")
    out.append(
        "-> filter=propertyname1:value1  or  filter=userid:xxx  or  filter=userid:xxx|propertyname1:value1"
    )
    out.append("-> dochange=1")
    out.append(
        "by example ...?kw=wysiwyg_editor:FCKeditor|nationalregister=00000000097&"
        "filter=userid:quidam&dochange=1<br/>"
    )

    out.append("given keyword parameters:%s" % kw)

    def returnKeywordParamsAsDic(dico, param):
        for tup in param.split("|"):
            keyvalue = tup.split(":")
            if len(keyvalue) == 2:
                (key, value) = keyvalue
                if value == "True":
                    value = True
                elif value == "False":
                    value = False
                dico[key] = value
            elif tup:
                out.append("problem in param '%s'" % tup)

    dic = {}
    returnKeywordParamsAsDic(dic, kw)
    out.append("New properties dictionary=%s<br/>" % dic)

    screen = {}
    returnKeywordParamsAsDic(screen, filter)
    out.append("Filtering properties dictionary=%s<br/>" % screen)
    userscreen = screen.pop("userid", "")

    out.append("<h2>Users</h2>")
    change_property = False
    if dochange not in ("", "0", "False", "false"):
        change_property = True
    newvaluestring = ",".join(["%s='%s'" % (key, dic[key]) for key in dic.keys()])
    total = filtered = 0
    for member in get_users(self):
        total += 1
        u_id = member.id
        if userscreen and u_id != userscreen:
            continue
        for propname in screen:
            # if user doesn't have the property or his property is different from the filtering value,
            # we continue with next user
            if (
                not member.hasProperty(propname)
                or member.getProperty(propname) != screen[propname]
            ):
                break  # do not continue in else clause
        else:
            filtered += 1
            out.append("<br/>USER:'%s'" % (u_id))
            # out.append("->  old properties=%s" % portal.portal_membership.getMemberInfo(memberId=u))
            # display not all properties
            out.append(
                "=>  all properties: %s"
                % return_properties(
                    dict(portal.portal_memberdata.propertyItems()), member
                )
            )
            if len(dic):
                out.append("->  old properties: %s" % return_properties(dic, member))
                if change_property:
                    member.setMemberProperties(dic)
                    out.append(
                        "->  new properties: %s" % return_properties(dic, member)
                    )
                else:
                    out.append("->  new values after change: %s" % newvaluestring)
    try:
        out[out.index("<h2>Users</h2>")] = "<h2>Users : total=%d, filtered=%d</h2>" % (
            total,
            filtered,
        )
    except BaseException:
        pass

    # in some case like using a LDAP, this will break
    # try in unicode, else pass...
    result = ""
    try:
        result = "<br/>".join(out)
    except BaseException:
        try:
            result = u"<br/>".join(out)
        except BaseException:
            pass
    return result


def store_user_properties(self):
    """
        store all user properties
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    out = []
    txt = []

    from Products.CMFCore.utils import getToolByName

    portal = getToolByName(self, "portal_url").getPortalObject()
    target_dir = portal

    if "users_properties" not in target_dir.objectIds():
        self.manage_addDTMLDocument(id="users_properties", title="All users properties")
        out.append(
            "Document '%s/users_properties' added"
            % "/".join(target_dir.getPhysicalPath())
        )

    properties_names = dict(portal.portal_memberdata.propertyItems()).keys()
    properties_names.sort()
    #    skipped_properties = ['description', ]
    #    properties_names = [name for name in properties_names if name not in skipped_properties]
    txt.append("Count\tUser\t" + "\t".join(properties_names))
    #    userids = [ud['userid'] for ud in get_users(self)]
    count = 1
    for member in get_users(self):
        user = member.id
        out.append("Current member '%s'" % (user))
        if member is None:
            out.append("! Member not found ")
            continue
        line = ["%03d" % count, user]
        for name in properties_names:
            if member.hasProperty(name):
                line.append(str(member.getProperty(name)).replace("\r\n", "|"))
            else:
                line.append("")
                out.append("!!! User '%s' hasn't property '%s'" % (user, name))
        txt.append("\t".join(line))
        count += 1
    doc = self.users_properties
    doc.raw = "\n".join(txt)
    out.append(
        "Document '%s/users_properties' updated !"
        % "/".join(target_dir.getPhysicalPath())
    )

    return "\n".join(out)


def load_user_properties(self, dochange=""):
    """
        load saved user properties
    """

    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    from Products.CMFCore.utils import getToolByName

    portal = getToolByName(self, "portal_url").getPortalObject()

    out = []
    if "oldacl" not in portal.objectIds():
        return (
            "First you must create a folder at Plonesite root named 'oldacl' and containing the imported "
            "'user_properties' DTMLDocument (created with external method 'store_user_properties')"
        )

    if "users_properties" not in portal.oldacl.objectIds():
        return (
            "You must import in the folder named '/oldacl' the DTMLDocument named 'user_properties'"
            "(created with external method 'store_user_properties')"
        )

    change_property = False
    if dochange not in ("", "0", "False", "false"):
        change_property = True

    if not change_property:
        out.append(
            "The following changes are not applied: you must run the script with the parameter '...?dochange=1'"
        )

    properties_names = dict(portal.portal_memberdata.propertyItems())
    skipped_properties = [
        "error_log_update",
        "ext_editor",
        "last_login_time",
        "listed",
        "login_time",
        "visible_ids",
        "wysiwyg_editor",
    ]

    doc = portal.oldacl.users_properties
    lines = doc.raw.splitlines()
    if not len(lines) > 1:
        return "No information found in document: content='%s'" % doc.raw
    columns = {}

    header_line = True
    for line in lines:
        infos = line.split("\t")
        user = infos[1]
        props = {}
        if header_line and user != "User":
            return "No header line in document: content='%s'" % doc.raw
        for i in range(2, len(infos)):
            property = infos[i]
            if not property:
                continue
            if header_line:
                if property in skipped_properties:
                    property = ""
                    # this column is made empty, this will not be used when reading value
                elif property not in properties_names:
                    out.append(
                        "Warning: old property '%s' not found in portal_memberdata properties"
                        % property
                    )
                    property = ""
                columns[i] = property
            elif columns[i]:
                props[columns[i]] = property.replace("|", "\r\n")

        if header_line:
            header_line = False
            continue

        count = int(infos[0])
        if props:
            out.append(
                "%03d, User '%s' has changed properties '%s'"
                % (count, user, str(props))
            )
            if change_property:
                member = portal.portal_membership.getMemberById(user)
                if member is None:
                    out.append("%03d, User '%s' not found !!" % (count, user))
                    continue
                member.setMemberProperties(props)
        else:
            out.append("%03d, User '%s' hasn't change in properties" % (count, user))
    return "\n".join(out)


def ploneboard_correct_modified(self, dochange=""):
    """
        This script corrects the modified date of conversations after a migration.
        The modified date becomes last modified comment.
        The portal_catalog must be updated !!
    """
    from Products.CMFCore.utils import getToolByName

    if not check_role(self):
        return "You must have a manager role to run this script"

    out = []
    if not dochange:
        # out.append("available properties:%s" % portal.portal_memberdata.propertyItems())
        out.append("To really change modification date, call the script with param:")
        out.append("-> dochange=1")
        out.append("by example ...?dochange=1\n")
        out.append("You must update the portal_catalog after running the script\n")

    portal_url = getToolByName(self, "portal_url")
    portal = portal_url.getPortalObject()

    kw = {}
    kw["portal_type"] = "PloneboardConversation"
    # kw['review_state'] = ('private',) #'published'
    # kw['path'] = '/' # '/'.join(context.getPhysicalPath())
    kw["sort_on"] = "created"
    # kw['sort_order'] = 'reverse'

    results = portal.portal_catalog.searchResults(kw)

    out.append("%d conversations found\n" % len(results))
    for r in results:
        conv = r.getObject()
        #        print "%s, %s, %s, %s" % (r.id, conv.Title(), r.created, r.modified)
        out.append("%s, %s, %s, %s" % (r.id, conv.Title(), r.created, r.modified))
        last_modification_date = None
        for com in conv.getComments():
            #            print "\t%s, %s, %s, %s" % (com.getId(), com.Title(), com.CreationDate(), com.ModificationDate())
            out.append("\t%s, %s, %s" % (com.getId(), com.Title(), com.CreationDate()))
            if dochange:
                com.setModificationDate(com.CreationDate())
                # com.reindexObject() #avoid
            # print "\t%s" % com.ModificationDate()
            last_modification_date = com.CreationDate()
        out.append("=> new modification date = %s" % last_modification_date)
        if dochange:
            conv.setModificationDate(last_modification_date)
            # conv.reindexObject() #avoid
    return "\n".join(out)


def configure_fckeditor(self, default=1, allusers=1, custom=1, nomerge=0):
    """
        configure fckeditor with default parameters.
        This method can be called as an external method, with the following parameters: ...?default=1&alluser=0&custom=0
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    from Products.CMFCore.utils import getToolByName

    portal = getToolByName(self, "portal_url").getPortalObject()

    try:
        pqi = getToolByName(self, "portal_quickinstaller")
        if not pqi.isProductInstalled("FCKeditor"):
            pqi.installProduct("FCKeditor")
    except Exception, msg:
        return "FCKeditor cannot be installed: '%s'" % msg

    # setting default editor to FCKeditor
    if default:
        portal.portal_memberdata.manage_changeProperties(wysiwyg_editor="FCKeditor")

    # changing editor of all users
    if allusers:
        change_user_properties(portal, kw="wysiwyg_editor:FCKeditor", dochange=1)

    # setting custom toolbar
    if custom:
        fckprops = portal.portal_properties.fckeditor_properties
        if fckprops.getProperty("fck_toolbar") != "Custom":
            fckprops.manage_changeProperties(
                fck_custom_toolbar="[\n ['Templates','rtSpellCheck'],\n ['Cut','Copy',"
                "'Paste','PasteText','PasteWord'],\n ['Undo','Redo','-','Find','Replace',"
                "'-','RemoveFormat'],\n ['Bold','Italic','Underline','StrikeThrough'],\n "
                "['OrderedList','UnorderedList'],\n ['JustifyLeft','JustifyCenter',"
                "'JustifyRight','JustifyFull'],\n ['Link','Unlink'],\n ['Image',"
                "'imgmapPopup','Table','Rule','SpecialChar'],\n ['Style','FontFormat',"
                "'TextColor'],\n ['FitWindow'],['Source']\n]"
            )
            fckprops.manage_changeProperties(fck_toolbar="Custom")

    # removing javascript merge option on fcksetting custom toolbar
    if nomerge:
        pjs = getToolByName(self, "portal_javascripts")
        pjs.updateScript("fckeditor.js", cookable=False)


def configure_ckeditor(
    self,
    default=1,
    allusers=1,
    custom="",
    rmTiny=1,
    forceTextPaste=1,
    scayt=1,
    removeWsc=1,
    skin="moono-lisa",
    filtering="",
    use_registry=False
):
    """
        configure collective.ckeditor with default parameters.
        This method can be called as an external method, with the following parameters: ...?default=1&alluser=0&custom=0
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    customs = {
        "urban": u"[\n['AjaxSave','Templates'],\n['Cut','Copy','Paste','PasteText','PasteFromWord','-',"
        "'Scayt'],\n['Undo','Redo','-','RemoveFormat'],\n['Bold','Italic','Underline','Strike'],\n"
        "['NumberedList','BulletedList','-','Outdent','Indent','Blockquote'],\n['JustifyLeft','JustifyCenter',"
        "'JustifyRight','JustifyBlock'],\n['Table','SpecialChar','Link','Unlink'],\n'/',\n['Styles','Format'],"
        "\n['Maximize', 'ShowBlocks', 'Source']\n]",
        "plonemeeting": u"[\n"
        u"['Cut','Copy','Paste','PasteText','PasteFromWord','-','Scayt'],\n"
        u"['Undo','Redo','-','RemoveFormat'],\n"
        u"['Bold','Italic','Underline','Strike','-','Subscript','Superscript'],\n"
        u"['NumberedList','BulletedList','-','Outdent','Indent'],\n"
        u"['JustifyLeft','JustifyCenter','JustifyRight','JustifyBlock'],\n"
        u"['Table','SpecialChar','Link','Unlink','Image'],\n"
        u"'/',\n"
        u"['Styles','NbSpace','NbHyphen'],\n"
        u"['Maximize','ShowBlocks','Source']\n"
        u"]\n",
        "ged": u"[\n['Templates'], \n['Cut','Copy','Paste','PasteText','PasteFromWord','-',"
        "'Scayt'],\n['Undo','Redo','-','RemoveFormat'],\n['Bold','Italic','Underline','Strike'],\n"
        "['NumberedList','BulletedList'],\n['Table','SpecialChar','Link','Unlink'],\n['Format'],\n['Maximize', "
        "'ShowBlocks', 'Source']\n]",
        "pst": u"[\n['AjaxSave'],\n['Cut','Copy','Paste','PasteText','PasteFromWord','-',"
        "'Scayt'],\n['Undo','Redo','-','RemoveFormat'],\n['Bold','Italic','Underline','Strike'],\n"
        "['NumberedList','BulletedList','-','Outdent','Indent','Blockquote'],\n['JustifyLeft','JustifyCenter',"
        "'JustifyRight','JustifyBlock'],\n['Table','SpecialChar','Link','Unlink'],\n'/',\n['Styles'],"
        "\n['Maximize', 'ShowBlocks', 'Source']\n]",
        "site": u"[\n['AjaxSave','Templates'],\n['Cut','Copy','Paste','PasteText','PasteFromWord','-','Scayt'],\n"
        "['Undo','Redo','-','Find','Replace','-','RemoveFormat'],\n['Bold','Italic','Underline','Strike','-',"
        "'Subscript','Superscript'],\n['NumberedList','BulletedList','-','Outdent','Indent','Blockquote'],\n"
        "['JustifyLeft','JustifyCenter','JustifyRight','JustifyBlock'],\n['Link','Unlink','Anchor'],\n'/',"
        "['Image','Flash','Table','HorizontalRule','Smiley','SpecialChar','PageBreak'],\n['Styles','Format'],\n"
        "['Maximize', 'ShowBlocks', 'Source']\n]",
    }

    out = [
        "Call the script followed by possible parameters:",
        "-> default=... : set as default editor (default 1)",
        "-> allusers=... : set ckeditor for all users (default 1)",
        "-> rmTiny=... : remove Tiny from available editors (default 1)",
        "-> forceTextPaste=... : set force paste as plain text (default 1)",
        "-> skin=... : set skin (default moono-lisa)",
        "-> custom=%s : set custom toolbar (default None)'\n"
        % "|".join(customs.keys()),
    ]

    from Products.CMFCore.utils import getToolByName

    portal = getToolByName(self, "portal_url").getPortalObject()

    try:
        pqi = getToolByName(self, "portal_quickinstaller")
        if not pqi.isProductInstalled("collective.ckeditor"):
            pqi.installProduct("collective.ckeditor")
    except Exception, msg:
        return "collective.ckeditor cannot be installed: '%s'" % msg

    sp = portal.portal_properties.site_properties
    if use_registry:
        registry = getUtility(IRegistry)
        ck_prefix = "collective.ckeditor.browser.ckeditorsettings.ICKEditorSchema.%s"
    else:
        ckp = portal.portal_properties.ckeditor_properties

    # setting default editor to ckeditor
    if default:
        portal.portal_memberdata.manage_changeProperties(wysiwyg_editor="CKeditor")
        sp.manage_changeProperties(default_editor="CKeditor")
        out.append("Set ckeditor as default editor")

    # remove FCKeditor from available editor
    availables = list(sp.available_editors)
    if "FCKeditor" in availables:
        availables.remove("FCKeditor")
    sp.manage_changeProperties(available_editors=availables)
    out.append("Removed FCKeditor from available editors")

    # remove Tiny from available editor
    if rmTiny:
        availables = list(sp.available_editors)
        if "TinyMCE" in availables:
            availables.remove("TinyMCE")
        sp.manage_changeProperties(available_editors=availables)
        out.append("Removed Tiny from available editors")

        def disable_resource(tool, names=[]):
            changes = False
            for name in names:
                rsc = tool.getResource(name)
                if rsc.getEnabled():
                    changes = True
                    rsc.setEnabled(False)
            if changes:
                tool.cookResources()

        disable_resource(
            portal.portal_css, names=["++resource++tinymce.stylesheets/tinymce.css"]
        )
        disable_resource(
            portal.portal_javascripts, names=["jquery.tinymce.js", "tiny_mce_gzip.js"]
        )

    # changing editor for all users
    if allusers:
        change_user_properties(portal, kw="wysiwyg_editor:CKeditor", dochange=1)
        out.append("Set ckeditor as editor for all users")

    # setting custom toolbar
    if custom:
        if custom not in customs:
            return (
                "custom parameter '%s' not defined in available custom toolbars"
                % custom
            )
        if use_registry:
            if registry.get(ck_prefix % "toolbar") != "Custom":
                registry[ck_prefix % "toolbar"] = "Custom"
                registry[ck_prefix % "toolbar_Custom"] = safe_encode(customs[custom])
        else:
            if ckp.getProperty("toolbar") != "Custom":
                ckp.manage_changeProperties(toolbar="Custom")
                ckp.manage_changeProperties(toolbar_Custom=customs[custom])
        out.append("Set '%s' toolbar" % custom)

    # force text paste
    if forceTextPaste:
        if use_registry:
            registry[ck_prefix % "forcePasteAsPlainText"] = True
        else:
            ckp.manage_changeProperties(forcePasteAsPlainText=True)
        out.append("Set forcePasteAsPlainText to True")

    # activate scayt
    if scayt:
        if use_registry:
            registry[ck_prefix % "enableScaytOnStartup"] = True
        else:
            ckp.enableScaytOnStartup = True
        out.append("Set enableScaytOnStartup to True")

    # disable the 'wsc' plugin, removing the wsc plugin will remove the
    # "Check spell" option from Scayt menu that is broken
    if removeWsc:
        if use_registry:
            removePlugins = registry.get(ck_prefix % "removePlugins")
            if 'wsc' not in removePlugins:
                removePlugins += ('wsc',)
                registry[ck_prefix % "removePlugins"] = removePlugins
        else:
            removePlugins = ckp.removePlugins
            if u'wsc' not in removePlugins:
                removePlugins += (u'wsc',)
                ckp.removePlugins = removePlugins

    # change filtering
    if filtering and filtering in ("default", "custom", "disabled"):
        if use_registry:
            registry[ck_prefix % "filtering"] = filtering
        else:
            ckp.manage_changeProperties(filtering=filtering)
        out.append("Set filtering to '{}'".format(filtering))

    # skin
    if skin:
        if use_registry:
            registry[ck_prefix % "skin"] = skin
        else:
            ckp.manage_changeProperties(skin=skin)

    return "\n".join(out)


def list_users(
    self,
    output="csv",
    sort="users",
    gtitle="1",
    separator=";",
    ignored_global_roles=("Member", "Authenticated"),
):
    """
        list users following parameters :
            sort = 'users' or 'groups', sort key for output
            gtitle = '1' or '0', include group title (1 by default)
    """
    if not check_role(self):
        return "You must have a manager role to run this script"
    lf = "<br />\n"

    from Products.CMFCore.utils import getToolByName

    pg = getToolByName(self, "portal_groups")
    out = [
        "<h2>Users list</h2>",
        "You can call the script with the following parameters:",
        "-> output=screen => output for screen or csv (default=csv)",
        "-> sort=groups (or users) => output is sorted following groups (default=users)",
        "-> gtitle=0 => include group title (default=1)",
        "-> separator=; => csv separator (default=;)",
        "by example /cputils_list_users?output=screen&sort=groups",
        "You can copy/paste the following lines in the right program like libreoffice calc ;-) or Excel :-(%s"
        % lf,
    ]

    if sort not in ("users", "groups"):
        out.append("invalid parameter sort, value must be 'users' or 'groups'")
        return
    if output not in ("csv", "screen"):
        out.append("invalid parameter output, value must be 'csv' or 'screen'")
        return
    title = False
    if gtitle not in ("", "0", "False", "false"):
        title = True

    users = {}
    groups = {}
    for member in get_users(self):
        userid = member.id

        if userid not in users:
            roles = [
                role for role in member.getRoles() if role not in ignored_global_roles
            ]
            users[userid] = {
                "obj": member,
                "name": member.getProperty("fullname"),
                "email": member.getProperty("email"),
                "roles": roles,
            }
        groupids = [
            safe_encode(gid)
            for gid in pg.getGroupsForPrincipal(member)
            if gid != "AuthenticatedUsers"
        ]
        if not groupids:
            groupids = ["aucun"]
        users[userid]["groups"] = groupids
        for groupid in groupids:
            if groupid not in groups:
                grp = pg.getGroupById(groupid)
                if grp is not None:
                    roles = [
                        role
                        for role in grp.getRoles()
                        if role not in ignored_global_roles
                    ]
                    groups[groupid] = {
                        "title": pg.getGroupInfo(groupid)
                        and pg.getGroupInfo(groupid)["title"]
                        or "",
                        "roles": roles,
                        "users": [],
                    }
                else:
                    groups[groupid] = {"title": "", "roles": [], "users": []}
            groups[groupid]["users"].append(userid)

    if output == "csv":
        titles = {
            "users": [
                "UserId",
                "GroupId",
                "Username",
                "Email",
                "UserGlobalRoles",
                "GroupGlobalRoles",
            ],
            "groups": [
                "GroupId",
                "UserId",
                "Username",
                "Email",
                "GroupGlobalRoles",
                "UserGlobalRoles",
            ],
        }
        # insert 'GroupTitle' after 'GroupId'
        if title:
            titles[sort].insert(titles[sort].index("GroupId") + 1, "GroupTitle")
        if ignored_global_roles == "*":
            titles["users"].remove("UserGlobalRoles")
            titles["users"].remove("GroupGlobalRoles")
            titles["groups"].remove("UserGlobalRoles")
            titles["groups"].remove("GroupGlobalRoles")
        out.append(separator.join(titles[sort]))

    if sort == "users":
        for userid in sorted(users.keys()):
            if output == "screen":
                outstr = "- userid: %s, fullname: %s, email: %s" % (
                    userid,
                    users[userid]["name"],
                    users[userid]["email"],
                )
                if ignored_global_roles != "*":
                    outstr += ", global roles: %s" % (",".join(users[userid]["roles"]))

                out.append(outstr)

            for groupid in users[userid]["groups"]:
                if output == "csv":
                    infos = [
                        userid,
                        groupid,
                        users[userid]["name"],
                        users[userid]["email"] or '',  # correction for ldap
                    ]
                    if title:
                        infos.insert(2, groups[groupid]["title"])
                    if ignored_global_roles != "*":
                        infos.append(
                            ",".join(users[userid]["roles"])
                        )  # user global roles before groups global roles
                        infos.append(",".join(groups[groupid]["roles"]))
                    out.append(separator.join(infos))
                else:
                    outstr = "&emsp;&emsp;&rArr; %s" % (groupid)
                    if title:
                        outstr += ", %s" % (groups[groupid]["title"])
                    if ignored_global_roles != "*":
                        outstr += ", global roles: %s" % (
                            ",".join(groups[groupid]["roles"])
                        )
                    out.append(outstr)
    elif sort == "groups":
        for groupid in sorted(groups.keys()):
            if output == "screen":
                outstr = "- groupid: %s" % (groupid)
                if title:
                    outstr += ", %s" % (groups[groupid]["title"])
                if ignored_global_roles != "*":
                    outstr += ", global roles: %s" % (
                        ",".join(groups[groupid]["roles"])
                    )
                out.append(outstr)

            for userid in groups[groupid]["users"]:
                if output == "csv":
                    infos = [
                        groupid,
                        userid,
                        users[userid]["name"],
                        users[userid]["email"],
                    ]
                    if title:
                        infos.insert(1, groups[groupid]["title"])
                    if ignored_global_roles != "*":
                        infos.append(
                            ",".join(groups[groupid]["roles"])
                        )  # group global roles before groups global roles
                        infos.append(",".join(users[userid]["roles"]))
                    out.append(separator.join(infos))
                else:
                    outstr = "&emsp;&emsp;&rArr; %s, fullname: %s, email: %s" % (
                        userid,
                        users[userid]["name"],
                        users[userid]["email"],
                    )
                    if ignored_global_roles != "*":
                        outstr += ", global roles: %s" % (
                            ",".join(users[userid]["roles"])
                        )

                    out.append(outstr)
    return lf.join(out)


def check_groups_users(self, app="docs"):
    if not check_role(self):
        return "You must have a manager role to run this script"
    lf = "<br />\n"
    out = [
        "<h2>Groups and users checks</h2>",
        "You can call the script with the following parameters:",
        "-> app=xxx => configuration to use (Default: docs){}".format(lf),
    ]
    from collective.contact.plonegroup.config import get_registry_functions
    from collective.contact.plonegroup.config import get_registry_organizations
    from collective.wfadaptations.api import get_applied_adaptations
    from datetime import datetime
    from plone import api
    from zope.component import getUtility
    from zope.schema.interfaces import IVocabularyFactory

    out.append(
        "{}T0={}".format(lf, datetime(1973, 02, 12).now().strftime("%H:%M:%S.%f"))
    )
    all_groups = {g.id: g for g in api.group.get_groups()}
    all_users = get_users(self, obj=False)
    out.append("Total of groups: {}".format(len(all_groups)))
    out.append("Total of users: {}".format(len(all_users)))
    # out.append("{}T all ={}".format(lf, datetime(1973, 02, 12).now().strftime("%H:%M:%S.%f")))
    # Functions check
    ge = (
        api.portal.get_registry_record(
            "imio.dms.mail.browser.settings.IImioDmsMailConfig.imail_group_encoder"
        )
        or api.portal.get_registry_record(
            "imio.dms.mail.browser.settings.IImioDmsMailConfig.omail_group_encoder"
        )
        or api.portal.get_registry_record(
            "imio.dms.mail.browser.settings.IImioDmsMailConfig.contact_group_encoder"
        )
    )
    wfa = [dic["adaptation"] for dic in get_applied_adaptations()]
    right_fcts = {
        "docs": {
            "encodeur": True,
            "lecteur": True,
            "editeur": True,
            "n_plus_1": (
                len(
                    [
                        wf
                        for wf in wfa
                        if wf == "imio.dms.mail.wfadaptations.IMServiceValidation"
                    ]
                )
                >= 1
                or "imio.dms.mail.wfadaptations.OMServiceValidation" in wfa
                or "imio.dms.mail.wfadaptations.TaskServiceValidation" in wfa
            ),
            "n_plus_2": (
                len(
                    [
                        wf
                        for wf in wfa
                        if wf == "imio.dms.mail.wfadaptations.IMServiceValidation"
                    ]
                )
                >= 2
            ),
            "n_plus_3": (
                len(
                    [
                        wf
                        for wf in wfa
                        if wf == "imio.dms.mail.wfadaptations.IMServiceValidation"
                    ]
                )
                >= 3
            ),
            "n_plus_4": (
                len(
                    [
                        wf
                        for wf in wfa
                        if wf == "imio.dms.mail.wfadaptations.IMServiceValidation"
                    ]
                )
                >= 4
            ),
            "n_plus_5": (
                len(
                    [
                        wf
                        for wf in wfa
                        if wf == "imio.dms.mail.wfadaptations.IMServiceValidation"
                    ]
                )
                >= 5
            ),
            "group_encoder": ge,
            "contacts_part": api.portal.get_registry_record(
                "imio.dms.mail.browser.settings."
                "IImioDmsMailConfig.contact_group_encoder"
            ),
        }
    }
    # out.append("{}T={}".format(lf, datetime(1973, 02, 12).now().strftime("%H:%M:%S.%f")))
    all_orgs = get_registry_organizations()
    all_fcts = get_registry_functions()
    voc_inst = getUtility(
        IVocabularyFactory, u"collective.contact.plonegroup.organization_services"
    )
    full_orgs = {t.value: t.title for t in voc_inst(self)}
    all_orgs = sorted(all_orgs, key=lambda o: full_orgs.get(o))
    # out.append("{}T orgs ={}".format(lf, datetime(1973, 02, 12).now().strftime("%H:%M:%S.%f")))
    out.append("Total of functions: {}".format(len(all_fcts)))
    out.append("Total of activated orgs: {}".format(len(all_orgs)))
    out.append(
        "Total of inactive orgs: {}{}".format(len(full_orgs) - len(all_orgs), lf)
    )
    groups = {}  # all possible groups created following functions
    for fct in all_fcts:
        if fct["fct_id"] not in right_fcts[app]:
            out.append("!! manual function '{}' added".format(fct["fct_id"]))
        elif not right_fcts[app][fct["fct_id"]]:
            out.append("!! useless function '{}' found".format(fct["fct_id"]))
        if not fct["enabled"]:
            out.append("!! function '{}' disabled".format(fct["fct_id"]))
        if fct["fct_orgs"]:
            groups.update(
                {
                    "{}_{}".format(org, fct["fct_id"]): {"s": "missing", "u": []}
                    for org in fct["fct_orgs"]
                }
            )
        else:
            groups.update(
                {
                    "{}_{}".format(org, fct["fct_id"]): {"s": "missing", "u": []}
                    for org in all_orgs
                }
            )
    # Orgs-functions groups check
    # out.append("{}T1={}".format(lf, datetime(1973, 02, 12).now().strftime("%H:%M:%S.%f")))
    for group in groups:
        if group not in all_groups:
            out.append("!! function group '{}' not found".format(group))
            continue
        groups[group]["s"] = "activated"
        groups[group]["u"] = [u.id for u in api.user.get_users(groupname=group)]
    all_fcts_ids = [f["fct_id"] for f in all_fcts]
    app_groups = {
        "docs": [
            "createurs_dossier",
            "dir_general",
            "encodeurs",
            "expedition",
            "lecteurs_globaux_cs",
            "lecteurs_globaux_ce",
        ]
    }
    global_groups = [
        "AuthenticatedUsers",
        "Administrators",
        "Reviewers",
        "Site Administrators",
    ] + app_groups[app]
    # Other groups check
    # out.append("{}T={}".format(lf, datetime(1973, 02, 12).now().strftime("%H:%M:%S.%f")))
    for group in all_groups:
        if group not in groups:
            parts = group.split("_")
            org = parts[:1][0]
            suffix = "_".join(parts[1:])
            if suffix and org in full_orgs and suffix in all_fcts_ids:
                groups.setdefault(group, {})["s"] = "inactive"
                groups[group]["u"] = [u.id for u in api.user.get_users(groupname=group)]
                out.append(
                    "!! group '{}' on inactive org '{}' with {} users".format(
                        group, full_orgs[org].encode("utf8"), len(groups[group]["u"])
                    )
                )
            elif group in global_groups:
                groups.setdefault(group, {})["s"] = "global"
                groups[group]["u"] = [u.id for u in api.user.get_users(groupname=group)]
            else:
                groups.setdefault(group, {})["s"] = "manual"
                groups[group]["u"] = [u.id for u in api.user.get_users(groupname=group)]
                out.append(
                    "!! global group '{}' added with {} users".format(
                        group, len(groups[group]["u"])
                    )
                )
    # Groups stats
    stats = {}
    users = {}
    for group in groups:
        if groups[group]["s"] not in stats:
            stats[groups[group]["s"]] = 0
        stats[groups[group]["s"]] += 1
        for user in groups[group]["u"]:
            users.setdefault(user, []).append(group)
    for status in stats:
        out.append("Group status '{}' : {}".format(status, stats[status]))
    # Display first 3 highest groups
    out.append("{}3 highest users number groups".format(lf))
    for i, tup in enumerate(
        sorted(groups.items(), key=lambda tp: len(tp[1]["u"]), reverse=True)[0:3]
    ):
        out.append(
            " > {}: '{}'".format(
                all_groups[tup[0]].getProperty("title"), len(tup[1]["u"])
            )
        )
    # Display first 3 highest users
    out.append("{}3 highest groups number users".format(lf))
    for i, tup in enumerate(
        sorted(users.items(), key=lambda tp: len(tp[1]), reverse=True)[0:3]
    ):
        out.append(" > {}: '{}'".format(tup[0], len(tup[1])))

    # Check useless group assignment following function
    out.append("{}Useless group attributions".format(lf))
    useless_attr = {
        "docs": {
            "lecteur": ["editeur", "n_plus_1", "n_plus_2"],
            "editeur": ["n_plus_1", "n_plus_2"],
        }
    }
    u_attr = useless_attr[app]
    for org in all_orgs:
        for u_fct in u_attr:
            u_grp = "{}_{}".format(org, u_fct)
            for h_fct in u_attr[u_fct]:
                res = set(groups[u_grp]["u"]).intersection(
                    set(groups.get("{}_{}".format(org, h_fct), {}).get("u", []))
                )
                if res:
                    out.append(
                        " > '{} ({})' can be cleaned of '{}' users; already in '{}'".format(
                            full_orgs[org].encode("utf8"),
                            u_fct,
                            ",".join(sorted(res)),
                            h_fct,
                        )
                    )

    # Check useless function: difference between target users and source users
    out.append("{}Useless function ?".format(lf))
    useless_fcts = {"docs": {"n_plus_1": "editeur"}}
    u_fcts = useless_fcts[app]
    for u_fct in u_fcts:
        if u_fct not in all_fcts_ids:
            continue
        for org in all_orgs:
            s_grp = set(groups.get("{}_{}".format(org, u_fct), {}).get("u", []))
            t_grp = set(groups.get("{}_{}".format(org, u_fcts[u_fct]), {}).get("u", []))
            if not s_grp and not t_grp:
                continue
            if s_grp == t_grp:
                out.append(
                    " > '{} ({})' and '{}': same users '{}'".format(
                        full_orgs[org].encode("utf8"),
                        u_fct,
                        u_fcts[u_fct],
                        ",".join(sorted(s_grp)),
                    )
                )
            elif not s_grp:
                out.append(
                    " > '{} ({})' and '{}': no users in the 1".format(
                        full_orgs[org].encode("utf8"), u_fct, u_fcts[u_fct]
                    )
                )
            elif not t_grp:
                out.append(
                    " > '{} ({})' and '{}': no users in the 2".format(
                        full_orgs[org].encode("utf8"), u_fct, u_fcts[u_fct]
                    )
                )
            else:
                res = t_grp.difference(s_grp)
                if res:
                    out.append(
                        " > '{} ({})' and '{}': more users '{}' in the 2".format(
                            full_orgs[org].encode("utf8"),
                            u_fct,
                            u_fcts[u_fct],
                            ",".join(sorted(res)),
                        )
                    )
                res = s_grp.difference(t_grp)
                if res:
                    out.append(
                        " > '{} ({})' and '{}': more users '{}' in the 1".format(
                            full_orgs[org].encode("utf8"),
                            u_fct,
                            u_fcts[u_fct],
                            ",".join(sorted(res)),
                        )
                    )
    out.append(
        "{}T end={}".format(lf, datetime(1973, 02, 12).now().strftime("%H:%M:%S.%f"))
    )
    return lf.join(out)


def check_users(self):
    if not check_role(self):
        return "You must have a manager role to run this script"
    from Products.CMFCore.utils import getToolByName
    from Products.CMFPlone.RegistrationTool import _checkEmail

    utils = getToolByName(self, "plone_utils")
    lf = "\n"
    errors = []
    for member in get_users(self):
        userid = member.id
        email = member.getProperty("email")
        if not email:
            errors.append("Le userid '%s' n'a pas d'adresse email" % userid)
            continue
        else:
            # add the single email address
            if not utils.validateSingleEmailAddress(email):
                errors.append(
                    "L'email '%s' du userid '%s' n'est pas valide" % (email, userid)
                )
                continue
        check, msg = _checkEmail(email)
        if not check:
            errors.append(
                "L'email '%s' du userid '%s' a un problème: %s" % (email, userid, msg)
            )
    return lf.join(errors)


def recreate_users_groups(self, only_users=False, only_groups=False, dochange=""):
    """copy users from old acl_users to the new one """

    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    from Products.CMFCore.utils import getToolByName

    portal = getToolByName(self, "portal_url").getPortalObject()

    out = []
    lf = "\n"
    out.append("call the script followed by needed parameters:")
    out.append("-> only_users=... : recreate only users")
    out.append("-> only_groups=... : recreate only groups")
    out.append("-> dochange=1 : apply changes")
    out.append("")

    change = False
    if dochange not in ("", "0", "False", "false"):
        change = True
    if not change:
        out.append(
            "The following changes are not applied: you must run the script with the parameter 'dochange=1'"
        )

    if "oldacl" not in portal.objectIds():
        out.append(
            "First you must create a folder at Plonesite root named 'oldacl' and containing a "
            "copy of another acl_users"
        )
        return lf.join(out)

    if "acl_users" not in portal.oldacl.objectIds():
        out.append(
            "You must import a Plonesite acl_users folder in the folder named '/oldacl'"
        )
        return lf.join(out)

    old_acl = portal.oldacl.acl_users
    acl = portal.acl_users
    prg = portal.portal_registration
    pgr = portal.portal_groups

    if not only_users:
        for gd in old_acl.searchGroups():
            if gd["pluginid"] == "auto_group":
                continue
            g = old_acl.source_groups.getGroupById(gd["groupid"])
            if g.getId() not in acl.getGroupIds():
                if change:
                    pgr.addGroup(g.getId(), roles=g.getRoles(), groups=g.getGroups())
                out.append("Group '%s' is added" % g.getId())
            else:
                out.append("Group '%s' already exists" % g.getId())

    if not only_groups:
        users = old_acl.getUsers()
        # thanks http://blog.kagesenshi.org/2008/05/exporting-plone30-memberdata-and.html
        passwords = old_acl.source_users._user_passwords
        # Check if password validation is activated, if so deactivate it
        # This is necessary because it will try to validate the hash instead of the real password
        val_deact = False
        plugins = acl.plugins
        val_plugins = plugins.getAllPlugins(plugin_type="IValidationPlugin")
        if "password_strength_plugin" in val_plugins["active"]:
            from Products.PluggableAuthService.interfaces.plugins import IValidationPlugin

            plugins.deactivatePlugin(IValidationPlugin, "password_strength_plugin")
            val_deact = True
        for user in users:
            if user.getUserId() not in [ud["userid"] for ud in acl.searchUsers()]:
                if change:
                    try:
                        prg.addMember(
                            user.getUserId(),
                            passwords[user.getUserId()],
                            roles=user.getRoles(),
                            domains=user.getDomains(),
                        )
                    except ValueError, error:
                        out.append(
                            "Problem creating user '%s': %s" % (user.getUserId(), error)
                        )
                        continue
                out.append("User '%s' is added" % user.getUserId())
                if not only_users:
                    for groupid in user.getGroupIds():
                        if groupid == "AuthenticatedUsers":
                            continue
                        if change:
                            pgr.addPrincipalToGroup(user.getUserId(), groupid)
                        out.append("    -> Added in group '%s'" % groupid)
            else:
                out.append("User '%s' already exists" % user.getUserId())
        # Reactivate password validation plugin, only if we deactivated it
        if val_deact:
            plugins.activatePlugin(IValidationPlugin, "password_strength_plugin")
    return lf.join(out)


def get_user_pwd_hash(self, userid=""):
    """Get a user password as hash"""
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    passwords = self.acl_users.source_users._user_passwords
    if userid in passwords:
        return "'{}' = '{}'".format(userid, passwords[userid])
    else:
        return "Cannot find password for userid '{}'".format(userid)


def set_user_pwd_hash(self, userid="", pwd="", doit=""):
    """Set a hashed user password in source_users"""
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    out = [
        "call the script followed by needed parameters:",
        "-> userid=...",
        "-> pwd=...",
        "-> doit=0",
        "Special characters must be escaped ! See https://www.w3schools.com/tags/ref_urlencode.ASP",
        "",
    ]
    passwords = self.acl_users.source_users._user_passwords
    if userid not in passwords:
        out.append("Cannot find userid '{}' in passwords".format(userid))
        return "\n".join(out)
    if not pwd.startswith("{SSHA}"):
        out.append("Password not hashed !")
        return "\n".join(out)
    if doit == "1":
        passwords[userid] = pwd
        out.append("'{}' passwd is replaced with '{}'".format(userid, pwd))
    else:
        out.append(
            "'{}' passwd WILL be replaced with '{}'. Check if what's displayed is correct !".format(
                userid, pwd
            )
        )
    return "\n".join(out)


def checkPOSKey(self):
    """
        Call a method from the script checks to check the dbs
    """
    lf = "<br />\n"
    from Products.CPUtils.scripts import checkPOSKeyErrors

    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    errors = []
    checkPOSKeyErrors.check(self, errors)
    #    if not errors:
    #        errors.append('No POSKey errors found')
    return lf.join(errors)


def correctPOSKey(self, dochange=""):
    """
        Correct a DICT like attribute.
        Must be called on site context
    """
    from Products.CMFCore.utils import getToolByName
    from ZODB.POSException import POSKeyError

    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    lf = "<br />\n"
    out = ["<h1>Cleaning POSKey errors</h1>"]
    out.append("You can/must call the script with following parameters:")
    out.append("-> dochange=1 : to apply change")
    out.append("by example ...?dochange=1")
    out.append("")

    do_change = False
    if dochange not in ("", "0", "False", "false"):
        do_change = True

    portal_url = getToolByName(self, "portal_url")

    def correctDicValues(dic, out):
        out.append("Len of dic: %d keys<br />" % len(dic))
        for key in dic.keys():
            try:
                repr(dic[key])
            except POSKeyError:
                out.append("Value of key '%s' corrupted." % key)
                if do_change:
                    del dic[key]
                    out.append("&emsp;Value deleted !")
                else:
                    out.append("&emsp;Value will be deleted")

    if (
        portal_url.getPortalPath() == "/daverdisse/daverdisse"
        and portal_url.getPortalObject() == self
    ):
        from plone.app.redirector.interfaces import IRedirectionStorage
        from zope.component import queryUtility

        utility = queryUtility(IRedirectionStorage, context=self)
        dic = utility._rpaths
        out.append("Correcting values for dic _rpaths in utility RedirectionStorage")
        correctDicValues(dic, out)

    return lf.join(out)


def sync_properties(self, base="", update="", dochange=""):
    """
        Synchronize properties between objects
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    lf = "\n"
    #    lf = '<br />'
    base_path = base
    update_path = update
    base_obj = None
    update_obj = None
    change_property = False

    from Products.CMFCore.utils import getToolByName

    portal = getToolByName(self, "portal_url").getPortalObject()
    out = []
    out.append('<head><style type="text/css">')
    out.append("table { border: 1px solid black; border-collapse:collapse; }")
    out.append("table th { border: 1px solid black; background: #8297FD; }")
    out.append("table td { border: 1px solid black; padding: 2px }")
    out.append(".red { color: red; } ")
    out.append("</style></head>")
    out.append("<h2>Synchronize properties of objects</h2>")
    out.append("<p>You can call the script with the following parameters:<br />")
    out.append(
        "-> base=path => path of base object to synchronize, beginning at the root of the plone site "
        "(those properties will be kept)<br />"
    )
    out.append(
        "-> update=path => path of update object (containing new properties), beginning at the root of "
        "the plone site<br />"
    )
    out.append(
        "-> dochange=1 => really do the change. By default, only prints changes<br />"
    )
    out.append(
        "by example /cputils_sync_properties?base=portal_skins/custom/cpskin3_properties&update=portal_skins/"
        "acptheme_cpskin3_theme1/cpskin3_properties</p>"
    )

    if not base:
        out.append("<p>!! You must enter the 'base' parameter</p>")
        return lf.join(out)

    if not update:
        out.append("<p>!! You must enter the 'update' parameter</p>")
        return lf.join(out)

    base_path = base_path.lstrip("/")
    base_obj = portal.unrestrictedTraverse(base_path)
    if base_obj is None:
        out.append("<p>base path '%s' not found in portal</p>" % base_path)
        return lf.join(out)

    update_path = update_path.lstrip("/")
    update_obj = portal.unrestrictedTraverse(update_path)
    if update_obj is None:
        out.append("<p>update path '%s' not found in portal</p>" % update_path)
        return lf.join(out)

    if dochange not in ("", "0", "False", "false"):
        change_property = True

    #    if not dochange:
    #        out.append("<p>To really change the base object to synchronize '%s', call the script with another param:</p>" %
    # base_path)
    #        out.append("<p>-> dochange=1    , by example ...&dochange=1</p>")

    #    out.append('<p style="text-align: center;">*****</p>')
    out.append("<table><thead><tr>")
    out.append("<th>Property</th>")
    out.append("<th>Status</th>")
    out.append("<th>Base value</th>")
    out.append("<th>Other value</th>")
    out.append("<th>Kept</th>")
    out.append("</tr></thead><tbody>")

    base_dic = dict(base_obj.propertyItems())
    base_keys = base_dic.keys()
    base_keys.sort()
    update_dic = dict(update_obj.propertyItems())

    for base_prop in base_keys:
        if base_prop in update_dic:
            if base_dic[base_prop] == update_dic[base_prop]:
                out.append(
                    "<tr><td>%s</td><td>==</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                    % (
                        base_prop,
                        base_dic[base_prop],
                        base_dic[base_prop],
                        base_dic[base_prop],
                    )
                )
            else:
                out.append(
                    "<tr><td>%s</td><td class='red'><></td><td>%s</td><td>%s</td><td>%s</td></tr>"
                    % (
                        base_prop,
                        base_dic[base_prop],
                        update_dic[base_prop],
                        base_dic[base_prop],
                    )
                )
            del update_dic[base_prop]
        else:
            out.append(
                "<tr><td>%s</td><td class='red'>del</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                % (base_prop, base_dic[base_prop], "", base_dic[base_prop])
            )
    update_keys = update_dic.keys()
    update_keys.sort()

    for new_prop in update_keys:
        out.append(
            "<tr><td>%s</td><td class='red'>new</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (new_prop, "", update_dic[new_prop], update_dic[new_prop])
        )
        if change_property:
            #            base_obj.manage_changeProperties({newprop:update_dic[new_prop]})
            base_obj.manage_addProperty(
                new_prop, update_dic[new_prop], update_obj.getPropertyType(new_prop)
            )

    out.append("</tbody></table>")
    return lf.join(out)


def correct_language(
    self, default="", search="all", onlycurrentfolder=0, dochange="", filter=0
):
    """
        correct language objects, set as neutral if no translation exists
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    import Missing

    lf = "\n"
    #    lf = '<br />'
    change_property = False
    only_current_folder = False
    filters = [1, 2, 3, 4]

    from Products.CMFCore.utils import getToolByName

    portal = getToolByName(self, "portal_url").getPortalObject()
    pqi = portal.portal_quickinstaller

    out = []
    out.append('<head><style type="text/css">')
    out.append("table { border: 1px solid black; border-collapse:collapse; }")
    out.append("table th { border: 1px solid black; background: #8297FD; }")
    out.append("table td { border: 1px solid black; padding: 2px }")
    out.append(".red { color: red; } ")
    out.append(".green { color: green; } ")
    out.append("</style></head>")
    out.append("<h2>Corrects language of untranslated objects</h2>")
    out.append("<p>You can call the script with the following parameters:<br />")
    out.append(
        "-> default=code => language code for untranslated objects (default to neutral)<br />"
    )
    out.append(
        "-> search=fr => language code of searched objects (default to all languages)<br />"
    )
    out.append(
        "-> onlycurrentfolder=0 => do correct language in all site (default) <br />"
    )
    out.append(
        "-> filter=1 or filter=123 => filter numbers (default to all objects)<br />"
    )
    out.append("-> &nbsp;&nbsp;&nbsp;&nbsp;1 => displays only canonical objects<br />")
    out.append("-> &nbsp;&nbsp;&nbsp;&nbsp;2 => displays only translations<br />")
    out.append(
        "-> &nbsp;&nbsp;&nbsp;&nbsp;3 => displays if object language is different from default<br />"
    )
    out.append("-> &nbsp;&nbsp;&nbsp;&nbsp;4 => displays unchanged objects<br />")
    out.append(
        "-> dochange=1 => really do the change. By default, only prints changes<br />"
    )
    out.append("by example /cputils_correct_language?default=fr&dochange=1</p>")
    out.append('<p>New value in <span class="red">red</span> will be changed</p>')

    errors = []

    if "LinguaPlone" not in [p["id"] for p in pqi.listInstalledProducts()]:
        out.append(
            "<p>LinguaPlone not installed ! Not necessary to do this operation</p>"
        )
        return lf.join(out)

    if onlycurrentfolder not in ("", "0", "False", "false"):
        only_current_folder = True

    kw = {}
    # kw['portal_type'] = ('Document','Link','Image','File','Folder','Large Plone Folder','Wrapper','Topic')
    # kw['review_state'] = ('private',) #'published'
    if only_current_folder:
        kw["path"] = "/".join(self.getPhysicalPath())
    # kw['sort_on'] = 'created'
    # kw['sort_order'] = 'reverse'
    kw["Language"] = search

    if filter:
        filters = [int(i) for i in list(filter.strip())]

    if dochange not in ("", "0", "False", "false"):
        change_property = True

    results = portal.portal_catalog.searchResults(kw)
    out.append("<p>Number of retrieved objects (not filtered): %d</p>" % len(results))
    out.append("<table><thead><tr>")
    out.append("<th>Language</th>")
    out.append("<th>Metadata</th>")
    out.append("<th>Path</th>")
    out.append("<th>New value</th>")
    out.append("</tr></thead><tbody>")

    # out.append("<tr><td>%s</td></tr>" % ';'.join(filters))
    for brain in results:
        obj = brain.getObject()
        # metadata can be missing !
        if brain.Language == Missing.MV:
            meta_lang = "Missing.Value"
        elif brain.Language == "":
            meta_lang = "neutral"
        else:
            meta_lang = brain.Language
        # we use obj instead
        try:
            if obj.getLanguage() == "":
                current_lang = "neutral"
            else:
                current_lang = obj.getLanguage()
            obj.getDeletableLanguages()
        except AttributeError:
            errors.append(
                "<div>Cannot get language on object '%s' at url '<a href=\"%s\">%s</a>'</div>"
                % (brain.Title, brain.getURL(), brain.getPath())
            )
            current_lang = "AttributeError"
            continue
        except KeyError, msg:
            # es-es not found in deletable language
            errors.append(
                "<div>Language '%s' not in deletable lang: '%s' at url '<a href=\"%s\">%s</a>'</div>"
                % (msg, brain.Title, brain.getURL(), brain.getPath())
            )
            continue

        # we first search for translated objects: no change for those objects
        # condition= already language and canonical with translations
        if current_lang and obj.isCanonical() and obj.getDeletableLanguages():
            if 1 in filters:
                out.append(
                    '<tr><td>%s</td><td>%s</td><td><a href="%s" target="_blank">%s</a></td><td class="green">'
                    "canonical</td></tr>"
                    % (current_lang, meta_lang, brain.getURL(), brain.getPath())
                )
        # condition= already language and not canonical = translation
        elif current_lang and not obj.isCanonical():
            if 2 in filters:
                out.append(
                    '<tr><td>%s</td><td>%s</td><td><a href="%s" target="_blank">%s</a></td><td class="green">'
                    "translation</td></tr>"
                    % (current_lang, meta_lang, brain.getURL(), brain.getPath())
                )
        # no translation and language must be changed
        elif current_lang != default:
            if 3 in filters:
                out.append(
                    '<tr><td class="red">%s</td><td>%s</td><td><a href="%s" target="_blank">%s</a></td>'
                    '<td class="red">%s</td></tr>'
                    % (
                        current_lang,
                        meta_lang,
                        brain.getURL(),
                        brain.getPath(),
                        default or "neutral",
                    )
                )
                if change_property:
                    obj.setLanguage(default)
                    obj.reindexObject()
        # no change
        elif 4 in filters:
            out.append(
                '<tr><td>%s</td><td>%s</td><td><a href="%s" target="_blank">%s</a></td><td>unchanged</td></tr>'
                % (current_lang, meta_lang, brain.getURL(), brain.getPath())
            )

    out.append("</tbody></table>")

    if errors:
        i = out.index("<table><thead><tr>")
        errors.append("<br />")
        out[i:i] = errors

    return lf.join(out)


def correct_pam_language(
    self,
    default="",
    search="all",
    onlycurrentfolder="0",
    dochange="",
    filter=0,
    avoidedlangfolders="",
):
    """
        manage language objects in Plone 4
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    import Missing

    lf = "\n"
    #    lf = '<br />'
    change_property = False
    only_current_folder = False
    filters = [1, 2, 3, 4]
    avoided_folders = ["shared"]
    for lang in avoidedlangfolders.split("|"):
        avoided_folders.append(lang.strip())

    from Products.CMFCore.utils import getToolByName

    portal = getToolByName(self, "portal_url").getPortalObject()
    all_langs = []
    for tup in portal.availableLanguages():
        all_langs.append(tup[0])
    lang_level_index = len(portal.getPhysicalPath())

    out = []
    out.append('<head><style type="text/css">')
    out.append("table { border: 1px solid black; border-collapse:collapse; }")
    out.append("table th { border: 1px solid black; background: #8297FD; }")
    out.append("table td { border: 1px solid black; padding: 2px }")
    out.append(".red { color: red; } ")
    out.append(".green { color: green; } ")
    out.append(".discreet, .discreet a { color: #666666; font-weight: normal;}")
    out.append("</style></head>")
    out.append("<h2>Corrects language of untranslated objects</h2>")
    out.append("<p>You can call the script with the following parameters:<br />")
    out.append(
        "-> default=code => language code for untranslated objects (default to neutral)<br />"
    )
    out.append(
        "-> search=fr => language code of searched objects (default to all languages)<br />"
    )
    out.append(
        "-> onlycurrentfolder=0 => do correct language in all site (default) <br />"
    )
    out.append(
        "-> avoidedlangfolders=fr|en => avoid objects in languages folders (default not) <br />"
    )
    out.append(
        "-> filter=1 or filter=123 => filter numbers (default to all objects)<br />"
    )
    #    out.append("-> &nbsp;&nbsp;&nbsp;&nbsp;1 => displays only canonical objects<br />")
    #    out.append("-> &nbsp;&nbsp;&nbsp;&nbsp;2 => displays only translations<br />")
    out.append(
        "-> &nbsp;&nbsp;&nbsp;&nbsp;3 => displays if object language is different from default<br />"
    )
    #    out.append("-> &nbsp;&nbsp;&nbsp;&nbsp;4 => displays unchanged objects<br />")
    out.append(
        "-> dochange=1 => really do the change. By default, only prints changes<br />"
    )
    out.append("by example /cputils_correct_language?default=fr&dochange=1</p>")
    out.append('<p>New value in <span class="red">red</span> will be changed</p>')

    errors = []

    #    if 'LinguaPlone' not in [p['id'] for p in pqi.listInstalledProducts()]:
    #        out.append("<p>LinguaPlone not installed ! Not necessary to do this operation</p>")
    #        return lf.join(out)

    if onlycurrentfolder not in ("", "0", "False", "false"):
        only_current_folder = True

    kw = {}
    # kw['portal_type'] = ('Document','Link','Image','File','Folder','Large Plone Folder','Wrapper','Topic')
    # kw['review_state'] = ('private',) #'published'
    if only_current_folder:
        kw["path"] = "/".join(self.getPhysicalPath())
    # kw['sort_on'] = 'created'
    # kw['sort_order'] = 'reverse'
    kw["Language"] = search

    if filter:
        filters = [int(i) for i in list(filter.strip())]

    if dochange not in ("", "0", "False", "false"):
        change_property = True

    results = portal.portal_catalog.searchResults(kw)
    out.append("<p>Number of retrieved objects (not filtered): %d</p>" % len(results))
    out.append("<table><thead><tr>")
    out.append("<th>Language</th>")
    out.append("<th>Metadata</th>")
    out.append("<th>Path</th>")
    out.append("<th>New value</th>")
    out.append("</tr></thead><tbody>")

    # out.append("<tr><td>%s</td></tr>" % ';'.join(filters))
    for brain in results:
        obj = brain.getObject()
        # metadata can be missing !
        try:
            if brain["Language"] == Missing.MV:
                meta_lang = "Missing.Value"
            elif brain["Language"] == "":
                meta_lang = "neutral"
            else:
                meta_lang = brain["Language"]
        except KeyError:
            meta_lang = "Missing.Value"
        # we use obj instead
        try:
            if obj.Language() == "":
                current_lang = ""
            else:
                current_lang = obj.Language()
        except AttributeError:
            errors.append(
                "<div>Cannot get language on object '%s' at url '<a href=\"%s\">%s</a>'</div>"
                % (brain.Title, brain.getURL(), brain.getPath())
            )
            current_lang = "AttributeError"
            continue

        # avoided folders
        if (
            len(obj.getPhysicalPath()) > lang_level_index
            and obj.getPhysicalPath()[lang_level_index] in avoided_folders
        ):
            out.append(
                '<tr class="discreet"><td>%s</td><td>%s</td><td><a href="%s" target="_blank">%s</a></td>'
                "<td></td></tr>"
                % (
                    current_lang or "neutral",
                    meta_lang,
                    brain.getURL(),
                    brain.getPath(),
                )
            )
        # no translation and language must be changed
        elif current_lang != default:
            if 3 in filters:
                out.append(
                    '<tr><td class="red">%s</td><td>%s</td><td><a href="%s" target="_blank">%s</a></td>'
                    '<td class="red">%s</td></tr>'
                    % (
                        current_lang or "neutral",
                        meta_lang,
                        brain.getURL(),
                        brain.getPath(),
                        default or "neutral",
                    )
                )
                if change_property:
                    obj.setLanguage(default)
                    obj.reindexObject()
        else:
            out.append(
                '<tr class="discreet"><td>%s</td><td>%s</td><td><a href="%s" target="_blank">%s</a></td>'
                "<td></td></tr>"
                % (
                    current_lang or "neutral",
                    meta_lang,
                    brain.getURL(),
                    brain.getPath(),
                )
            )

    out.append("</tbody></table>")

    if errors:
        i = out.index("<table><thead><tr>")
        errors.append("<br />")
        out[i:i] = errors

    return lf.join(out)


def copy_image_attribute(self):
    """
        copy image from canonical document into translated document.
        method to add action in site :
        1. add external method (copy_image_attribute)
        2. in portal_action add new CMF action
        3. edit this action
        >>> url (expression) is : string:${globals_view/getCurrentObjectUrl}/cputils_copy_image_attributes
        >>> Condition (expression) is : python:checkPermission("Delete objects", globals_view.getParentObject()) and
            checkPermission("Copy or Move", object) and checkPermission("Add portal content", object) and
            not globals_view.isPortalOrPortalDefaultPage() and not object.isCanonical()
    """
    from collective.contentleadimage.config import IMAGE_FIELD_NAME
    from collective.contentleadimage.utils import hasContentLeadImage

    canonical_obj = self.getCanonical()
    if not canonical_obj or (self == self.getCanonical()):
        return
    if hasContentLeadImage(canonical_obj):
        if canonical_obj.getField(IMAGE_FIELD_NAME) and self.getField(IMAGE_FIELD_NAME):
            self.getField(IMAGE_FIELD_NAME).getMutator(self)(
                canonical_obj.getField(IMAGE_FIELD_NAME).getAccessor(canonical_obj)()
            )
    self.plone_utils.addPortalMessage(u"Ajout du champ leadImage")
    return self.REQUEST.RESPONSE.redirect(self.absolute_url())


def desactivate_base2dom(self):
    """
     desactivate base2-dom javascript to resolve problem on fckeditor loading in firefox4
    """
    if not check_zope_admin():
        return "desactivate_base2dom run with a non admin user: we go out"
    out = []
    try:
        for site in get_all_site_objects(self):
            sitePath = "/".join(site.getPhysicalPath())
            if hasattr(site, "portal_javascripts"):
                js = site.portal_javascripts.getResource("++resource++base2-dom-fp.js")
                if js.getEnabled():
                    js.setEnabled(False)
                    out.append("Disabled ++resource++base2-dom-fp.js for %s" % sitePath)
    except Exception, message:
        out.append("!! error when disabling base2dom: %s" % (message))
    return "\n".join(out)


def unregister_adapter(self, unregister=""):
    """
        unregister lost adapter (product removed from the file system)
        for error "AttributeError: type object 'IThemeSpecific' has no attribute 'isOrExtends' "
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    lf = "\n"
    #    lf = '<br />'
    out = []
    out.append("<p>You can call the script with the following parameters:<br />")
    out.append(
        "-> unregister=... => name of the adapter to unregister (default to empty => "
        "list all adapters)<br />"
    )

    from Products.CMFCore.utils import getToolByName
    from zope.component import getSiteManager

    portal = getToolByName(self, "portal_url").getPortalObject()

    params = []
    components = getSiteManager(portal)
    for reg in components.registeredAdapters():
        if unregister:
            if reg.name == unregister:
                params = [reg.factory, reg.required, reg.provided]
                break
        else:
            out.append(reg.name)
    if unregister:
        try:
            if components.unregisterAdapter(
                params[0], params[1], params[2], unregister
            ):
                out.append("Adapter '%s' unregistered" % unregister)
            else:
                out.append("Adapter '%s' not unregistered !" % unregister)
        except Exception, msg:
            out.append("Adapter '%s' not unregistered : %s" % (unregister, msg))

    return lf.join(out)


def change_authentication_plugins(self, activate="", dochange=""):
    """
        activate or desactivate and save (in dtml doc) authentication plugin
    """

    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    out = []
    txt = []

    change_activate = False
    if activate not in ("", "0", "False", "false"):
        change_activate = True

    change_plugins = False
    if dochange not in ("", "0", "False", "false"):
        change_plugins = True

    if not change_plugins:
        out.append(
            "The following changes are not applied: you must run the script with the parameter '...?dochange=1'"
        )

    from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin

    if change_activate:
        # read authentication_plugins_sites dtml doc
        if "authentication_plugins_sites" not in self.objectIds():
            return out.append(
                "No DTMLDocument named 'authentication_plugins_sites' found"
            )
        doc = self.authentication_plugins_sites
        lines = doc.raw.splitlines()
        out.append(
            "Read all lines from DTMLDocument named 'authentication_plugins_sites'"
        )
        for line in lines:
            out.append(str(line))
            infos = line.split("\t")
            site = infos[0]
            if site.find("/") > 0:
                (path, site) = site.split("/")
                if hasattr(self, path):
                    context = getattr(self, path)
                else:
                    continue
            else:
                context = self
            if hasattr(context, site):
                out.append("site found %s" % site)
                obj = getattr(context, site)
                plugins = obj.acl_users.plugins
            else:
                continue
            auth_plugins = plugins.getAllPlugins(plugin_type="IAuthenticationPlugin")
            for i in range(1, len(infos)):
                plugin = infos[i]
                if plugin not in auth_plugins["active"]:
                    # activate authentication plugins
                    out.append("Activate plugins %s for %s" % (plugin, site))
                    if change_plugins:
                        plugins.activatePlugin(IAuthenticationPlugin, plugin)
    else:
        # save authentication_plugins_sites in dtml doc plugin from all site
        if "authentication_plugins_sites" not in self.objectIds():
            self.manage_addDTMLDocument(
                id="authentication_plugins_sites",
                title="All authentication plugins sites",
            )
            out.append(
                "Document '%s/authentication_plugins_sites' added"
                % "/".join(self.getPhysicalPath())
            )
        allSiteObj = get_all_site_objects(self)
        for obj in allSiteObj:
            objPath = ""
            for i in range(1, len(obj.getPhysicalPath()) - 1):
                objPath = objPath + obj.getPhysicalPath()[i] + "/"
            objid = obj.getId()
            plugins = obj.acl_users.plugins
            auth_plugins = plugins.getAllPlugins(plugin_type="IAuthenticationPlugin")
            plugLine = objPath + objid
            for plug in list(auth_plugins["active"]):
                plugLine = plugLine + "\t" + str(plug)
                out.append(
                    "Desactivate plugins %s for %s" % (str(plug), objPath + objid)
                )
                if change_plugins:
                    # desactivate authentication plugins
                    plugins.deactivatePlugin(IAuthenticationPlugin, plug)
            txt.append(plugLine)

        doc = self.authentication_plugins_sites
        doc.raw = "\n".join(txt)
        out.append("Document '/authentication_plugins_sites' updated !")
    return "\n".join(out)


def install_plone_product(self, productName="", installMode="", dochange=""):
    """
        install/reinstall or uninstall a plone product
    """

    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    out = []

    out.append('<head><style type="text/css">')
    out.append("table { border: 1px solid black; border-collapse:collapse; }")
    out.append("table th { border: 1px solid black; background: #8297FD; }")
    out.append("table td { border: 1px solid black; padding: 2px }")
    out.append(".red { color: red; } ")
    out.append(".green { color: green; } ")
    out.append("</style></head>")
    out.append("<h2>Install, Uninstall or Re-Install product</h2>")
    out.append("<p>You can call the script with the following parameters:<br />")
    out.append("-> productName=name of product => ie. contact<br />")
    out.append(
        "-> installMode='I','U' or 'R' => Install (Re-Install if product exist), Uninstall or Re-install "
        "(not install if product doesn't exist)<br />"
    )
    out.append(
        "-> (Optional) dochange=1 => really do the change. By default, only prints changes<br />"
    )
    out.append(
        "<p>by example /install_plone_product?productName=Linguaplone&installMode=I&dochange=1</p>"
    )

    out.append("<table><thead><tr>")
    out.append("</tr></thead><tbody>")
    if productName == "":
        out.append(
            """<tr><td class="red">please, choose a product to install</td><td class="red"></td></tr>"""
        )
        return "\n".join(out)

    if installMode not in ("I", "U", "R"):
        out.append(
            """<tr><td class="red">please, installMode must be in 'I','U' or 'R'</td>"""
            """<td class="red"></td></tr>"""
        )
        return "\n".join(out)
    out.append("</tbody></table>")

    execute_change = False
    if dochange not in ("", "0", "False", "false"):
        execute_change = True

    if not execute_change:
        out.append(
            "The following changes are not applied: you must run the script with the parameter '...?dochange=1'"
        )

    # get all site on root or in first folder (by mountpoint)
    allSiteObj = get_all_site_objects(self)
    if installMode in ("I", "R"):
        # install or re-install product
        for obj in allSiteObj:
            objid = obj.getId()
            if not obj.portal_quickinstaller.isProductInstallable(productName):
                out.append("<p>Bad Product name %s for %s</p>" % (productName, objid))
                continue
            if obj.portal_quickinstaller.isProductInstalled(productName):
                out.append("<p>Re-install product %s for %s</p>" % (productName, objid))
                if execute_change:
                    obj.portal_quickinstaller.reinstallProducts([productName])
            elif installMode == "I":
                out.append("<p>Install product %s for %s</p>" % (productName, objid))
                if execute_change:
                    obj.portal_quickinstaller.installProducts([productName])
    else:
        # uninstall product
        for obj in allSiteObj:
            objid = obj.getId()
            if not obj.portal_quickinstaller.isProductInstallable(productName):
                out.append("<p>Bad Product name %s for %s</p>" % (productName, objid))
                continue
            if obj.portal_quickinstaller.isProductInstalled(productName):
                out.append("<p>Uninstall product %s for %s</p>" % (productName, objid))
                if execute_change:
                    obj.portal_quickinstaller.uninstallProducts([productName])
    return "\n".join(out)


def send_adminMail(
    self,
    dochange="",
    subject="Aux administrateurs du site plone",
    bodyText="",
    allsites="1",
):
    """
        send mail to all admin user
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    out = []
    send_mail = False
    if dochange not in ("", "0", "False", "false"):
        send_mail = True

    # get all site on root or in first folder (by mountpoint)
    allSiteObj = get_all_site_objects(self)
    if allsites in ("", "0", "False", "false"):
        allSiteObj = [self.portal_url.getPortalObject()]

    for obj in allSiteObj:
        # get contact email
        authorEmail = obj.email_from_address
        users_mail = [authorEmail]
        # get administrators email
        for userInfos in obj.acl_users.searchUsers():
            userid = userInfos["userid"]
            member = obj.portal_membership.getMemberById(userid)
            if member.has_role("Manager"):
                user_mail = member.getProperty("email")
                if user_mail != "" and user_mail not in users_mail:
                    users_mail.append(user_mail)
        objPath = "/".join(obj.getPhysicalPath())
        To = ";".join(users_mail)

        out.append("EMAIL for site %s" % objPath)
        out.append(
            "From : %s, To : %s, Mail subject : %s, mail data : %s "
            % (authorEmail, To, subject, bodyText)
        )

        if send_mail:
            ret = sendmail(obj, authorEmail, To, bodyText, subject=subject)
            ret and out.append("Return code:%s" % ret)

    return "\n".join(out)


def checkInstance(self, isProductInstance="", instdir=""):
    from Products.CPUtils.hiddenProductsList import dic_hpList

    if not check_zope_admin():
        return "checkInstance run with a non admin user: we go out"
    try:
        out = []

        is_Production_Instance = False
        if isProductInstance not in ("", "0", "False", "false"):
            is_Production_Instance = True
        allSiteObj = get_all_site_objects(self)
        isProductInstance = self.getId()

        # 0.Check if hiddenProducts properties exists, and if yes, check discrepancies
        if not hasattr(self, "hiddenProducts"):
            out.append(" !! No hiddenProducts properties defined")
        else:
            # Search the "type" of application hosted by the zope instance (website, urban, teleservice,..)
            type = ""
            for productname in dic_hpList.keys():
                # Determine it by checking if the product is installable
                if productname in self.Control_Panel.Products.objectIds():
                    type = productname
                    break
            # Once the type is known, look for discrepancies in the "hidden products" list for this type of product
            external_hp_list = set(dic_hpList[type])
            internal_hp_list = set(self.hiddenProducts)
            for hiddenProduct in external_hp_list.symmetric_difference(
                internal_hp_list
            ):
                if hiddenProduct not in internal_hp_list:
                    out.append(
                        "!! the product '%s' is in the hidden products external list but not in the site list"
                        % (hiddenProduct)
                    )
                else:
                    out.append(
                        "!! the product '%s' is in the hidden products site list but not in the external list"
                        % (hiddenProduct)
                    )

        for obj in allSiteObj:
            objid = obj.getId()
            objPath = ""
            for i in range(1, len(obj.getPhysicalPath()) - 1):
                objPath = objPath + obj.getPhysicalPath()[i] + "/"
            # out.append(">> Site in analyse : %s" % objPath+objid)
            # 1. Check if we are in debugMode (only for product instance)
            if is_Production_Instance:
                # out.append(">> Check debugMode")
                if hasattr(obj, "portal_css"):
                    if obj.portal_css.debugmode:
                        obj.portal_css.setDebugMode(False)
                        out.append(
                            "!! %s (debugMode) >>> Css : %s"
                            % (objPath + objid, obj.portal_css.debugmode)
                        )
                if hasattr(obj, "portal_javascripts"):
                    if obj.portal_javascripts.debugmode:
                        obj.portal_javascripts.setDebugMode(False)
                        out.append(
                            "!! %s (debugMode) >>> Javascripts : %s"
                            % (objPath + objid, obj.portal_javascripts.debugmode)
                        )
                if hasattr(obj, "portal_kss"):
                    if obj.portal_kss.debugmode:
                        obj.portal_kss.setDebugMode(False)
                        out.append(
                            "!! %s (debugMode) >>> kss %s"
                            % (objPath + objid, obj.portal_kss.debugmode)
                        )
            # 2. Check if robot.txt exist in test instance and not exist in product instance
            # out.append(">> Check robots.txt")
            if hasattr(obj, "portal_skins.custom"):
                if is_Production_Instance and hasattr(
                    obj.portal_skins.custom, "robots.txt"
                ):
                    out.append(
                        "!! %s >>> Have a file named 'robots.txt'" % (objPath + objid)
                    )
                elif not is_Production_Instance and not hasattr(
                    obj.portal_skins.custom, "robots.txt"
                ):
                    out.append(
                        "!! %s >>> Haven't a file named 'robots.txt'"
                        % (objPath + objid)
                    )
            # 3. Check if connexion plugins is activate
            # out.append(">> Check connexion plugins")
            plugins = obj.acl_users.plugins
            auth_plugins = plugins.getAllPlugins(plugin_type="IAuthenticationPlugin")
            if not auth_plugins["active"]:
                out.append(
                    "!! %s >>> No connexion plugins is activate" % (objPath + objid)
                )
            # 4. Check if Ids is correct (without space)
            # out.append(">> Check Ids")
            if objid.find(" ") >= 0:
                out.append(
                    "!! %s >>> this site (%s) contain space characters in id"
                    % (objPath + objid, objid)
                )
            # 5. Check if cache setup is installed (only for product instance)
            if is_Production_Instance:
                # out.append(">> Check CacheSetup")
                if hasattr(obj, "portal_quickinstaller"):
                    if not obj.portal_quickinstaller.isProductInstalled("CacheSetup"):
                        out.append(
                            "!! %s >>> cache setup isn't installed" % (objPath + objid)
                        )
            # out.append("")
        return "\n".join(out)
    except Exception, message:
        out.append("!! error in checkinstance %s" % str(message))
        return "\n".join(out)


def list_context_portlets_by_name(self, portlet_name=""):
    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    if not portlet_name:
        return (
            "You MUST provide a portlet_name to query for. "
            "Add '?portlet_name=myportletname' at the end of the url calling this script. "
            "If you want to see every portlets of this site, use '*' as portlet_name"
        )

    from plone.portlets.interfaces import ILocalPortletAssignable
    from plone.portlets.interfaces import IPortletAssignmentMapping
    from plone.portlets.interfaces import IPortletManager
    from Products.CMFCore.utils import getToolByName
    from zope.component import getMultiAdapter
    from zope.component import getUtility

    out = ['<table><tr style="nth-child(odd): background-color: #000000;">']
    left_column = getUtility(IPortletManager, name=u"plone.leftcolumn")
    right_column = getUtility(IPortletManager, name=u"plone.rightcolumn")

    brains = self.portal_catalog()
    # Add the portal as it is portlet assignable
    portal_url = getToolByName(self, "portal_url")
    portal = portal_url.getPortalObject()

    for brain in [portal] + list(brains):
        if not brain.portal_type == "Plone Site":
            obj = brain.getObject()
        else:
            obj = brain
        # check if the obj is portlet assignable
        if not ILocalPortletAssignable.providedBy(obj):
            continue

        abs_url = obj.absolute_url()
        left_mappings = getMultiAdapter((obj, left_column), IPortletAssignmentMapping)
        if not portlet_name == "*" and portlet_name in left_mappings:
            out.append(
                '<td width=50%%>left_column</td><td width=50%%><a href="%s">%s</a></td></tr>'
                % (abs_url, abs_url)
            )
        elif portlet_name == "*":
            for k in left_mappings.keys():
                out.append(
                    '<td width=20%%>left_column</td><td width=60%%><a href="%s">%s</a></td>'
                    "<td width=20%%>%s</td></tr>" % (abs_url, abs_url, k)
                )
        right_mappings = getMultiAdapter((obj, right_column), IPortletAssignmentMapping)
        if not portlet_name == "*" and portlet_name in right_mappings:
            out.append(
                '<td width=50%%>right_column</td><td width=50%%><a href="%s">%s</a></td></tr>'
                % (abs_url, abs_url)
            )
        elif portlet_name == "*":
            for k in right_mappings.keys():
                out.append(
                    '<td width=20%%>right_column</td><td width=60%%><a href="%s">%s</a></td>'
                    "<td width=20%%>%s</td></tr>" % (abs_url, abs_url, k)
                )

    if out == ['<table><tr style="nth-child(odd): background-color: #000000;">']:
        out = ['Nothing found with search parameter "%s"' % portlet_name]
    else:
        out.append("</table>")
        out.extend(
            (
                "<style type='text/css'>tr:nth-child(even) {background-color: #EDEDED;}</style>",
            )
        )

    return "\n".join(out)


def list_portlets(self):
    if not check_zope_admin():
        return "checkInstance run with a non admin user: we go out"

    from zope.annotation.interfaces import IAnnotations

    out = []
    ann = IAnnotations(self)
    out.append(
        "left: "
        + str(
            dict(ann["plone.portlets.contextassignments"].get("plone.leftcolumn", ""))
        )
    )
    out.append(
        "right: "
        + str(
            dict(ann["plone.portlets.contextassignments"].get("plone.rightcolumn", ""))
        )
    )
    return "\n".join(out)


def rename_long_ids(self, length="255", dochange="", fromfile=""):
    """
        Renames too long ids, not permitting transmogrifier export
        1) run on orig site first, writing correspondences in output file
        2) renames as orig filenames from correspondences file
    """
    from Acquisition import aq_base
    from Products.CMFCore.utils import getToolByName

    import os.path

    if not check_role(self):
        return "You must have a manager role to run this script"

    out = []
    out.append("<p>You can call the script with following parameters:</p>")
    out.append("-> length=20 : maximum length of id")
    out.append("-> fromfile : rename from the generated file")
    out.append("-> dochange=1 : to do really the changes")
    out.append("by example ...?length=20&dochange=1<br/>")

    from_file = False
    if fromfile not in ("", "0", "False", "false"):
        from_file = True
    do_change = False
    if dochange not in ("", "0", "False", "false"):
        do_change = True
    max_len = int(length)

    portal_url = getToolByName(self, "portal_url")
    portal = portal_url.getPortalObject()

    otn = {}
    nto = {}
    plen = max_len - 3

    def cut_oid(oid):
        """ Cut oid following '-', nicer """
        i = lasti = 0
        while i >= 0:
            lasti = i
            i = oid.find("-", i + 1, plen)
        if lasti:
            return oid[0:lasti]
        else:
            return oid[0:plen]

    if not from_file:
        results = portal.portal_catalog.searchResults()
        otn["/"] = {}
        otn["/"]["obj"] = portal
        otn["/"]["npathid"] = ""

        # cannot get results sorted by path index !
        for r in results:
            obj = r.getObject()
            rpathid = "/%s" % "/".join(portal_url.getRelativeContentPath(obj))
            otn[rpathid] = {}
            otn[rpathid]["obj"] = obj

        txt = []
        # sort objects by path, handling parents to childs
        for opathid in sorted(otn.keys()):
            if opathid == "/":
                continue
            (opath, oid) = os.path.split(opathid)
            noid = oid
            npath = otn[opath]["npathid"]
            if len(oid) > max_len:
                cont = otn[opath]["obj"]
                baseoid = noid = cut_oid(oid)
                i = 1
                while hasattr(aq_base(cont), noid) or "%s/%s" % (npath, noid) in nto:
                    noid = "%s-%d" % (baseoid, i)
                    i += 1
            npathid = "%s/%s" % (npath, noid)
            otn[opathid]["npathid"] = npathid
            nto[npathid] = opathid
            if opathid != npathid:
                txt.append("%s => %s" % (opathid, npathid))
                out.append("%s => %s" % (opathid, npathid))

        if do_change:
            # reverse sort objects by path to change id, handling childs to parents
            for opathid in sorted(otn.keys(), reverse=True):
                if opathid == "/" or opathid == otn[opathid]["npathid"]:
                    continue
                obj = portal.restrictedTraverse(opathid[1:])
                nid = os.path.split(otn[opathid]["npathid"])[1]
                obj.setId(nid)
                obj.reindexObject("id")

        if "rename_long_ids" not in portal.objectIds():
            portal.manage_addDTMLDocument(
                id="rename_long_ids", title="Correspondences for long ids rename"
            )
            out.append(
                "<br />Document '%s/rename_long_ids' added"
                % "/".join(portal.getPhysicalPath())
            )
        doc = self.rename_long_ids
        if txt:
            doc.raw = "\n".join(txt)
            out.append(
                "Document '%s/rename_long_ids' updated !"
                % "/".join(portal.getPhysicalPath())
            )
    else:
        if "rename_long_ids" not in portal.objectIds():
            return "You must import at the root site the DTMLDocument named 'rename_long_ids'"
        # first we load the correspondences
        doc = portal.rename_long_ids
        lines = doc.raw.splitlines()
        # reverse sort objects by path to change id, handling childs to parents
        for line in sorted(lines, reverse=True):
            opathid, npathid = line.split(" => ")
            opath, oid = os.path.split(opathid)
            out.append("%s => %s" % (npathid, oid))
            if do_change:
                obj = portal.restrictedTraverse(npathid[1:])
                obj.setId(oid)
                obj.reindexObject("id")

    if do_change:
        out.append("<br />Rename applied !")
    return "<br />".join(out)


def list_newsletter_users(self, activity="all", format="all"):
    if not check_role(self):
        return "You must have a manager role to run this script"

    out = []

    out.append("You can call the script with following parameters:\n")
    out.append("-> activity=all : 'all' (default value).")
    out.append("                :'active' selects active users")
    out.append("                :'inactive' selects inactive users")
    out.append("-> format=all : 'all' (default value).")
    out.append("              :'HTML' selects users with the HTML format")
    out.append("              :'Text' selects users with the text format")
    out.append(
        "\nexample:  .../cputils_list_newsletter_users?activity=active&format=Text\n"
    )

    options = {
        "activity": ["all", "active", "inactive"],
        "format": ["all", "HTML", "Text"],
    }

    if activity not in options["activity"]:
        activity = options["activity"][0]
    if format not in options["format"]:
        format = options["format"][0]

    header = ["EMAIL", "ACTIVE", "FORMAT"]
    header = ",".join(header)

    results = self.portal_catalog.searchResults(portal_type="NewsletterBTree")
    for brain in results:
        obj = brain.getObject()
        out.append(
            "\nSucribers list of the folder '"
            + obj.Title()
            + "' from the newsletter '"
            + obj.aq_parent.Title()
            + "'\n"
        )
        out.append(header)
        for sub in obj.objectValues():
            line = [sub.email]

            if activity != "all" and (activity == "active") != sub.active:
                continue

            if sub.active:
                act = "*"
            else:
                act = ""
            line.append(act)

            if format != "all" and format != sub.format:
                continue
            line.append(sub.format)

            out.append(",".join(line))

    return "\n".join(out)


def zmi(self):
    if not check_role(self):
        return "You must have a manager role to run this script"

    """ no more necessary
    servers = { 'plonegov' : 'plonegov-0000.proxy.pilotsystems.net',
                'villesetcommunes' : 'villesetcommunes.all2all.org:0000',
                'villesetcommunes3' : 'villesetcommunes3.all2all.org:0000',}
    """
    import socket

    infos = self.Control_Panel.getServers()
    hostname = socket.gethostname()
    # ip_address = socket.gethostbyname(hostname)
    out = []
    if "instance" in hostname:  # into docker
        import os

        hostname = os.environ.get("HOSTNAME_HOST")
        http_port = os.environ.get("HTTP_PORT")
        url = "http://{0}:{1}/manage_main".format(hostname, http_port)
        out.append('<a href="%s">%s</a>' % (url, url))
        return self.REQUEST.RESPONSE.redirect(url)

    server = "localhost:0000"
    if infos and len(infos[0]) > 1:
        port = infos[0][1]
        out.append(port)
        port = port.replace("Port: ", "")
        #        if servers.has_key(hostname):
        #            server = servers[hostname]
        server = server.replace("localhost", hostname)
        #        server = server.replace('localhost', ip_address)
        server = server.replace("0000", port)
        url = "http://%s/manage_main" % server
        out.append('<a href="%s">%s</a>' % (url, url))
        return self.REQUEST.RESPONSE.redirect(url)
    # out.append(infos[1])
    return "<br />\n".join(out)


def removeStep(self, step=""):
    """
        Remove an import step
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    from Products.CMFCore.utils import getToolByName

    out = []

    out.append("You can call the script with following parameters:\n")
    out.append("-> step=name of step to delete\n")

    setup = getToolByName(self, "portal_setup")

    ir = setup.getImportStepRegistry()

    out.append("before delete")
    out.append(str(ir.listSteps()))  # for debugging and seeing what steps are available

    # delete the offending step
    try:
        del ir._registered[step]
    except KeyError:
        pass

    import transaction

    transaction.commit()

    out.append("after delete")
    out.append(str(ir.listSteps()))  # for debugging and seeing what steps are available
    return "<br />\n".join(out)


def remove_dependency_step(self, step="", dependency="", change="", by="5"):
    """
        Remove from import step an invalid dependency
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    from Products.CMFCore.utils import getToolByName
    from Products.GenericSetup.registry import _import_step_registry

    out = []

    out.append("<h2>You can call the script with following parameters:\n</h2>")
    out.append("-> step=name of step to search in\n")
    out.append("-> dependency=name of dependency to remove from list\n")
    out.append("-> by=5 print x items by line\n")
    out.append("-> change=1 apply changes\n")
    by = int(by)

    setup = getToolByName(self, "portal_setup")
    for registry, name in (
        (setup.getImportStepRegistry(), "getImportStepRegistry"),
        (_import_step_registry, "_import_step_registry"),
    ):
        out.append("<br /><b>Available steps in '{}'</b>".format(name))
        steps = sorted(registry.listSteps())
        out.append(
            "{}".format(
                "<br />\n".join(
                    [", ".join(steps[i: i + by]) for i in xrange(0, len(steps), by)]
                )
            )
        )
        if registry._registered.get(step) is None:
            continue
        deps = list(registry._registered.get(step)["dependencies"])
        out.append("<b>Available dependencies</b> for {}: {}".format(step, deps))
        if dependency in deps:
            deps.remove(dependency)
            out.append("<b>New dependencies</b>: {}".format(deps))
            if change == "1":
                registry._registered.get(step)["dependencies"] = tuple(deps)
                out.append("<b>New value applied</b>")
    if change == "1":
        setup._p_changed = True
    return "<br />\n".join(out)


def removeRegisteredTool(self, tool=""):
    """
        Remove a tool
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    from Products.CMFCore.utils import getToolByName

    out = []

    out.append("You can call the script with following parameters:\n")
    out.append("-> tool=name of tool to delete\n")

    setup = getToolByName(self, "portal_setup")

    toolset = setup.getToolsetRegistry()

    out.append("before delete")
    out.append(str(toolset.listRequiredTools()))

    # delete the offending step
    try:
        del toolset._required[tool]
    except KeyError:
        pass

    import transaction

    transaction.commit()

    out.append("after delete")
    out.append(str(toolset.listRequiredTools()))
    return "<br />\n".join(out)


def subscribers(self):
    """
        Display subscribers on context (Products.PloneboardSubscription)
    """
    if not check_role(self):
        return "You must have a manager role to run this script"
    from Products.CMFCore.utils import getToolByName

    portal_url = getToolByName(self, "portal_url")
    portal = portal_url.getPortalObject()
    pb_tool = getToolByName(portal, "portal_pbnotification")
    path = pb_tool.getObjId(self)
    if path in pb_tool.subscribers:
        return "Subscribers on '%s':\n%s" % (
            path,
            "\n".join(sorted(pb_tool.subscribers[path])),
        )
    return "No subscriber on %s" % path


def subscribe_forums(
    self,
    userids="",
    dochange="",
    action="add",
    target="forum,conversation",
    details="",
    path="",
):
    """
        Manage subscription to forum or conversation (Products.PloneboardSubscription)
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    import os

    out = []
    out.append("<p>You can call the script with following parameters:</p>")
    out.append("-> userids=user1,user2 : list of users separated by ,")
    out.append(
        "-> action=add|remove|replace : 'add' (default) or 'remove' the users for all forums. "
        "'replace' user1 by user2 for all forums and conversations."
    )
    out.append("-> target=forum,conversation : list of changes target (default twice)")
    out.append("-> path=folder : relative site path to search in")
    out.append("-> details=1 : display all subscribers")
    out.append("-> dochange=1 : to do really the changes")
    out.append("by example ...?userids=user1,user2&dochange=1<br/>")

    do_change = False
    if dochange not in ("", "0", "False", "false"):
        do_change = True
    if not userids:
        return "<br />\n".join(out)

    kw = {"sort_on": "path", "portal_type": []}
    targets = target.strip().split(",")
    for starget in targets:
        if starget == "forum":
            kw["portal_type"].append("PloneboardForum")
        elif starget == "conversation":
            kw["portal_type"].append("PloneboardConversation")
        else:
            out.append(
                "Target option '%s' must be a list of forum and/or conversation '%s'"
                % (starget, target)
            )
            return "<br />\n".join(out)

    from Products.CMFCore.utils import getToolByName

    portal_url = getToolByName(self, "portal_url")
    portal = portal_url.getPortalObject()
    pb_tool = getToolByName(portal, "portal_pbnotification")
    mtool = getToolByName(portal, "portal_membership")
    if path:
        kw["path"] = os.path.join(portal_url.getPortalPath(), path)
    out.append("Catalog search parameters: %s<br/>" % repr(kw))

    users = userids.split(",")
    users = [user.strip(" ").decode() for user in users]
    if action == "replace" and len(users) != 2:
        out.append(
            "With replace action, you have to give 2 users: ?userids=oldname,newname"
        )
    error = False
    for user in users:
        mem = mtool.getMemberById(user)
        if mem is None:
            out.append("!! user not exist: %s" % user)
            error = True
    if not error:
        i = 0
        results = portal.portal_catalog.searchResults(kw)
        for brain in results:
            i += 1
            obj_path = brain.getPath()
            type = brain.getObject().getPortalTypeName().replace("Ploneboard", "")
            if action in ("add", "remove"):
                for user in users:
                    if (
                        obj_path not in pb_tool.subscribers
                        or user not in pb_tool.subscribers[obj_path]
                    ):
                        if action == "add":
                            out.append("%d %s: %s (%s)" % (i, type, brain.id, obj_path))
                            if details and obj_path in pb_tool.subscribers:
                                out.append(
                                    "&emsp;... %s"
                                    % ",".join(pb_tool.subscribers[obj_path])
                                )
                            if do_change:
                                pb_tool.addSubscriber(brain.getObject(), user)
                                out.append("&emsp;===> added")
                            else:
                                out.append("&emsp;===> will be added")
                    else:
                        if action == "remove":
                            out.append("%d %s: %s (%s)" % (i, type, brain.id, obj_path))
                            if details:
                                out.append(
                                    "&emsp;... %s"
                                    % ",".join(pb_tool.subscribers[obj_path])
                                )
                            if do_change:
                                pb_tool.subscribers[obj_path].remove(user)
                                out.append("&emsp;===> removed")
                            else:
                                out.append("&emsp;===> will be removed")
            elif action == "replace":
                oldname, newname = users
                if (
                    obj_path in pb_tool.subscribers
                    and oldname in pb_tool.subscribers[obj_path]
                ):
                    out.append("%d %s: %s (%s)" % (i, type, brain.id, obj_path))
                    if details and obj_path in pb_tool.subscribers:
                        out.append(
                            "&emsp;... %s" % ",".join(pb_tool.subscribers[obj_path])
                        )
                    idx = pb_tool.subscribers[obj_path].index(oldname)
                    if do_change:
                        if newname in pb_tool.subscribers[obj_path]:
                            pb_tool.subscribers[obj_path].pop(idx)
                            out.append("&emsp;===> %s removed" % oldname)
                        else:
                            pb_tool.subscribers[obj_path][idx] = newname
                            out.append(
                                "&emsp;===> %s replaced by %s" % (oldname, newname)
                            )
                    elif newname in pb_tool.subscribers[obj_path]:
                        out.append("&emsp;===> %s will be removed" % oldname)
                    else:
                        out.append(
                            "&emsp;===> %s will be replaced by %s" % (oldname, newname)
                        )
    if do_change:
        # We must indicate that the PersistentMapping has been modified. Otherwise nothing is commited
        pb_tool.subscribers._p_changed = 1
        import transaction

        transaction.commit()

    return "<br />\n".join(out)


def list_used_views(self, specific_view=None):
    """
        List used views of the plone site
        If a specific_view is given, return only elements using this particular view, either
        returns every used views
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    from Products.CMFCore.utils import getToolByName

    portal = getToolByName(self, "portal_url").getPortalObject()
    catalog = portal.portal_catalog
    types = portal.portal_types.objectIds()
    views = {}

    for t in types:
        brains = catalog(portal_type=t)
        for brain in brains:
            ob = brain.getObject()
            layout = ob.getLayout()
            if t not in views:
                views[t] = {}
            if not specific_view:
                if layout not in views[t]:
                    views[t][layout] = 0
                views[t][layout] += 1
            elif specific_view and specific_view == layout:
                views[t]["/".join(ob.getPhysicalPath())] = ob.absolute_url()
    if not specific_view:
        out = ["Used views on objects\n---------------------\n"]
        for typ in views.keys():
            out.append(
                "%s : %s"
                % (
                    typ,
                    ", ".join(
                        [
                            "%s (%s)" % (lay, views[typ][lay])
                            for lay in sorted(views[typ])
                        ]
                    ),
                )
            )
    else:
        out = [
            "<html><b><u>Objects using the '%s' layout</u></b><br /><br />"
            % specific_view
        ]
        for typ in views.keys():
            for path in sorted(views[typ]):
                out.append("%s : <a href='%s'>%s</a>" % (typ, views[typ][path], path))
                out.append("<br />")
        out.append("</html>")
    return "\n".join(out)


def list_local_roles(self):
    """
        List defined local roles on the site
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    out = ["<h1>List of defined local roles</h1>"]
    avoided_roles = ["Owner"]
    from Products.CMFCore.utils import getToolByName

    purl = getToolByName(self, "portal_url")
    portal = purl.getPortalObject()
    acl = portal.acl_users
    putils = portal.plone_utils
    catalog = portal.portal_catalog
    brains = catalog(sort_on="path")
    objects = [brain.getObject() for brain in brains]
    objects.insert(0, portal)
    for ob in objects:
        olr = []
        for username, roles, userType, userid in acl._getLocalRolesForDisplay(ob):
            roles = [role for role in roles if role not in avoided_roles]
            if roles:
                olr.append(".. %s '%s' => %s" % (userType, userid, ", ".join(roles)))
        lra = putils.isLocalRoleAcquired(ob)
        # we log too if acquisition is disabled
        if olr or not lra:
            out.append(
                '<a href="%s/@@sharing">%s</a> : %s'
                % (
                    ob.absolute_url(),
                    "/" + "/".join(purl.getRelativeContentPath(ob)),
                    (
                        lra
                        and " "
                        or '<span style="color:red">acquisition disabled !</span>'
                    ),
                )
            )
            out += olr
    return "<br />\n".join(out)


def unlock_webdav_objects(self, dochange=""):
    """
        unlock webdav locked objects
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    from Products.CMFCore.utils import getToolByName

    purl = getToolByName(self, "portal_url")
    portal = purl.getPortalObject()

    out = []
    out.append("<p>You can call the script with following parameters:</p>")
    out.append("-> dochange=1 : to unlock objects")
    out.append("by example ...?dochange=1<br/>")
    out.append("<h1>Locked objects in '%s'</h1>" % self.absolute_url_path())

    do_change = False
    if dochange not in ("", "0", "False", "false"):
        do_change = True

    def unlock_obj(obj):
        if obj.wl_isLocked():
            out.append("%s is locked" % obj.absolute_url())
            if do_change:
                obj.wl_clearLocks()
                if obj.wl_isLocked():
                    out.append("  ERROR: object is always locked")

    def walk_dir(folder):
        for obj in folder.objectValues():
            unlock_obj(obj)
            if obj.isPrincipiaFolderish:
                walk_dir(obj)

    if self != portal:
        unlock_obj(self)
    walk_dir(self)
    return "<br />\n".join(out)


def objects_stats(self, csv=""):
    if not check_role(self):
        return "You must have a manager role to run this script"
    sep = "<br/>"
    out = []
    as_csv = False
    if csv not in ("", "0", "False", "false"):
        sep = "\n"
        as_csv = True
        out.append("Type\tNumber\tSize (Mb)")
    portal = self.portal_url.getPortalObject()
    brains = portal.portal_catalog.searchResults()
    types = {}
    for brain in brains:
        if brain.portal_type not in types:
            types[brain.portal_type] = {"nb": 0, "size": 0}
        types[brain.portal_type]["nb"] += 1
        types[brain.portal_type]["size"] += tobytes(brain.getObjSize or "0 KB")
    for typ in sorted(types.keys()):
        if as_csv:
            out.append(
                "%s\t%d\t%s"
                % (
                    typ,
                    types[typ]["nb"],
                    fileSize(types[typ]["size"], as_size="M", decimal=",", rm_sz=True),
                )
            )
        else:
            out.append(
                "%s: %d, %s (%s)"
                % (
                    typ,
                    types[typ]["nb"],
                    fileSize(types[typ]["size"], as_size="M"),
                    '<a href="%s/cputils_list_objects?type=%s">+</a>'
                    % (self.absolute_url(), typ),
                )
            )
    return sep.join(out)


def list_objects(self, type):
    if not check_role(self):
        return "You must have a manager role to run this script"
    portal = self.portal_url.getPortalObject()
    brains = portal.portal_catalog.searchResults({"portal_type": type})
    out = []
    for brain in brains:
        obj = brain.getObject()
        url = obj.absolute_url()
        info = "&nbsp;<a href= " + url + "/cputils_object_info>(more info)</a>"
        out.append("%s %s %s %s %s %s" % ("<a href= ", url, ">", url, "</a>", info))
    return "<br/>".join(out)


def reftooltoobjects(self, dochange=""):
    """
        This is usefull with quintagroup.transmogrifier because references
        are not migrated on object (at_references).  But they are
        still in the old imported reference_catalog.zexp.
        Update every objects.at_references depending on the found references
        in the reference_catalog.
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    import logging

    logger = logging.getLogger("CPUtils")
    from Acquisition import aq_base
    from Products.CMFCore.utils import getToolByName

    purl = getToolByName(self, "portal_url")
    portal = purl.getPortalObject()

    out = []
    out.append("<p>You can call the script with following parameters:</p>")
    out.append("-> dochange=1 : to update at_references on objects")
    out.append("by example ...?dochange=1<br/>")
    out.append("<h1>Updated objects</h1>")

    do_change = False
    if dochange not in ("", "0", "False", "false"):
        do_change = True

    logger.info("Updating 'at_references' on every objects...")
    brains = portal.portal_catalog()
    totalBrains = len(brains)

    if totalBrains < 100:
        numberOfSteps = 1
    elif totalBrains < 1000:
        numberOfSteps = 10
    else:
        numberOfSteps = 100

    i = 1
    stepTreshold = round(int(totalBrains / numberOfSteps))
    step = 1
    logger.info("Updating '%d' objects..." % totalBrains)
    refTool = portal.reference_catalog
    changed = False
    for brain in brains:
        if i > stepTreshold:
            i = 1
            logger.info("Step '%d / %d'..." % (step, numberOfSteps))
            step = step + 1
        i = i + 1
        obj = brain.getObject()
        # some elements like Newsletters are not referenceable...
        uobj = aq_base(obj)
        if not refTool.isReferenceable(uobj):
            continue
        at_references = obj._getReferenceAnnotations()
        if at_references.objectValues():
            # at_references already contains references, it seems OK...
            continue
        # Look in the reference_catalog for existing references about obj
        # for every relationships
        for relationship in refTool.getRelationships(obj):
            if not relationship:
                continue
            references = obj.getReferences(relationship)
            for reference in references:
                if not reference:
                    continue
                out.append(
                    "References for relationship '%s' of object at %s' where updated"
                    % (relationship, "/".join(obj.getPhysicalPath()))
                )
                if do_change:
                    changed = True
                    refTool.addReference(
                        obj, reference, relationship, updateReferences=False
                    )
    if changed:
        refTool.refreshCatalog(clear=1)
    logger.info("Done !")
    return "<br />\n".join(out)


def del_bad_portlet(self, dochange="", column="left", portlet=""):
    """
        Delete a Plone3 portlet that cannot more be edited.
        Print the content of the text portlet.
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    import logging

    logger = logging.getLogger("CPUtils")
    from zope.annotation.interfaces import IAnnotations

    import cgi

    out = ["<h1>Deleting a portlet and displaying some attributes</h1>"]
    out.append("You can/must call the script with following parameters:")
    out.append("-> column='right' : to search left (default) or right portlets")
    out.append(
        "-> portlet='xxx' : the id of the portlet to search (can be seen in url when editing it)"
    )
    out.append("-> dochange=1 : to apply change (really delete portlet)")
    out.append("by example ...?portlet=mon portlet&column=right")
    out.append("")

    do_change = False
    if dochange not in ("", "0", "False", "false"):
        do_change = True
    if not portlet:
        out.append("!! You must give the portlet name with 'portlet' parameter")
        return "\n".join(out)

    ann = IAnnotations(self)
    columnkey = "plone.%scolumn" % column
    if "plone.portlets.contextassignments" not in ann:
        out.append("No portlets defined in this context")
    elif columnkey not in ann["plone.portlets.contextassignments"]:
        out.append("Column '%s' not found in portlets definition" % columnkey)
    elif portlet not in ann["plone.portlets.contextassignments"][columnkey]:
        out.append(
            "Portlet '%s' in column '%s' not found in portlets definition"
            % (portlet, column)
        )
    else:
        asg = ann["plone.portlets.contextassignments"][columnkey][portlet]
        if hasattr(asg, "header"):
            out.append("header attribute='%s'\n<br />" % asg.header)
        if hasattr(asg, "text"):
            out.append("text attribute='%s'\n<br />" % cgi.escape(asg.text))
        if do_change:
            del ann["plone.portlets.contextassignments"][columnkey][portlet]
            out.append("portlet '%s' of %s column is deleted" % (portlet, column))
        else:
            out.append(
                "portlet '%s' of %s column will be really deleted with dochange parameter"
                % (portlet, column)
            )
    logger.info("\n".join(out))
    return "<br />\n".join(out)


def clean_provides_for(self, interface_name=None):
    """
        Removed given interface_name from every object providing it...
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    if not interface_name:
        return (
            "You must provide an interface_name argument with the complete interface dotted name (like "
            "'collective.zipfiletransport.utilities.interfaces.IZipFileTransportUtility' for example)"
        )

    brains = self.portal_catalog(object_provides=interface_name)
    if not brains:
        return "No elements provides '%s'" % interface_name

    from zope.component.interface import getInterface
    from zope.interface import noLongerProvides

    out = []
    interface = getInterface("", interface_name)
    out.append(
        "Following object no longer provides '%s' interface :\n" % interface_name
    )

    for brain in brains:
        out.append(brain.getURL())
        obj = brain.getObject()
        noLongerProvides(obj, interface)
        obj.reindexObject()

    import transaction

    transaction.commit()

    return "\n".join(out)


def clean_utilities_for(self, interface_name=None):
    """
        Wipe out Zope for bad leftovers (not completely removed products)
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    if not interface_name:
        return (
            "You must provide an interface_name argument with the complete interface dotted name (like "
            "'collective.zipfiletransport.utilities.interfaces.IZipFileTransportUtility' for example)"
        )

    from zope.component import getSiteManager

    sm = getSiteManager()
    out = []

    # correct adapters
    foundAdapter = False
    correctedAdapters = {}
    for adapter in sm.utilities._adapters[0]:
        if interface_name not in str(adapter):
            correctedAdapters[adapter] = sm.utilities._adapters[0][adapter]
        else:
            foundAdapter = True
    if foundAdapter:
        sm.utilities._adapters[0] = correctedAdapters
        out.append("Corrected adapters")
    else:
        out.append("Interface not found in adapters")

    # correct subscribers
    foundSubscriber = False
    correctedSubscribers = {}
    for subscriber in sm.utilities._subscribers[0]:
        if interface_name not in str(subscriber):
            correctedSubscribers[subscriber] = sm.utilities._subscribers[0][subscriber]
        else:
            foundSubscriber = True
    if foundSubscriber:
        sm.utilities._subscribers[0] = correctedSubscribers
        out.append("Corrected subscribers")
    else:
        out.append("Interface not found in subscribers")

    import transaction

    transaction.commit()

    return "\n".join(out)


def add_subject(self, dochange="", path="", type="", subject=""):
    """
        Search for objects regarding type, path, ... and add the subject.
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    import logging

    logger = logging.getLogger("CPUtils")
    from Products.CMFCore.utils import getToolByName

    import os

    purl = getToolByName(self, "portal_url")
    portal = purl.getPortalObject()
    sitePath = "/".join(portal.getPhysicalPath())

    out = ["<h1>Adding a subject to objects</h1>"]
    out.append("You can/must call the script with following parameters:")
    out.append(
        "-> path='' : path to search in (do not begin with '/'). By default nothing: all site is considered."
    )
    out.append("-> type='' : portal type to search.")
    out.append("-> subject='' : subject to add.")
    out.append("-> dochange=1 : to apply change")
    out.append("by example ...?subject=Motclé&path=/theme1&type=News")
    out.append("")

    do_change = False
    if dochange not in ("", "0", "False", "false"):
        do_change = True
    if not subject:
        out.append("!! You must give the subject name with 'subject' parameter")
        return "<br />\n".join(out)

    kw = {}
    # kw['sort_on'] = 'path'
    if type:
        kw["portal_type"] = type
    if path:
        kw["path"] = os.path.join(sitePath, path)

    # kw['review_state'] = ('private',) #'published'
    # kw['sort_order'] = 'reverse'
    results = portal.portal_catalog.searchResults(kw)
    results = sorted(results, key=lambda obj: obj.getPath())
    out.append("Count of objects:%d" % len(results))
    for brain in results:
        obj = brain.getObject()
        subjects = list(obj.Subject())
        if subject not in subjects:
            subjects.append(subject)
            if do_change:
                obj.setSubject(subjects)
                obj.reindexObject()
                out.append(
                    "%s -> added subject to subjects:'%s'"
                    % (brain.getPath(), "|".join(subjects))
                )
            else:
                out.append(
                    "%s -> will add subject to subjects:'%s'"
                    % (brain.getPath(), "|".join(subjects))
                )
        else:
            out.append(
                "%s -> subject already in subjects:'%s'"
                % (brain.getPath(), "|".join(subjects))
            )
    logger.info("\n".join(out))
    return "<br />\n".join(out)


def list_for_generator(self, tree):
    # Avoiding "Unauthorized: The container has no security assertions." in ZMI Python scripts
    # on LOBTreeItems
    return [elem for elem in tree]


def removeZFT(self):
    if not check_role(self):
        return "You must have a manager role to run this script"
    try:
        from zope.app.component.hooks import setSite
    except ImportError:
        from zope.component.hooks import setSite

    from collective.zipfiletransport.utilities.interfaces import IZipFileTransportUtility
    from zope.component import getSiteManager

    setSite(self)
    sm = getSiteManager()
    util = sm.queryUtility(IZipFileTransportUtility, name="zipfiletransport")
    sm.unregisterUtility(component=None, provided=IZipFileTransportUtility)
    sm.utilities.unsubscribe((), IZipFileTransportUtility)
    del util

    # Even though unregister happened, it probably said it worked but left crap around.
    # Let's clean it up

    # This intclass variable might not be right.  It's going to be the key present below,
    # so you can always find the right InterfaceClass manually and set it accordingly.
    intclass = IZipFileTransportUtility

    try:
        del sm.utilities._adapters[0][intclass]
    except BaseException:
        pass

    try:
        del sm.utilities._subscribers[0][intclass]
    except BaseException:
        pass

    try:
        del sm.utilities._provided[intclass]
    except BaseException:
        pass

    # From here, search for 'Zip' to see if it's gone
    # Each should return -1.  If not, you've done something wrong!
    str(sm.utilities._adapters[0]).find("Zip")
    str(sm.utilities._subscribers[0]).find("Zip")
    str(sm.utilities._provided).find("Zip")
    str(sm.utilities.__bases__[0].__dict__).find("Zip")

    import transaction

    transaction.commit()


def order_folder(self, key="title", reverse="", verbose=""):
    """
        Order items in a folder
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    out = ["<h1>Order a folder</h1>"]
    out.append("You can/must call the script with following parameters:")
    out.append("-> key='' : ordering key (default title).")
    out.append("-> reverse='' : reversing order (default False).")
    out.append("by example ...?key=title&reverse=")
    out.append("")

    do_reverse = False
    if reverse not in ("", "0", "False", "false"):
        do_reverse = True
    do_print = True
    if verbose in ("", "0", "False", "false"):
        do_print = False

    self.orderObjects(key, reverse=do_reverse)
    out.append(
        "Re-ordered by '%s' in %s order" % (key, do_reverse and "reverse" or "normal")
    )

    if do_print:
        return "<br />\n".join(out)
    else:
        return self.REQUEST.RESPONSE.redirect(self.absolute_url())


def move_item(self, delta=-1):
    """
        move an item in an ordered container
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    eid = self.getId()
    folder = self.__parent__
    oldpos = folder.getObjectPosition(eid)
    folder.moveObjectsByDelta(eid, int(delta))
    newpos = folder.getObjectPosition(eid)
    print "%d => %d" % (oldpos, newpos)


def search_users_by_name(self, filter_login="", filter_name="", filter_mail=""):
    """
        search users by login, fullname or email.
    """
    out = ["<strong>Search users </strong>"]
    out.append("You can/must call the script with following parameters:")
    out.append("-> filter_login='' : expression to search in login")
    out.append("-> filter_name=''  : expression to search in fullname")
    out.append("-> filter_mail=''  : expression to search in email")
    out.append(
        "ie. searchAllUsers?filter_login=anuyens,anu&filter_name=André,Patrick&filter_mail=anu,andre,nuyens"
    )
    out.append("")

    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    for user in self.acl_users.searchUsers():
        if user["pluginid"] in ("users", "source_users"):
            user_login = user["login"]
            # for zope user, check only on login
            for filter_value in filter_login.split(","):
                if filter_value and filter_value.upper() in user_login.upper():
                    out.append("Zope, id: %s" % user_login)

    for site in get_all_site_objects(self):
        for member in get_users(site):
            user_login = member.id
            user_fullname = member.getProperty("fullname")
            user_mail = member.getProperty("email")
            for user_prop, filter_value in (
                (user_login, filter_login),
                (user_fullname, filter_name),
                (user_mail, filter_mail),
            ):
                if [
                    i
                    for i in filter_value.split(",")
                    if filter_value and i.upper() in user_prop.upper()
                ]:
                    out.append(
                        "%s, id: %s, mail: %s, fullname: %s"
                        % (
                            "/".join(site.getPhysicalPath()),
                            user_login,
                            user_mail,
                            user_fullname,
                        )
                    )
                    break
    return "<br />\n".join(out)


def move_copy_objects(self, action="move", dest="", doit="", types="", by=50):
    """
        move or copy objects.
    """
    out = ["Move or copy objects"]
    out.append("You can/must call the script with following parameters:")
    out.append("-> action='move' : copy|move")
    out.append("-> dest='' : relative path")
    out.append("-> doit='' : commit flag")
    out.append(
        "-> types='' : filter on those portal types (comma separated without space)"
    )
    out.append("-> by='50' : slice number")
    out.append("ie. move_copy_objects?action=copy&dest=archives")
    out.append("")

    if not check_role(self):
        return "You must have a manager role to run this script"

    if not dest:
        out.append("!! You must give the dest path")
        return "<br />\n".join(out)
    portal = self.portal_url.getPortalObject()
    dest = dest.lstrip("/")
    by = int(by)
    try:
        dest_folder = portal.unrestrictedTraverse(dest)
    except KeyError, e:
        out.append("!! The dest path '%s' isn't correct: %s" % (dest, e))
        return "<br />\n".join(out)
    if not self.plone_utils.isStructuralFolder(dest_folder):
        out.append("!! The dest object '%s' isn't folderish" % (dest_folder))
        return "<br />\n".join(out)
    do_change = False
    if doit not in ("", "0", "False", "false"):
        do_change = True
    params = {}
    if types:
        params["portal_type"] = [typ.strip() for typ in types.split(",")]
    dest_path = dest_folder.absolute_url_path()
    ids = []
    found_types = []
    for obj in self.listFolderContents(contentFilter=params):
        if dest_path.startswith(obj.absolute_url_path()):
            continue
        if obj.portal_type not in found_types:
            found_types.append(obj.portal_type)
        if obj.portal_type not in dest_folder.getLocallyAllowedTypes():
            out.append("Object not allowed: '%s'" % obj)
            continue
        ids.append(obj.getId())
    out.append("\nExisting types: %s" % ", ".join(found_types))
    out.append("Will %s: %s" % (action, ", ".join(ids)))
    while ids:
        pids = ids[0:by]
        ids[0:by] = []
        if action == "move":
            clipboard = self.manage_cutObjects(pids)
        elif action == "copy":
            clipboard = self.manage_copyObjects(pids)
        if do_change:
            dest_folder.manage_pasteObjects(clipboard)
    return "\n".join(out)


def reset_passwords(self, not_for_ids="siteadmin", dochange=""):
    """
        Reset all users passwords
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    portal = self.portal_url.getPortalObject()
    regtool = portal.portal_registration
    out = []
    out.append("call the script followed by needed parameters:")
    out.append(
        "-> not_for_ids=user1|user2  : list of userids exception (default siteadmin)"
    )
    out.append("-> dochange=1")
    change = False
    if dochange not in ("", "0", "False", "false"):
        change = True

    out.append("\nResetting all users passwords")
    exceptions = not_for_ids.strip().split("|")
    out.append("Userids exceptions: '%s'" % ",".join(exceptions))
    users = portal.portal_membership.listMembers()
    out.append("Total users: %d" % len(users))
    out.append("Total exceptions: %d" % len(exceptions))
    intersect = list(set([u.id for u in users]) & set(exceptions))
    out.append("Intersection: %d => %s" % (len(intersect), ",".join(intersect)))
    reset = 0
    for user in users:
        if user.id in exceptions:
            continue
        reset += 1
        if change:
            pw = regtool.generatePassword()
            user.setSecurityProfile(password=pw)
    out.append("Total reset: %d" % reset)
    if change:
        out.append("\nReset really done")
    else:
        out.append("\nReset not really done")
    return "\n".join(out)


def reindex_relations(self):
    """
        Clear the relation catalog (zc.relation.catalog) to fix issues with interfaces that don't
        exist anymore.
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    from z3c.relationfield.event import updateRelations
    from z3c.relationfield.interfaces import IHasRelations
    from zc.relation.interfaces import ICatalog
    from zope.component import getUtility

    rcatalog = getUtility(ICatalog)
    rcatalog.clear()
    brains = self.portal_catalog.searchResults(
        object_provides=IHasRelations.__identifier__
    )
    for brain in brains:
        obj = brain.getObject()
        updateRelations(obj, None)


def mark_last_version(self, product=""):
    """
        Mark a product in pqi as last version installed
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    if not product:
        return (
            "You must give the parameter product with the product name: "
            "mark_last_version?product=Products.Ploneboard"
        )
    pqi = self.portal_quickinstaller
    try:
        prod = pqi.get(product)
        i_v = prod.getInstalledVersion()
        s_v = pqi.getProductVersion(product)
        if i_v != s_v:
            setattr(prod, "installedversion", s_v)
            return "Product version set in pqi: '%s' from '%s' to '%s'" % (
                product,
                i_v,
                s_v,
            )
        else:
            return "Product version in pqi already at last: '%s' '%s'" % (product, i_v)
    except AttributeError, e:
        return "Cannot get product '%s' from portal_quickinstaller: %s" % (product, e)


def resources_order(self, tool="css", output="xml"):
    """
        Print resources order:
        - with output type: 'list', 'xml' (default)
        - with tool: 'css' (default), 'js'
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    portal = self.portal_url.getPortalObject()
    out = []
    out.append(resources_order.__doc__.strip("\n "))
    out.append("Used parameters: tool='%s', output='%s'\n" % (tool, output))
    tools = {
        "css": {"n": "portal_css", "tag": "stylesheet"},
        "js": {"n": "portal_javascripts", "tag": "javascript"},
    }
    if tool not in tools:
        out.append("Bad parameter value for tool")
        return "\n".join(out)

    last = ""
    for i, rsc in enumerate(getattr(portal, tools[tool]["n"]).getResources()):
        if output == "list":
            out.append(
                "%02d: %s: %s" % (i, rsc.getEnabled() and "O" or "-", rsc.getId())
            )
        elif output == "xml":
            out.append(
                '<%s id="%s" insert-after="%s" />\n'
                % (tools[tool]["tag"], rsc.getId(), last)
            )
        last = rsc.getId()

    return "\n".join(out)


def load_site(self, duration="15"):
    """
        Load the site during a specified duration
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    import time

    portal = self.portal_url.getPortalObject()
    infinity = True
    t_end = time.time() + int(duration)
    while infinity:
        for brain in portal.portal_catalog():
            obj = brain.getObject()
            obj
            if time.time() > t_end:
                infinity = False
                break


def dv_images_size(self):
    """
        Return size of documentviewer files
    """
    from plone.app.blob.utils import openBlob
    from zope.annotation.interfaces import IAnnotations

    import os

    sizes = {"large": 0, "normal": 0, "small": 0, "text": 0, "pages": 0, "fmt": ""}
    annot = IAnnotations(self).get("collective.documentviewer", "")
    if (
        not annot
        or not annot.get("successfully_converted")
        or not annot.get("blob_files", None)
    ):
        return sizes
    files = annot.get("blob_files", None)
    keys = files.keys()
    iformat = annot["pdf_image_format"]
    for name in sizes:
        for page in range(1, annot["num_pages"] + 1):
            img = "%s/dump_%d.%s" % (name, page, (name != "text" and iformat or "txt"))
            if img in keys:
                blob = files[img]
                blobfi = openBlob(blob)
                sizes[name] += os.fstat(blobfi.fileno()).st_size
                blobfi.close()
    sizes["fmt"] = iformat
    sizes["pages"] = annot["num_pages"]
    return sizes


def dv_conversion(
    self,
    pt="dmsmainfile,dmsommainfile,dmsappendixfile",
    fmt="jpg",
    change="",
    csv="",
    batch="3000",
):
    """
        Convert files into document viewer images
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    out = []
    out.append("call the script followed by needed parameters:")
    out.append(
        "-> pt=portal_types to search, separated by comma (default dmsmainfile,dmsommainfile,dmsappendixfile)"
    )
    out.append("-> fmt=images format (jpg or png: default jpg)")
    out.append("-> csv=1 export to csv")
    out.append("-> batch=batch number to commit each nth (default 3000)")
    out.append("-> change=1")
    try:
        from collective.documentviewer.convert import runConversion
        from collective.documentviewer.settings import GlobalSettings
    except ImportError:
        out.append("collective.documentviewer not found")
        return "\n".join(out)
    from datetime import datetime

    start = datetime(1973, 02, 12).now()
    import logging

    logger = logging.getLogger("CPUtils dv_conversion")
    commit = int(batch)
    import transaction

    log_list(out, "Starting dv_conversion at %s" % start, logger)
    doit = as_csv = False
    if change == "1":
        doit = True
        gsettings = GlobalSettings(self.portal_url.getPortalObject())
        gsettings.pdf_image_format = fmt
    pts = pt.split(",")
    portal = self.portal_url.getPortalObject()
    where = ""
    crits = {"portal_type": pts}
    if self != portal:
        crits["path"] = "/".join(self.getPhysicalPath())
        where = "in context "
    brains = self.portal_catalog(**crits)
    bl = len(brains)
    log_list(
        out,
        "Searching portal_types '%s' %s: found %d objects" % (pts, where, bl),
        logger,
    )
    if csv == "1":
        as_csv = True
        portal_path = self.portal_url.getPortalPath()
        ppl = len(portal_path)
        log_list(
            out,
            "\nFile,File size,Large size,Normal size,Small size,Text size,Format,Pages",
            logger,
        )
    total = {"orig": 0, "pages": 0, "old_i": 0, "new_i": 0}
    loggerdv = logging.getLogger("collective.documentviewer")
    loggerdv.setLevel(30)
    to_convert = converted = already = 0
    for i, brain in enumerate(brains):
        obj = brain.getObject()
        sizes = dv_images_size(obj)
        try:
            total["orig"] += tobytes(brain.getObjSize)
        except BaseException:
            log_list(
                out, "getObjSize is empty for '%s'" % brain.getURL(), logger, "warn"
            )
        total["old_i"] += sizes["large"] + sizes["normal"] + sizes["small"]
        total["pages"] += sizes["pages"]
        if as_csv:
            log_list(
                out,
                "%s,%d,%d,%d,%d,%d,%s,%s"
                % (
                    brain.getPath()[ppl:],
                    tobytes(brain.getObjSize),
                    sizes["large"],
                    sizes["normal"],
                    sizes["small"],
                    sizes["text"],
                    sizes.get("fmt", ""),
                    sizes.get("pages", ""),
                ),
                logger,
            )

        if sizes["fmt"] == fmt:
            total["new_i"] += sizes["large"] + sizes["normal"] + sizes["small"]
            already += 1
            continue
        to_convert += 1
        if doit:
            ret = runConversion(obj)
            if ret == "failure":
                log_list(
                    out,
                    "Error during conversion of %s" % brain.getURL(),
                    logger,
                    "error",
                )
            else:
                converted += 1
                sizes = dv_images_size(obj)
                total["new_i"] += sizes["large"] + sizes["normal"] + sizes["small"]
                if converted % commit == 0:
                    transaction.commit()
                    log_list(
                        out,
                        "Files: '%d', To convert: '%d', Converted: '%d', Already: '%d', PDF: '%s', "
                        "Pages: '%d', old: '%s', new: '%s'"
                        % (
                            bl,
                            to_convert,
                            converted,
                            already,
                            fileSize(total["orig"], decimal=","),
                            total["pages"],
                            fileSize(total["old_i"], decimal=","),
                            fileSize(total["new_i"], decimal=","),
                        ),
                        logger,
                    )
    loggerdv.setLevel(20)
    if as_csv:
        log_list(
            out,
            "TOTAL,=somme(B2:B{0})/1048576,=somme(C2:C{0})/1048576,=somme(D2:D{0})/1048576,"
            "=somme(E2:E{0})/1048576,=somme(F2:F{0})/1048576,,=somme(H2:H{0})".format(
                bl + 1
            ),
        )

    end = datetime(1973, 02, 12).now()
    delta = end - start
    log_list(out, "Finishing dv_conversion, duration %s" % delta, logger)
    log_list(
        out,
        "Files: '%d', To convert: '%d', Converted: '%d', Already: '%d', PDF: '%s', "
        "Pages: '%d', old: '%s', new: '%s'"
        % (
            bl,
            to_convert,
            converted,
            already,
            fileSize(total["orig"], decimal=","),
            total["pages"],
            fileSize(total["old_i"], decimal=","),
            fileSize(total["new_i"], decimal=","),
        ),
        logger,
    )
    return "\n".join(out)


def remove_empty_related_items(self):
    """
        Remove related items which do not exists anymore (bugs with plone.app.contenttypes on Plone 4.3)
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    old_related = len(self.relatedItems)
    self.relatedItems = [rel for rel in self.relatedItems if not rel.isBroken()]
    new_related = len(self.relatedItems)
    import transaction

    transaction.commit()
    return "This object has now {0} related items (before: {1}".format(
        new_related, old_related
    )


def creators(self, value="", replace="1", add="-1", recursive="", dochange=""):
    """
        Change creators metadata.
    """
    if not check_role(self):
        return "You must have a manager role to run this script"
    from Products.CMFPlone.utils import base_hasattr

    out = ["<strong>Creators change</strong>"]
    out.append("You can/must call the script with following parameters:")
    out.append("-> value='' : creator name. Mandatory param")
    out.append("-> replace='1' : if not empty, replace creators value. Default=1")
    out.append("-> add='0' : index insertion value in creators list. Default=0")
    out.append("-> recursive=''  : do it recursively. Default=empty")
    out.append("-> dochange=''  : apply changes. Default=empty")
    out.append("ie. cputils_creators?value=sgeulette&replace=&add=0")
    out.append("")
    sep = "\n<br />"
    users = get_users(self, obj=False)
    if not value:
        out.append("!! value is mandatory")
        return sep.join(out)
    values = [v.strip() for v in value.split(",")]
    for val in values:
        if val not in users:
            out.append("!! value '%s' is not a user" % val)
            return sep.join(out)
    change = False
    if dochange not in ("", "0", "False", "false"):
        change = True
    new_i = int(add)

    def set_creators(obj):
        if not base_hasattr(obj, "Creators"):
            return
        cur_val = list(obj.Creators())
        mod = False
        if replace == "1":
            if cur_val != values:
                cur_val = values
                mod = True
        else:
            for val in reversed(values):
                if val in cur_val:
                    i = cur_val.index(val)
                    if i == new_i or (
                        new_i >= len(cur_val) - 1 and i == len(cur_val) - 1
                    ):
                        continue  # right place
                    else:
                        cur_val.remove(val)
                mod = True
                cur_val.insert(new_i, val)
        if mod:
            out.append(
                "New val set '%s' for <a href='%s'>%s</a>"
                % (cur_val, obj.absolute_url(), obj.Title())
            )
            if change:
                obj.setCreators(tuple(cur_val))
                obj.reindexObject(["Creator", "listCreators"])
        else:
            out.append(
                "Old val kept '%s' for <a href='%s'>%s</a>"
                % (cur_val, obj.absolute_url(), obj.Title())
            )

    if recursive:
        pc = self.portal_catalog
        for brain in pc(
            path={"query": "/".join(self.getPhysicalPath()), "depth": 2}, sort_on="path"
        ):
            set_creators(brain._unrestrictedGetObject())
    else:
        set_creators(self)
    return sep.join(out)


def change_uuid(self, recursive="", dochange=""):
    """
        Change uuid values.
    """
    if not check_role(self):
        return "You must have a manager role to run this script"
    from plone.uuid.interfaces import ATTRIBUTE_NAME
    from plone.uuid.interfaces import IUUID
    from plone.uuid.interfaces import IUUIDGenerator
    from Products.CMFPlone.utils import base_hasattr
    from zope.component import getUtility

    generator = getUtility(IUUIDGenerator)

    out = ["<strong>Creators change</strong>"]
    out.append("You can/must call the script with following parameters:")
    out.append("-> recursive=''  : do it recursively. Default=empty")
    out.append("-> dochange=''  : apply changes. Default=empty")
    out.append("ie. cputils_change_uuid?recursive=1")
    out.append("")
    sep = "\n<br />"

    change = False
    if dochange not in ("", "0", "False", "false"):
        change = True

    def set_uuid(obj):
        new_uuid = generator()
        out.append(
            "%s, old='%s', new='%s'"
            % ("/".join(obj.getPhysicalPath()), IUUID(obj), new_uuid)
        )
        if change:
            if base_hasattr(obj, ATTRIBUTE_NAME):
                setattr(obj, ATTRIBUTE_NAME, new_uuid)
            else:
                obj._setUID(new_uuid)
            obj.reindexObject(idxs=["UID"])

    if recursive:
        pc = self.portal_catalog
        for brain in pc(path="/".join(self.getPhysicalPath()), sort_on="path"):
            set_uuid(brain._unrestrictedGetObject())
    else:
        set_uuid(self)

    return sep.join(out)


def correct_intids(self, dochange=""):
    """
        Correct intids key references after a zodb change: mount point to main.
        Not well working !!!!!!!
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    from zope.component import getUtility
    from zope.intid.interfaces import IIntIds
    from zope.keyreference.interfaces import IKeyReference

    change = False
    if dochange not in ("", "0", "False", "false"):
        change = True
    intids = getUtility(IIntIds)
    items = intids.items()
    ilen = len(intids.ids)
    rlen = len(intids.refs)
    wlen = len(items)
    errors = 0
    for (iid, keyref) in items:
        obj = keyref.object
        key = IKeyReference(obj)
        if key not in intids.ids:
            errors += 1
            if change:
                # remove old keyref
                del intids.ids[keyref]
                # add new one
                intids.ids[key] = iid
                # correct refs
                intids.refs[iid] = key

    return "ids bef=%d, refs bef=%d, walked=%d, errors=%d, ids aft=%d, refs aft=%d" % (
        ilen,
        rlen,
        wlen,
        errors,
        len(intids.ids),
        len(intids.refs),
    )


def register_intid(self, dochange=""):
    """
        Register intid if object is not well registered.
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    from zope.component import getUtility
    from zope.intid.interfaces import IIntIds

    out = ["Check intid registration for '%s'" % self.absolute_url()]
    intids = getUtility(IIntIds)
    try:
        out.append("obj already registered with intid '%s'" % intids.getId(self))
    except KeyError:
        out.append("!! Missing intid !!")
        if dochange == "1":
            intids.register(self)
            out.append("obj now registered with intid '%s'" % intids.getId(self))
    return "\n<br />".join(out)


def check_all_catalog_intids(self, dochange=""):
    """
        Check all catalog intids for registration.
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    from zope.component import getUtility
    from zope.intid.interfaces import IIntIds

    out = ["Check all catalog intids for registration."]
    intids = getUtility(IIntIds)
    portal_types = []
    number_of_cataloged_objects = 0
    number_of_registered_intid = 0
    number_of_missing_intid = 0
    for brain in self.portal_catalog():
        number_of_cataloged_objects += 1
        obj = brain.getObject()
        try:
            out.append("obj already registered with intid {}".format(intids.getId(obj)))
            number_of_registered_intid += 1
        except KeyError:
            number_of_missing_intid += 1
            portal_type = obj.portal_type
            if portal_type not in portal_types:
                portal_types.append(portal_type)
            out.append(
                "!! Missing intid !! portal_type : {}, absolute_url : {}".format(
                    portal_type, obj.absolute_url()
                )
            )
            if dochange == "1":
                intids.register(obj)
                out.append("obj now registered with intid '%s'" % intids.getId(obj))
    resume = (
        "<br />number of cataloged objects : {}; number of registered intid : {}; number of missing intid : {};"
        "\n<br />portal_types : {}".format(
            number_of_cataloged_objects,
            number_of_registered_intid,
            number_of_missing_intid,
            portal_types,
        )
    )
    return resume + "\n<br />".join(out)


def check_blobs(self, delete=""):
    """
        Check blobs for poskeyerrors, limited to cataloged object
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    delt = False
    if delete not in ("", "0", "False", "false"):
        delt = True
    ret = []

    from datetime import datetime
    from plone.app.blob.subtypes.file import ExtensionBlobField
    from plone.dexterity.content import DexterityContent
    from plone.namedfile.interfaces import INamedFile
    from Products.Archetypes.Field import FileField
    from Products.Archetypes.interfaces import IBaseContent
    from Products.CMFCore.utils import getToolByName
    from Products.CMFPlone.utils import base_hasattr
    from ZODB.POSException import POSKeyError

    portal = getToolByName(self, "portal_url").getPortalObject()
    log_list(ret, "Starting check_blobs at %s" % datetime(1973, 02, 12).now())

    blob_attrs = {}
    # get all files attributes
    for typ in portal.portal_types:
        brains = portal.portal_catalog(portal_type=typ)
        if not brains:
            continue
        obj = brains[0].getObject()
        if IBaseContent.providedBy(obj):
            schema = obj.Schema()
            for field in schema.fields():
                if isinstance(field, FileField) or isinstance(
                    field, ExtensionBlobField
                ):
                    value = field.getAccessor(obj)()
                    if not base_hasattr(value, "getSize"):
                        continue
                    if typ not in blob_attrs:
                        blob_attrs[typ] = {"t": "at", "at": []}
                    blob_attrs[typ]["at"].append(field.getName())
        elif isinstance(obj, DexterityContent):
            # Iterate through all Python object attributes
            for key, value in obj.__dict__.items():
                if not key.startswith("_"):
                    if INamedFile.providedBy(value):
                        if typ not in blob_attrs:
                            blob_attrs[typ] = {"t": "dx", "at": []}
                        blob_attrs[typ]["at"].append(key)
    log_list(ret, "Blob attributes: %s" % str(blob_attrs))

    for typ in blob_attrs:
        for brain in portal.portal_catalog(portal_type=typ):
            obj = brain.getObject()
            for attr in blob_attrs[typ]["at"]:
                try:
                    if blob_attrs[typ]["t"] == "dx":
                        val = getattr(obj, attr)
                        val.data
                    else:
                        val = obj.getField(attr).get(obj)
                        val.getSize()
                except (POSKeyError, SystemError):
                    log_list(
                        ret, "Found damaged object %s on %s" % (typ, obj.absolute_url())
                    )
                if delt:
                    parent = obj.aq_parent
                    log_list(ret, "  => will be deleted")
                    parent.manage_delObjects([obj.getId()])

    log_list(ret, "Finished check_blobs at %s" % datetime(1973, 02, 12).now())
    return "\n".join(ret)


def check_blobs_slow(self, delete=""):
    """
        Check blobs for poskeyerrors
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    delt = False
    if delete not in ("", "0", "False", "false"):
        delt = True
    ret = []

    from datetime import datetime
    from plone.dexterity.content import DexterityContent
    from plone.namedfile.interfaces import INamedFile
    from Products.Archetypes.Field import FileField
    from Products.Archetypes.interfaces import IBaseContent
    from Products.CMFCore.interfaces import IFolderish
    from Products.CMFCore.utils import getToolByName
    from ZODB.POSException import POSKeyError

    portal = getToolByName(self, "portal_url").getPortalObject()
    start = datetime(1973, 02, 12).now()
    log_list(ret, "Starting check_blobs at %s" % start)

    def check_at_blobs(context):
        """ Archetypes content checker. Return True if purge needed """
        if IBaseContent.providedBy(context):
            schema = context.Schema()
            for field in schema.fields():
                id = field.getName()
                if isinstance(field, FileField):
                    try:
                        field.get_size(context)
                    except POSKeyError:
                        log_list(
                            ret,
                            "Found damaged AT FileField %s on %s"
                            % (id, context.absolute_url()),
                        )
                        return True
        return False

    def check_dexterity_blobs(context):
        """ Check Dexterity content for damaged blob fields. Return True if purge needed """
        # Assume dexterity content inherits from Item
        if isinstance(context, DexterityContent):
            # Iterate through all Python object attributes
            # XXX: Might be smarter to use zope.schema introspection here?
            for key, value in context.__dict__.items():
                # Ignore non-contentish attributes to speed up us a bit
                if not key.startswith("_"):
                    if INamedFile.providedBy(value):
                        try:
                            value.getSize()
                        except POSKeyError:
                            log_list(
                                ret,
                                "Found damaged Dexterity plone.app.NamedFile %s on %s"
                                % (key, context.absolute_url()),
                            )
                            return True
        return False

    def fix_blobs(context, delete=False):
        """
        Iterate through the object variables and see if they are blob fields
        and if the field loading fails then poof
        """
        if check_at_blobs(context) or check_dexterity_blobs(context):
            log_list(ret, "Bad blobs found on %s" % context.absolute_url())
            if delete:
                parent = context.aq_parent
                log_list(ret, "  => will be deleted")
                parent.manage_delObjects([context.getId()])

    def recurse(tree, delete=False):
        """ Walk through all the content on a Plone site """
        for id, child in tree.contentItems():

            fix_blobs(child, delete=delete)

            if IFolderish.providedBy(child):
                recurse(child, delete=delete)

    recurse(portal, delete=delt)
    log_list(ret, "Finished check_blobs at %s" % datetime(1973, 02, 12).now())
    return "\n".join(ret)


def del_objects(self, doit="", types="", linki="1"):
    from plone import api

    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    # person,held_position
    out = ["<strong>Objects deletion following types search in context path</strong>"]
    out.append("You can/must call the script with following parameters:")
    out.append("-> types=''  : portal_types (separated by ,). Default=empty.")
    out.append(
        "-> linki=''  : link integrity check. Default=1. "
        "Possible values can be '', '0', 'False', 'false' or '1'"
    )
    out.append("-> doit=''  : apply changes if 1. Default=empty")
    out.append("ie. cputils_del_objects?types=Document,Folder&linki=0&doit=1")
    out.append("")

    ptypes = [p.strip() for p in types.split(",")]
    lk = False
    if linki not in ("", "0", "False", "false"):
        lk = True
    out.append("Given parameters:")
    out.append("Types: %s" % ptypes)
    out.append("Link integrity: %s" % lk)
    out.append("Apply: %s" % doit)
    out.append("")
    sep = "\n<br />"

    # only valid for plone < 5 !!!! otherwise use linkintegrity/utils.py
    pp = api.portal.get_tool("portal_properties")
    livalue = pp.site_properties.enable_link_integrity_checks
    if livalue != lk:
        pp.site_properties.enable_link_integrity_checks = lk

    crit = {"portal_type": ptypes}
    # crit.update({'created': {'query': datetime.strptime('20211213', '%Y%m%d'), 'range': 'min'}})
    for brain in api.content.find(
        context=self, sort_on="path", sort_order="ascending", **crit
    ):
        # if brain.internal_reference_no <= 'E13123': continue
        obj = brain.getObject()
        out.append(
            '<a href="%s">%s &nbsp;=>&nbsp; "%s"</a>'
            % (brain.getURL(), brain.getPath(), brain.Title)
        )
        if doit == "1":
            api.content.delete(obj=obj, check_linkintegrity=False)

    if livalue != lk:
        pp.site_properties.enable_link_integrity_checks = livalue
    return sep.join(out)


def del_object(self, doit="", linki="1"):
    from plone import api

    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    out = ["<strong>Object deletion</strong>"]
    out.append("You can/must call the script with following parameters:")
    out.append("-> linki=''  : link integrity check. Default=1")
    out.append("-> doit=''  : apply changes if 1. Default=empty")
    out.append("ie. cputils_del_objects?linki=0&doit=1")
    out.append("")
    sep = "\n<br />"
    # TODO add option to by pass subscribers with container._delObject(id, suppress_events=True)
    for brain in api.content.find(context=self, sort_on="path"):
        obj = brain.getObject()
        out.append(u"<span>{}</span>, {}".format(brain.getPath(), object_link(obj)))
        if doit == "1":
            api.content.delete(obj=self, check_linkintegrity=(linki == "1"))
    return sep.join(out)


def set_attr(self, attr="", value="", typ="str"):
    """
        Set attribute on context.
        Usefull to change creation_date by example
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    from cgi import escape
    from Products.CMFPlone.utils import safe_hasattr

    good_types = ["str", "int", "list", "DateTime", "unicode", "datetime", "None"]

    sep = "\n<br />"
    out = ["<h2>You can/must call the script with following parameters:</h2>",
           "-> attr=''  : attribute name.",
           "-> value=''  : value to set.",
           "-> typ=''  : value type. Can be %s. Default='str'" % ", ".join(["'%s'" % t for t in good_types]),
           "-> Example: ?attr=creation_date&value=2017-10-13 9:00 GMT%2B1&typ=DateTime<br />"
           "-> Example: ?attr=_plone.uuid&value=xxx<br />"
    ]
    if not attr:
        out.append("attr parameter is mandatory !")
        return sep.join(out)
    if not safe_hasattr(self, attr):
        out.append("Attr '%s' doesn't exist !" % attr)
        return sep.join(out)
    if not value:
        old_val = getattr(self, attr)
        out.append(u"Current value type={}, value='{}'".format(escape(str(type(old_val))), old_val))
        out.append("value parameter is mandatory !")
        return sep.join(out)
    if typ not in good_types:
        out.append("Given typ '%s' not in good types !" % typ)
        return sep.join(out)

    new_val = value
    try:
        if typ == "int":
            new_val = int(value)
        elif typ == "list":
            import json
            new_val = json.loads(value)
        elif typ == "unicode":
            from Products.CMFPlone.utils import safe_unicode
            new_val = safe_unicode(value)
        elif typ == "DateTime":
            from DateTime import DateTime
            new_val = DateTime(value)  # example '2017-10-13 9:00 GMT%2B1'  %2B = '+'
        elif typ == "datetime":
            from datetime import datetime

            import re
            dt = map(int, filter(None, re.split(r"[\- /\\:]+", value)))
            new_val = datetime(*dt)  # example '2017-10-13 9:00'
        elif typ == "None":
            new_val = None
    except Exception as msg:
        out.append("Cannot cast value type to '%s': '%s'" % (typ, msg))
        return sep.join(out)

    old_val = getattr(self, attr)
    setattr(self, attr, new_val)
    self.reindexObject()
    out.append("Attr '%s' set to '%s' (from '%s')" % (attr, new_val, old_val))
    return sep.join(out)


def uid(self):
    """ Display uid value """
    if not check_role(self):
        return "You must have a manager role to run this script"
    try:
        return self.UID()
    except Exception, msg:
        return msg


def obj_from_uid(self, uid=''):
    """ Get object from uid value """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    if not uid:
        return "uid parameter is mandatory !"
    obj = uuidToObject(uid)
    if obj is None:
        return "No object found for uid '%s'" % uid
    return object_link(obj)


def relation_infos(rel):
    """ utils method: not to be called as external method """
    return {
        "br": rel.isBroken(),
        "fr_i": rel.from_id,
        "fr_o": rel.from_object,
        "fr_a": rel.from_attribute,
        "fr_p": rel.from_path,
        "to_i": rel.to_id,
        "to_o": rel.to_object,
        "to_p": rel.to_path,
    }
    # rel.from_interfaces, rel.from_interfaces_flattened, rel.to_interfaces, rel.to_interfaces_flattened


def check_relations(self):
    """
        check zc.relations problems
        see collective.contact.core.upgrades.upgrades.reindex_relations
        see from z3c.relationfield.event import updateRelations
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    from zc.relation.interfaces import ICatalog
    from zope.app.intid.interfaces import IIntIds
    from zope.component import getUtility

    intids = getUtility(IIntIds)
    rels = getUtility(ICatalog)
    out = ["check_intids\n"]
    relations = list(rels.findRelations())
    for rel in relations:
        if not rel.from_id or not intids.queryObject(rel.from_id, False):
            log_list(out, "Missing from_id %s" % relation_infos(rel))
            # rels.unindex(rel)
        elif not rel.to_id or not intids.queryObject(rel.to_id, False):
            log_list(out, "Missing to_id %s" % relation_infos(rel))
        elif not rel.from_object or not intids.queryId(rel.from_object, False):
            log_list(out, "Missing from_object %s" % relation_infos(rel))
        elif not rel.to_object or not intids.queryId(rel.to_object, False):
            log_list(out, "Missing to_object %s" % relation_infos(rel))
    if len(out) == 1:
        out.append("No problem found")
    return "\n".join(out)


def show_object_relations(self):
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    from zc.relation.interfaces import ICatalog  # noqa
    from zope.component import queryUtility
    from zope.intid.interfaces import IIntIds

    intids = queryUtility(IIntIds)
    catalog = queryUtility(ICatalog)
    out = []
    for way in ("from", "to"):
        out.append("Way = {}".format(way))
        query = {"{}_id".format(way): intids.getId(self)}
        rels = list(catalog.findRelations(query))
        for rel in rels:
            out.append(str(relation_infos(rel)))
    return "\n".join(out)


def batch_remove_generated_previews(objs):
    """ Remove document viewer generated previews for a list of objects or brains """
    for obj in objs:
        remove_generated_previews(obj)


def remove_generated_previews(obj):
    """ Remove document viewer generated previews for an object or brain """
    from zope.annotation import IAnnotations

    if hasattr(obj, "getObject"):
        obj = obj.getObject()
    annotations = IAnnotations(obj)
    if "collective.documentviewer" in annotations:
        annotations.pop("collective.documentviewer", {})


def clear_completed_async_jobs(self):
    """ Remove plone.app.async jobs that are completed, i.e. success or failure.
        Does not remove jobs still in flight """
    from plone.app.async.interfaces import IAsyncDatabase
    from Products.CMFCore.interfaces import ISiteRoot
    from zc.async.interfaces import KEY
    from zope.component import getUtility

    db = getUtility(IAsyncDatabase)
    main_conn = getUtility(ISiteRoot)._p_jar
    async_conn = main_conn.get_connection(db.database_name)
    queue = async_conn.root()[KEY]['']
    for da in queue.dispatchers.values():
        for agent in da.values():
            agent.completed.clear()
