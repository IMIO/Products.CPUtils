# -*- coding: utf-8 -*-
#utilities

def search_users(self):
    from Products.CMFCore.utils import getToolByName
    portal = getToolByName(self, "portal_url").getPortalObject() 
    user_ids = []
    for user in portal.acl_users.searchUsers():
        if user['pluginid'] == 'source_users':
            user_ids.append(user['userid'])
    return user_ids

def check_role(self, role='Manager', context=None):
    from Products.CMFCore.utils import getToolByName
    pms = getToolByName(self, 'portal_membership')
    return pms.getAuthenticatedMember().has_role(role, context)

def check_zope_admin():
    from AccessControl.SecurityManagement import getSecurityManager
    user = getSecurityManager().getUser()
    if user.has_role('Manager') and user.__module__ == 'Products.PluggableAuthService.PropertiedUser':
        return True
    return False

def fileSize(nb):
    sizeletter = {1:'k', 2:'M', 3:'G', 4:'T'}
    for x in range(1,4):
        quot = nb//1024**x
        if quot < 1024:
            break
    return "%.1f%s"%(float(nb)/1024**x,sizeletter[x])

def get_all_site_objects(self):
    allSiteObj = []
    for objid in self.objectIds(('Plone Site', 'Folder')):
        obj = getattr(self, objid)
        if obj.meta_type == 'Folder':
            for sobjid in obj.objectIds('Plone Site'):
                sobj = getattr(obj, sobjid)
                allSiteObj.append(sobj)
        elif obj.meta_type == 'Plone Site':
            allSiteObj.append(obj)
    return allSiteObj

def sendmail(self, mfrom='', to='', body='', subject='', cc='', bcc=''):
    """
        send a mail
    """
    from Products.CMFCore.utils import getToolByName
    from Products.CPUtils.config import PLONE_VERSION
    from Products.CMFPlone.utils import safe_unicode
    import email.Message
    import email.Utils
    from email.Header import Header
    portal = getToolByName(self, 'portal_url').getPortalObject()

    mailMsg=email.Message.Message()
    mailMsg["To"]=to
    mailMsg["From"]=mfrom
    mailMsg["CC"]=cc
    mailMsg["BCC"]=bcc
    mailMsg["Subject"]=str(Header(safe_unicode(subject), 'utf-8'))
    mailMsg["Date"]=email.Utils.formatdate(localtime=1)
    mailMsg["Message-ID"]=email.Utils.make_msgid()
    mailMsg["Mime-version"]="1.0"
    mailMsg["Content-type"]="text/plain"
    mailMsg.set_payload(safe_unicode(body).encode('utf-8'), 'utf-8')
    mailMsg.epilogue="\n" # To ensure that message ends with newline
    mail_host = getattr(portal, 'MailHost', None)
    try:
        if PLONE_VERSION.startswith('4.'):
            return mail_host.send(mailMsg, mto=to, mfrom=mfrom, subject=subject)
        else:
            return mail_host.secureSend(mailMsg, to, mfrom, subject=subject)
    except Exception, msg:
        return msg

###############################################################################

def install(self):
    """
        Install cputils methods where the user is (root of zope?)
    """
    from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    methods = []
    for method in ('cpdb', 'object_info', 'audit_catalog', 'change_user_properties', 'configure_fckeditor', 'list_users', 'store_user_properties', 'load_user_properties', 'recreate_users_groups', 'sync_properties','send_adminMail','install_plone_product','change_authentication_plugins','list_portlets','copy_image_attribute','desactivate_base2dom', 'rename_long_ids', 'list_newsletter_users', 'zmi'):
        method_name = 'cputils_'+method
        if not hasattr(self.aq_inner.aq_explicit, method_name):
            #without aq_explicit, if the id exists at a higher level, it is found !
            manage_addExternalMethod(self, method_name, '', 'CPUtils.utils', method)
            methods.append(method_name)
    return "<div>Those methods have been added: %s</div>"%('<br />'.join(methods))

###############################################################################

def pack_db(self, days=0):
    """
        pack a db of the zope instance
    """
    out = []
# The user running this via urllib is not manager !!!!
#    if not check_role(self):
#        return "You must have a manager role to run this script"
#    import pdb; pdb.set_trace()
    import time
    t=time.time()-days*86400
    db=self._p_jar.db()
    sz_bef = db.getSize()
    t=db.pack(t)
    sz_aft = db.getSize()
    out.append("Size %s => %s"%(fileSize(sz_bef),fileSize(sz_aft)))
    out.append("well packed")
    return ', '.join(out)

###############################################################################

def cpdb(self):
    """
        run pdb on current context
    """
    if not check_zope_admin():
        return "You must have a zope manager to run this script"
    import pdb
    pdb.set_trace()

###############################################################################

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
        purl = getToolByName(self, 'portal_url')
        wtool = getToolByName(self, 'portal_workflow')
        putils = getToolByName(self, "plone_utils")
#        out.append("portal path='%s'" % purl.getPortalPath())
        out.append("current object path='/%s'" % '/'.join(purl.getRelativeContentPath(self)))
        out.append("current object id='%s'" % self.getId())
        out.append("current object portal type/class='%s'/'%s'" % (self.getPortalTypeName(),self.meta_type))
        out.append("is folderish='%s'" % self.isPrincipiaFolderish)
        out.append("creator='%s'" % self.Creator())
        workflow = False
#        import pdb; pdb.set_trace()
        try:
            workflows = [wfw.getId() for wfw in wtool.getWorkflowsFor(self)]
            state = wtool.getInfoFor(self, 'review_state')
            transitions = ';'.join([trans['name'] for trans in wtool.getTransitionsFor(self)])
            workflow = True
        except WorkflowException:
            workflows = ['-']
            state = '-'
            transitions = '-'
        out.append("\nAbout workflows:")
        out.append("> workflows='%s'" % ';'.join(workflows))
        out.append("> state='%s'" % state)
        out.append("> transitions='%s'" % transitions)
        if workflow:
            for wfid in workflows:
                out.append("> Permissions info for state '%s' in workflow '%s'"%(state, wfid))
                wf = wtool.getWorkflowById(wfid)
                if hasattr(wf.states, state):
                    st = getattr(wf.states, state)
                    permissions = st.getManagedPermissions()
                    if permissions:
                        for permission in permissions:
                            dic = st.getPermissionInfo(permission)
                            out.append("\t'%s' for '%s', acquired=%s"%(permission,', '.join(dic['roles']),dic['acquired']))
                    else:
                        out.append('\tno permissions redefined on this state !')
        out.append("\nAbout local roles:")
        out.append("> acquisition set='%s'"%putils.isLocalRoleAcquired(self))
        localroles = self.get_local_roles()
        if len(localroles):
            out.append('> local roles :')
        else:
            out.append('> local roles : Nothing defined !')
        for principalId, lr in localroles:
            out.append("\t'%s' has roles '%s'"%(principalId, ';'.join(lr)))
        inhlocalroles = putils.getInheritedLocalRoles(self)
        if len(inhlocalroles):
            out.append('> inherited local roles :')
        else:
            out.append('> inherited local roles : Nothing defined !')
        for principalId, lr, pType, pId in inhlocalroles:
             out.append("\t%s '%s' has roles '%s'"%(pType, principalId, ';'.join(lr)))
    except Exception, msg:
        out.append("! EXCEPTION !:%s"%msg)
    return '\n'.join(out)

###############################################################################

def audit_catalog(self):
    from Products.CMFCore.utils import getToolByName
    if not check_role(self):
        return "You must have a manager role to run this script"

    portal_url = getToolByName(self, "portal_url")
    portal = portal_url.getPortalObject()

    kw = {}
    #kw['portal_type'] = ('Document','Link','Image','File','Folder','Large Plone Folder','Wrapper','Topic')
    #kw['review_state'] = ('private',) #'published'
    #kw['path'] = '/' # '/'.join(context.getPhysicalPath())
    #kw['sort_on'] = 'created'
    #kw['sort_order'] = 'reverse'

    results = portal.portal_catalog.searchResults(kw)

    header = """<h1>RESULTATS DE LA RECHERCHE</h1> <p>Recherche dans : %s</p> <p>Nombre d'elements trouves : %d </p> """ % ('/',len(results))
    out =[header]

    res = []
    out.append("""%s : %s : %s""" % ('portal_type', 'getObjSize', 'url'))
    for r in results :
        res.append("%s;%s;%s;%s" % (r.portal_type, r.getObjSize, r.getURL()+'/view', r.getURL()+'/view'))

    def sortBySize(row1, row2):
        size1 = float(row1.split(';')[1][:-3])
        size2 = float(row2.split(';')[1][:-3])
        #reverse order
        return cmp(size1, size2)
    res.sort(sortBySize, reverse=True)

    for row in res :
        (part1,part2,part3,part4) = row.split(';')
        out.append("""%s : %s : <a href="%s">%s</a>""" % (part1, part2, part3, part4))

    out.append("<br />FIN")
    return '<br />'.join(out)

###############################################################################

def delete_subscribers(self, delete=False):
    """
        delete inactive subscribers (maybe robots) of PloneGazette.
        script to be run on the subscriber's folder context
    """
    if not check_role(self):
        return "You must have a manager role to run this script"
    ids = []
    out = ['<h1>Inactive subscribers</h1>']
    for obj in self.objectValues():
        if obj.meta_type == 'Subscriber' and not obj.active:
            out.append(obj.Title())
            ids.append(obj.getId())
    if delete:
        self.manage_delObjects(ids)
    return '<br />'.join(out)

###############################################################################

def delete_users(self, delete=False):
    """
        delete users added by robots.
    """
    if not check_role(self):
        return "You must have a manager role to run this script"
    from Products.CMFCore.utils import getToolByName
    portal = getToolByName(self, "portal_url").getPortalObject()
    out = ['<h1>all Users</h1>']
    i=0
    for u in search_users(self):
        i += 1
    #  if i >100:
    #    break
        member = portal.portal_membership.getMemberById(u)
        email = member.getProperty('email')
        if email.endswith('.com') and not ( email.endswith('gmail.com') or email.endswith('hotmail.com')) :
            out.append("<span>%s, %s, deleted</span>"%(u,email))
            if delete:
                portal.portal_membership.deleteMembers([u], delete_memberareas=1, delete_localroles=0)
        else:
            out.append("<span>%s, %s, kept</span>"%(u,email))
    return '<br/>'.join(out)

###############################################################################

def change_user_properties(self, kw='', dochange=''):
    """
        change user properties with parameter like
        kw=wysiwyg_editor:FCKeditor|nationalregister=00000000097
    """
    if not check_role(self):
        return "You must have a manager role to run this script"
    def return_properties(dic, member):
        ret = ''
        for key in dic.keys():
            if member.hasProperty(key):
                ret += "%s='%s',"%(key, member.getProperty(key))
            else:
                ret += "%s not found,"%(key)
        return ret

    from Products.CMFCore.utils import getToolByName
    portal = getToolByName(self, "portal_url").getPortalObject()
    out = []
    if not kw:
        #out.append("available properties:%s"%portal.portal_memberdata.propertyItems())
        out.append("call the script followed by needed parameters:")
        out.append("-> kw=propertyname1:value1|propertyname2:value2")
        out.append("-> dochange=1")
        out.append("by example ...?kw=wysiwyg_editor:FCKeditor|nationalregister=00000000097&dochange=1<br/>")

    out.append("given keyword parameters:%s"%kw)
    dic = {}
    for tup in kw.split('|'):
        keyvalue = tup.split(':')
        if len(keyvalue)==2:
            (key, value) = keyvalue
            if value == 'True':
                value = True
            elif value == 'False':
                value = False
            dic[key] = value
        elif tup:
            out.append("problem in param '%s'"%tup)
    out.append("build dictionary=%s<br/>"%dic)

    out.append('<h2>all Users</h2>')
    change_property=False
    if dochange not in ('', '0', 'False', 'false'):
        change_property=True
    for u in search_users(self):
        member = portal.portal_membership.getMemberById(u)
        out.append("<br/>USER:'%s'"%(u))
        #out.append("->  old properties=%s"%portal.portal_membership.getMemberInfo(memberId=u))
        #display not all properties
        out.append("=>  all properties: %s"%return_properties(dict(portal.portal_memberdata.propertyItems()), member))
        if len(dic):
            out.append("->  old properties: %s"%return_properties(dic, member))
            if change_property:
                member.setMemberProperties(dic)
                out.append("->  new properties: %s"%return_properties(dic, member))
    return '<br/>'.join(out)

###############################################################################

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

    #import pdb; pdb.set_trace()
    if 'users_properties' not in target_dir.objectIds():
        self.manage_addDTMLDocument(id='users_properties', title='All users properties')
        out.append("Document '%s/users_properties' added"%'/'.join(target_dir.getPhysicalPath()))

    properties_names = dict(portal.portal_memberdata.propertyItems()).keys()
    properties_names.sort()
#    skipped_properties = ['description', ]
#    properties_names = [name for name in properties_names if name not in skipped_properties]
    txt.append('Count\tUser\t'+'\t'.join(properties_names))
#    userids = [ud['userid'] for ud in search_users(self)]
    count = 1
    for user in search_users(self):
        out.append("Current member '%s'"%(user))
        if dic['pluginid'] != 'source_users':
            #out.append("! Not a user type '%s'"%(dic['principal_type']))
            continue
        member = portal.portal_membership.getMemberById(user)
        if member is None:
            out.append("! Member not found ")
            continue
        line = ["%03d"%count, user]
        for name in properties_names:
            if member.hasProperty(name):
                line.append(str(member.getProperty(name)).replace('\r\n', '|'))
            else:
                line.append('')
                out.append("!!! User '%s' hasn't property '%s'"%(user, name))
        txt.append('\t'.join(line))
        count += 1
    doc = self.users_properties
    doc.raw = '\n'.join(txt)
    out.append("Document '%s/users_properties' updated !"%'/'.join(target_dir.getPhysicalPath()))

    return '\n'.join(out)

###############################################################################

def load_user_properties(self, dochange=''):
    """
        load saved user properties
    """

    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    from Products.CMFCore.utils import getToolByName
    portal = getToolByName(self, "portal_url").getPortalObject()

    out=[]
    if 'oldacl' not in portal.objectIds():
        return "First you must create a folder at Plonesite root named 'oldacl' and containing the imported 'user_properties' DTMLDocument (created with external method 'store_user_properties')"

    if 'users_properties' not in portal.oldacl.objectIds():
        return "You must import in the folder named '/oldacl' the DTMLDocument named 'user_properties' (created with external method 'store_user_properties')"

    change_property=False
    if dochange not in ('', '0', 'False', 'false'):
        change_property=True

    if not change_property:
        out.append("The following changes are not applied: you must run the script with the parameter '...?dochange=1'")

    properties_names = dict(portal.portal_memberdata.propertyItems())
    skipped_properties = ['error_log_update', 'ext_editor', 'last_login_time', 'listed', 'login_time', 'visible_ids', 'wysiwyg_editor', ]

    #import pdb; pdb.set_trace()

    doc = portal.oldacl.users_properties
    lines = doc.raw.splitlines()
    if not len(lines) > 1:
        return "No information found in document: content='%s'"%doc.raw
    columns = {}

    header_line = True
    for line in lines:
        infos = line.split('\t')
        user = infos[1]
        props = {}
        if header_line and user != 'User':
            return "No header line in document: content='%s'"%doc.raw
        for i in range(2, len(infos)):
            property = infos[i]
            if not property: continue
            if header_line:
                if property in skipped_properties:
                    property = ''
                    #this column is made empty, this will not be used when reading value
                elif property not in properties_names:
                    out.append("Warning: old property '%s' not found in portal_memberdata properties"%property)
                columns[i] = property
            elif columns[i]:
                props[columns[i]] = property.replace('|', '\r\n')

        if header_line:
            header_line = False
            continue

        count = int(infos[0])
        if props:
            out.append("%03d, User '%s' has changed properties '%s'"%(count, user, str(props)))
            if change_property:
                member = portal.portal_membership.getMemberById(user)
                if member is None:
                    out.append("%03d, User '%s' not found !!"%(count, user))
                    continue
                member.setMemberProperties(props)
        else:
            out.append("%03d, User '%s' hasn't change in properties"%(count, user))
    return '\n'.join(out)

###############################################################################

def ploneboard_correct_modified(self, dochange=''):
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
        #out.append("available properties:%s"%portal.portal_memberdata.propertyItems())
        out.append("To really change modification date, call the script with param:")
        out.append("-> dochange=1")
        out.append("by example ...?dochange=1\n")
        out.append("You must update the portal_catalog after running the script\n")

    portal_url = getToolByName(self, "portal_url")
    portal = portal_url.getPortalObject()

    kw = {}
    kw['portal_type'] = ('PloneboardConversation')
        #kw['review_state'] = ('private',) #'published'
        #kw['path'] = '/' # '/'.join(context.getPhysicalPath())
    kw['sort_on'] = 'created'
        #kw['sort_order'] = 'reverse'

    results = portal.portal_catalog.searchResults(kw)

    out.append("%d conversations found\n"%len(results))
    for r in results :
        conv = r.getObject()
#        print "%s, %s, %s, %s"%(r.id, conv.Title(), r.created, r.modified)
        out.append("%s, %s, %s, %s"%(r.id, conv.Title(), r.created, r.modified))
        last_modification_date = None
        for com in conv.getComments():
#            print "\t%s, %s, %s, %s"%(com.getId(), com.Title(), com.CreationDate(), com.ModificationDate())
            out.append("\t%s, %s, %s"%(com.getId(), com.Title(), com.CreationDate()))
            if dochange:
                com.setModificationDate(com.CreationDate())
                #com.reindexObject() #avoid
            #print "\t%s"%com.ModificationDate()
            last_modification_date = com.CreationDate()
        out.append('=> new modification date = %s'%last_modification_date)
        if dochange:
            conv.setModificationDate(last_modification_date)
            #conv.reindexObject() #avoid
    return "\n".join(out)

###############################################################################

def configure_fckeditor(self, default=1, allusers=1, custom=1, nomerge=0):
    """
        configure fckeditor with default parameters.
        This method can be called as an external method, with the following parameters : ...?default=1&alluser=0&custom=0
    """
    if not check_role(self):
        return "You must have a manager role to run this script"

    from Products.CMFCore.utils import getToolByName
    portal = getToolByName(self, "portal_url").getPortalObject()

    try:
        pqi = getToolByName(self, 'portal_quickinstaller')
        if not pqi.isProductInstalled('FCKeditor'):
            pqi.installProduct('FCKeditor')
    except Exception, msg:
        return "FCKeditor cannot be installed: '%s'"%msg

    #setting default editor to FCKeditor
    if default:
        portal.portal_memberdata.manage_changeProperties(wysiwyg_editor='FCKeditor')

    #changing editor of all users
    if allusers:
        change_user_properties(portal, kw='wysiwyg_editor:FCKeditor', dochange=1)

    #setting custom toolbar
    if custom:
        fckprops = portal.portal_properties.fckeditor_properties
        if fckprops.getProperty('fck_toolbar') != 'Custom':
            fckprops.manage_changeProperties(fck_custom_toolbar="[\n ['Templates','rtSpellCheck'],\n ['Cut','Copy','Paste','PasteText','PasteWord'],\n ['Undo','Redo','-','Find','Replace','-','RemoveFormat'],\n ['Bold','Italic','Underline','StrikeThrough'],\n ['OrderedList','UnorderedList'],\n ['JustifyLeft','JustifyCenter','JustifyRight','JustifyFull'],\n ['Link','Unlink'],\n ['Image','imgmapPopup','Table','Rule','SpecialChar'],\n ['Style','FontFormat','TextColor'],\n ['FitWindow'],['Source']\n]")
            fckprops.manage_changeProperties(fck_toolbar='Custom')

    #removing javascript merge option on fcksetting custom toolbar
    if nomerge:
        pjs = getToolByName(self, 'portal_javascripts')
        pjs.updateScript('fckeditor.js', cookable=False)


###############################################################################

def list_users(self, output='csv', sort='users'):
    """
        list users following parameters :
            group = True, group information is included
            sort = 'users' or 'groups', sort key for output
    """
    if not check_role(self):
        return "You must have a manager role to run this script"
    lf = '\n'
    lf = '<br />'
    separator = ','

    from Products.CMFCore.utils import getToolByName
    portal = getToolByName(self, "portal_url").getPortalObject()
    pg = getToolByName(self, "portal_groups")
    out = []
    out.append('<h2>Users list</h2>')
    out.append("You can call the script with the following parameters:")
    out.append("-> output=screen => output for screen or csv (default=csv)")
    out.append("-> sort=groups (or users) => output is sorted following groups (default=users)")
    out.append("by example /cputils_list_users?output=screen&sort=groups")
    out.append("You can copy/paste the following lines in the right program like openoffice calc ;-) or Excel :-(%s"%lf)

    if sort not in ('users', 'groups'):
        out.append("invalid parameter sort, value must be 'users' or 'groups'")
        return
    if output not in ('csv', 'screen'):
        out.append("invalid parameter output, value must be 'csv' or 'screen'")
        return

    #import pdb; pdb.set_trace()
    users = {}
    groups = {}
    for userid in search_users(self):
        member = portal.portal_membership.getMemberById(userid)
        if not users.has_key(userid):
            users[userid] = {}
        users[userid]['obj'] = member
        groupids = pg.getGroupsForPrincipal(member)
        users[userid]['groups'] = groupids
        for groupid in groupids:
            if not groups.has_key(groupid):
                groups[groupid] = {}
                groups[groupid]['users'] = []
            groups[groupid]['users'].append(userid)

    if sort == 'users':
        if output == 'csv':
            out.append(separator.join(['UserId', 'GroupId']))
        for userid in users.keys():
            if output == 'screen':
                out.append("- userid: %s"%userid)
            for groupid in users[userid]['groups']:
                if output == 'csv':
                    out.append(separator.join([userid, groupid]))
                else:
                    out.append('&emsp&emsp&rArr %s'%groupid)
    elif sort == 'groups':
        if output == 'csv':
            out.append(separator.join(['GroupId', 'UserId', ]))
        for groupid in groups.keys():
            if output == 'screen':
                out.append("- groupid: %s"%groupid)
            for userid in groups[groupid]['users']:
                if output == 'csv':
                    out.append(separator.join([groupid, userid, ]))
                else:
                    out.append('&emsp&emsp&rArr %s'%userid)
    return lf.join(out)

###############################################################################

def recreate_users_groups(self):
    """copy users from old acl_users to the new one """

    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    from Products.CMFCore.utils import getToolByName
    portal = getToolByName(self, "portal_url").getPortalObject()

    if 'oldacl' not in portal.objectIds():
        return "First you must create a folder at Plonesite root named 'oldacl' and containing a copy of another acl_users"

    if 'acl_users' not in portal.oldacl.objectIds():
        return "You must import a Plonesite acl_users folder in the folder named '/oldacl'"

    old_acl = portal.oldacl.acl_users
    acl = portal.acl_users
    prg = portal.portal_registration
    pgr = portal.portal_groups
    messages = []

    #import pdb; pdb.set_trace()
    for gd in old_acl.searchGroups():
        g = old_acl.source_groups.getGroupById(gd['groupid'])
        if g.getId() not in acl.getGroupIds():
            pgr.addGroup(g.getId(), roles = g.getRoles(), groups = g.getGroups())
            messages.append("Group '%s' is added"%g.getId())
        else:
            messages.append("Group '%s' already exists"%g.getId())

    users = old_acl.getUsers()
    #thanks http://blog.kagesenshi.org/2008/05/exporting-plone30-memberdata-and.html
    passwords=old_acl.source_users._user_passwords
    for user in users:
        if user.getUserId() not in [ud['userid'] for ud in acl.searchUsers()]:
            prg.addMember(user.getUserId(), passwords[user.getUserId()], roles=user.getRoles(), domains=user.getDomains())
            messages.append("User '%s' is added"%user.getUserId())
            for groupid in user.getGroupIds():
                if groupid == 'AuthenticatedUsers':
                    continue
                pgr.addPrincipalToGroup(user.getUserId(), groupid)
                messages.append("    -> Added in group '%s'"%groupid)
        else:
            messages.append("User '%s' already exists"%user.getUserId())
    return "\n".join(messages)

###############################################################################

def checkPOSKey(self):
    """
        Call a method from the script checks to check the dbs
    """
    lf = '<br />'
    from Products.CPUtils.scripts import checkPOSKeyErrors
    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    errors = []
    checkPOSKeyErrors.check(self, errors)
#    if not errors:
#        errors.append('No POSKey errors found')
    return lf.join(errors)

###############################################################################

def sync_properties(self, base='', update='', dochange=''):
    """
        Synchronize properties between objects
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    lf = '\n'
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
    out.append('<h2>Synchronize properties of objects</h2>')
    out.append("<p>You can call the script with the following parameters:<br />")
    out.append("-> base=path => path of base object to synchronize, beginning at the root of the plone site (those properties will be kept)<br />")
    out.append("-> update=path => path of update object (containing new properties), beginning at the root of the plone site<br />")
    out.append("-> dochange=1 => really do the change. By default, only prints changes<br />")
    out.append("by example /cputils_sync_properties?base=portal_skins/custom/cpskin3_properties&update=portal_skins/acptheme_cpskin3_theme1/cpskin3_properties</p>")

    if not base:
        out.append("<p>!! You must enter the 'base' parameter</p>")
        return lf.join(out)

    if not update:
        out.append("<p>!! You must enter the 'update' parameter</p>")
        return lf.join(out)

    base_path = base_path.lstrip('/')
    base_obj = portal.unrestrictedTraverse(base_path)
    if base_obj is None:
        out.append("<p>base path '%s' not found in portal</p>"%base_path)
        return lf.join(out)

    update_path = update_path.lstrip('/')
    update_obj = portal.unrestrictedTraverse(update_path)
    if update_obj is None:
        out.append("<p>update path '%s' not found in portal</p>"%update_path)
        return lf.join(out)

    if dochange not in ('', '0', 'False', 'false'):
        change_property=True

#    if not dochange:
#        out.append("<p>To really change the base object to synchronize '%s', call the script with another param:</p>"%base_path)
#        out.append("<p>-> dochange=1    , by example ...&dochange=1</p>")

#    out.append('<p style="text-align: center;">*****</p>')
    out.append("<table><thead><tr>")
    out.append("<th>Property</th>")
    out.append("<th>Status</th>")
    out.append("<th>Base value</th>")
    out.append("<th>Other value</th>")
    out.append("<th>Kept</th>")
    out.append("</tr></thead><tbody>")

    #import pdb; pdb.set_trace()
    base_dic = dict(base_obj.propertyItems())
    base_keys = base_dic.keys()
    base_keys.sort()
    update_dic = dict(update_obj.propertyItems())

    for base_prop in base_keys:
        if update_dic.has_key(base_prop):
            if base_dic[base_prop] == update_dic[base_prop]:
                out.append("<tr><td>%s</td><td>==</td><td>%s</td><td>%s</td><td>%s</td></tr>"%(base_prop, base_dic[base_prop], base_dic[base_prop], base_dic[base_prop]))
            else:
                out.append("<tr><td>%s</td><td class='red'><></td><td>%s</td><td>%s</td><td>%s</td></tr>"%(base_prop, base_dic[base_prop], update_dic[base_prop], base_dic[base_prop]))
            del update_dic[base_prop]
        else:
            out.append("<tr><td>%s</td><td class='red'>del</td><td>%s</td><td>%s</td><td>%s</td></tr>"%(base_prop, base_dic[base_prop], '', base_dic[base_prop]))
    update_keys = update_dic.keys()
    update_keys.sort()

    for new_prop in update_keys:
        out.append("<tr><td>%s</td><td class='red'>new</td><td>%s</td><td>%s</td><td>%s</td></tr>"%(new_prop, '', update_dic[new_prop], update_dic[new_prop]))
        if change_property:
#            base_obj.manage_changeProperties({newprop:update_dic[new_prop]})
            base_obj.manage_addProperty(new_prop, update_dic[new_prop], update_obj.getPropertyType(new_prop))

    out.append('</tbody></table>')
    return lf.join(out)

###############################################################################

def correct_language(self, default='', search='all', onlycurrentfolder=0, dochange='', filter=0):
    """
        correct language objects, set as neutral if no translation exists
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    import Missing
    lf = '\n'
#    lf = '<br />'
    change_property = False
    only_current_folder = False
    filters = [1,2,3,4]

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
    out.append('<h2>Corrects language of untranslated objects</h2>')
    out.append("<p>You can call the script with the following parameters:<br />")
    out.append("-> default=code => language code for untranslated objects (default to neutral)<br />")
    out.append("-> search=fr => language code of searched objects (default to all languages)<br />")
    out.append("-> onlycurrentfolder=0 => do correct language in all site (default) <br />")
    out.append("-> filter=1 or filter=123 => filter numbers (default to all objects)<br />")
    out.append("-> &nbsp;&nbsp;&nbsp;&nbsp;1 => displays only canonical objects<br />")
    out.append("-> &nbsp;&nbsp;&nbsp;&nbsp;2 => displays only translations<br />")
    out.append("-> &nbsp;&nbsp;&nbsp;&nbsp;3 => displays if object language is different from default<br />")
    out.append("-> &nbsp;&nbsp;&nbsp;&nbsp;4 => displays unchanged objects<br />")
    out.append("-> dochange=1 => really do the change. By default, only prints changes<br />")
    out.append("by example /cputils_correct_language?default=fr&dochange=1</p>")
    out.append('<p>New value in <span class="red">red</span> will be changed</p>')

    errors = []

    if 'LinguaPlone' not in [p['id'] for p in pqi.listInstalledProducts()]:
        out.append("<p>LinguaPlone not installed ! Not necessary to do this operation</p>")
        return lf.join(out)

    if onlycurrentfolder not in ('', '0', 'False', 'false'):
        only_current_folder=True

    kw = {}
    #kw['portal_type'] = ('Document','Link','Image','File','Folder','Large Plone Folder','Wrapper','Topic')
    #kw['review_state'] = ('private',) #'published'
    if only_current_folder: 
        kw['path'] =  '/'.join(self.getPhysicalPath())
    #kw['sort_on'] = 'created'
    #kw['sort_order'] = 'reverse'
    kw['Language'] = search

    if filter:
        filters = [int(i) for i in list(filter.strip())]

    if dochange not in ('', '0', 'False', 'false'):
        change_property=True

    results = portal.portal_catalog.searchResults(kw)
    out.append("<p>Number of retrieved objects (not filtered): %d</p>"%len(results))
    out.append("<table><thead><tr>")
    out.append("<th>Language</th>")
    out.append("<th>Metadata</th>")
    out.append("<th>Path</th>")
    out.append("<th>New value</th>")
    out.append("</tr></thead><tbody>")

    #out.append("<tr><td>%s</td></tr>"%';'.join(filters))
    #import pdb; pdb.set_trace()
    for brain in results:
        obj = brain.getObject()
        #metadata can be missing !
        if brain.Language == Missing.MV:
            meta_lang = 'Missing.Value'
        elif brain.Language == '':
            meta_lang = 'neutral'
        else:
            meta_lang = brain.Language
        #we use obj instead
        try:
            if obj.getLanguage() == '':
                current_lang = 'neutral'
            else:
                current_lang = obj.getLanguage()
            obj.getDeletableLanguages()
        except AttributeError:
            errors.append("<div>Cannot get language on object '%s' at url '<a href=\"%s\">%s</a>'</div>"%(brain.Title, brain.getURL(), brain.getPath()))
            current_lang = 'AttributeError'
            continue
        except KeyError:
            # es-es not found in deletable language
            errors.append("<div>Language '%s' not in deletable lang: '%s' at url '<a href=\"%s\">%s</a>'</div>"%(msg, brain.Title, brain.getURL(), brain.getPath()))
            continue

        #we first search for translated objects: no change for those objects
        #condition= already language and canonical with translations
        if current_lang and obj.isCanonical() and obj.getDeletableLanguages():
            if 1 in filters:
                out.append("""<tr><td>%s</td><td>%s</td><td><a href="%s" target="_blank">%s</a></td><td class="green">canonical</td></tr>""" % (current_lang, meta_lang, brain.getURL(), brain.getPath()))
        #condition= already language and not canonical = translation
        elif current_lang and not obj.isCanonical():
            if 2 in filters:
                out.append("""<tr><td>%s</td><td>%s</td><td><a href="%s" target="_blank">%s</a></td><td class="green">translation</td></tr>""" % (current_lang, meta_lang, brain.getURL(), brain.getPath()))
        #no translation and language must be changed
        elif current_lang != default:
            if 3 in filters:
                out.append("""<tr><td class='red'>%s</td><td>%s</td><td><a href="%s" target="_blank">%s</a></td><td class="red">%s</td></tr>""" % (current_lang, meta_lang, brain.getURL(), brain.getPath(), default or "neutral"))
                if change_property:
                    obj.setLanguage(default)
                    obj.reindexObject()
        #no change
        elif 4 in filters:
            out.append("""<tr><td>%s</td><td>%s</td><td><a href="%s" target="_blank">%s</a></td><td>unchanged</td></tr>""" % (current_lang, meta_lang, c, brain.getPath()))

    out.append('</tbody></table>')

    if errors:
        i = out.index("<table><thead><tr>")
        errors.append('<br />')
        out[i:i] = errors

    return lf.join(out)

 ###############################################################################

def copy_image_attribute(self):
    """
        copy image from canonical document into translated document
        method to add action in site :
        1. add external method (copy_image_attribute)
        2. in portal_action add new CMF action
        3. edit this action
        >>> url (expression) is : string:${globals_view/getCurrentObjectUrl}/cputils_copy_image_attributes
        >>> Condition (expression) is : python:checkPermission("Delete objects", globals_view.getParentObject()) and checkPermission("Copy or Move", object) and checkPermission("Add portal content", object) and not globals_view.isPortalOrPortalDefaultPage() and not object.isCanonical()
    """
    from collective.contentleadimage.utils import hasContentLeadImage
    from collective.contentleadimage.config import IMAGE_FIELD_NAME
    canonical_obj = self.getCanonical()
    if not canonical_obj or (self == self.getCanonical()):
        return
    if hasContentLeadImage(canonical_obj):
        if canonical_obj.getField(IMAGE_FIELD_NAME) and self.getField(IMAGE_FIELD_NAME):
            self.getField(IMAGE_FIELD_NAME).getMutator(self)(canonical_obj.getField(IMAGE_FIELD_NAME).getAccessor(canonical_obj)())
    self.plone_utils.addPortalMessage(u'Ajout du champ leadImage')
    return self.REQUEST.RESPONSE.redirect(self.absolute_url())

 ###############################################################################

def desactivate_base2dom(self):
    """
     desactivate base2-dom javascript to resolve problem on fckeditor loading in firefox4
    """
    if not check_zope_admin():
        return 'desactivate_base2dom run with a non admin user: we go out'
    out = []
    try:
        for site in get_all_site_objects(self) :
            sitePath = '/'.join(site.getPhysicalPath())
            if hasattr(site,"portal_javascripts"):
                js = site.portal_javascripts.getResource('++resource++base2-dom-fp.js')
                if js.getEnabled():
                    js.setEnabled(False)
                    out.append("Disabled ++resource++base2-dom-fp.js for %s"%sitePath)
    except Exception, message:
        out.append("!! error when disabling base2dom: %s" %(message))
    return '\n'.join(out)

 ###############################################################################

def unregister_adapter(self, unregister=''):
        """
            unregister lost adapter (product removed from the file system)
            for error "AttributeError: type object 'IThemeSpecific' has no attribute 'isOrExtends' "
        """
        if not check_zope_admin():
            return "You must be a zope manager to run this script"

        lf = '\n'
    #    lf = '<br />'
        out = []
        out.append("<p>You can call the script with the following parameters:<br />")
        out.append("-> unregister=... => name of the adapter to unregister (default to empty => list all adapters)<br />")

        from zope.component import getSiteManager
        from Products.CMFCore.utils import getToolByName
        portal = getToolByName(self, "portal_url").getPortalObject()
        #import pdb; pdb.set_trace()

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
                if components.unregisterAdapter(params[0], params[1], params[2], unregister):
                    out.append("Adapter '%s' unregistered"%unregister)
                else:
                    out.append("Adapter '%s' not unregistered !"%unregister)
            except Exception, msg:
                out.append("Adapter '%s' not unregistered : %s"%(unregister, msg))

        return lf.join(out)

###############################################################################

def change_authentication_plugins(self, activate='', dochange=''):
    """
        activate or desactivate and save (in dtml doc) authentication plugin
    """

    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    out=[]
    txt=[]

    change_activate=False
    if activate not in ('', '0', 'False', 'false'):
        change_activate=True

    change_plugins=False
    if dochange not in ('', '0', 'False', 'false'):
        change_plugins=True

    if not change_plugins:
        out.append("The following changes are not applied: you must run the script with the parameter '...?dochange=1'")

    from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin
    if change_activate:
        #read authentication_plugins_sites dtml doc
        if 'authentication_plugins_sites' not in self.objectIds():
            return out.append("No DTMLDocument named 'authentication_plugins_sites' found")
        doc = self.authentication_plugins_sites
        lines = doc.raw.splitlines()
        out.append("Read all lines from DTMLDocument named 'authentication_plugins_sites'")
        for line in lines:
            out.append(str(line))
            infos = line.split('\t')
            site = infos[0]
            if site.find('/') > 0:
                (path,site) = site.split('/')
                if hasattr(self,path):
                    context = getattr(self, path)
                else:
                    continue
            else:
                context = self
            if hasattr(context,site):
                out.append('site found %s'%site)
                obj = getattr(context, site)
                plugins = obj.acl_users.plugins
            else:
                continue
            auth_plugins = plugins.getAllPlugins(plugin_type='IAuthenticationPlugin')
            for i in range(1, len(infos)):
                plugin = infos[i]
                if not plugin in auth_plugins['active']:
                    #activate authentication plugins
                    out.append('Activate plugins %s for %s'%(plugin,site))
                    if change_plugins:
                        plugins.activatePlugin(IAuthenticationPlugin,plugin)
    else:
        #save authentication_plugins_sites in dtml doc plugin from all site
        if 'authentication_plugins_sites' not in self.objectIds():
            self.manage_addDTMLDocument(id='authentication_plugins_sites', title='All authentication plugins sites')
            out.append("Document '%s/authentication_plugins_sites' added"%'/'.join(self.getPhysicalPath()))
        allSiteObj = get_all_site_objects(self)
        for obj in allSiteObj:
            objPath = ""
            for i in range(1,len(obj.getPhysicalPath())-1):
                objPath = objPath + obj.getPhysicalPath()[i] + '/'
            objid = obj.getId()
            plugins = obj.acl_users.plugins
            auth_plugins = plugins.getAllPlugins(plugin_type='IAuthenticationPlugin')
            plugLine = objPath + objid
            for plug in list(auth_plugins['active']):
                plugLine = plugLine + '\t' + str(plug)
                out.append('Desactivate plugins %s for %s'%(str(plug),objPath + objid))
                if change_plugins:
                    #desactivate authentication plugins
                    plugins.deactivatePlugin(IAuthenticationPlugin,plug)
            txt.append(plugLine)

        doc = self.authentication_plugins_sites
        doc.raw = '\n'.join(txt)
        out.append("Document '/authentication_plugins_sites' updated !")
    return '\n'.join(out)

###############################################################################

def install_plone_product(self, productName='', installMode='', dochange=''):
    """
        install/reinstall or uninstall a plone product
    """

    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    out=[]

    out.append('<head><style type="text/css">')
    out.append("table { border: 1px solid black; border-collapse:collapse; }")
    out.append("table th { border: 1px solid black; background: #8297FD; }")
    out.append("table td { border: 1px solid black; padding: 2px }")
    out.append(".red { color: red; } ")
    out.append(".green { color: green; } ")
    out.append("</style></head>")
    out.append('<h2>Install, Uninstall or Re-Install product</h2>')
    out.append("<p>You can call the script with the following parameters:<br />")
    out.append("-> productName=name of product => ie. contact<br />")
    out.append("-> installMode='I','U' or 'R' => Install (Re-Install if product exist), Uninstall or Re-install (not install if product doesn't exist)<br />")
    out.append("-> (Optional) dochange=1 => really do the change. By default, only prints changes<br />")
    out.append("<p>by example /install_plone_product?productName=Linguaplone&installMode=I&dochange=1</p>")

    out.append("<table><thead><tr>")
    out.append("</tr></thead><tbody>")
    if productName == "":
        out.append("""<tr><td class="red">please, choose a product to install</td><td class="red"></td></tr>""")
        return '\n'.join(out)

    if installMode not in ('I', 'U', 'R'):
        out.append("""<tr><td class="red">please, installMode must be in 'I','U' or 'R'</td><td class="red"></td></tr>""")
        return '\n'.join(out)
    out.append('</tbody></table>')

    execute_change=False
    if dochange not in ('', '0', 'False', 'false'):
        execute_change=True

    if not execute_change:
        out.append("The following changes are not applied: you must run the script with the parameter '...?dochange=1'")

    #get all site on root or in first folder (by mountpoint)
    allSiteObj = get_all_site_objects(self)
    if installMode in ('I','R'):
        #install or re-install product
        for obj in allSiteObj:
            objid = obj.getId()
            if not obj.portal_quickinstaller.isProductInstallable(productName):
                out.append('<p>Bad Product name %s for %s</p>'%(productName,objid))
                continue
            if  obj.portal_quickinstaller.isProductInstalled(productName):
                out.append('<p>Re-install product %s for %s</p>'%(productName,objid))
                if execute_change:
                    obj.portal_quickinstaller.reinstallProducts([productName])
            elif installMode == 'I':
                out.append('<p>Install product %s for %s</p>'%(productName,objid))
                if execute_change:
                    obj.portal_quickinstaller.installProducts([productName])
    else:
        #uninstall product
        for obj in allSiteObj:
            objid = obj.getId()
            if not obj.portal_quickinstaller.isProductInstallable(productName):
                out.append('<p>Bad Product name %s for %s</p>'%(productName,objid))
                continue
            if  obj.portal_quickinstaller.isProductInstalled(productName):
                out.append('<p>Uninstall product %s for %s</p>'%(productName,objid))
                if execute_change:
                   obj.portal_quickinstaller.uninstallProducts([productName])
    return '\n'.join(out)

###############################################################################

def send_adminMail(self, dochange='', subject='Aux administrateurs du site plone', bodyText='', allsites='1'):
    """
        send mail to all admin user
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    out=[]
    send_mail=False
    if dochange not in ('', '0', 'False', 'false'):
        send_mail=True

    #get all site on root or in first folder (by mountpoint)
    allSiteObj = get_all_site_objects(self)
    if allsites in ('', '0', 'False', 'false'):
        allSiteObj = [self.portal_url.getPortalObject()]

    for obj in allSiteObj:
        #get contact email
        authorEmail = obj.email_from_address
        users_mail = [authorEmail]
        #get administrators email
        for userInfos in obj.acl_users.searchUsers():
            userid = userInfos['userid']
            member = obj.portal_membership.getMemberById(userid)
            if member.has_role('Manager'):
                user_mail = member.getProperty('email')
                if user_mail != "" and user_mail not in users_mail:
                    users_mail.append(user_mail)
        objPath = "/".join(obj.getPhysicalPath())
        To = ";".join(users_mail)

        out.append("EMAIL for site %s"%objPath)
        out.append('From : %s, To : %s, Mail subject : %s, mail data : %s '%(authorEmail, To, subject, bodyText))

        if send_mail:
            ret = sendmail(obj, authorEmail, To, bodyText, subject = subject)
            ret and out.append('Return code:%s'%ret)

    return '\n'.join(out)

###############################################################################

def checkInstance(self, isProductInstance='', instdir=''):
    from Products.CPUtils.hiddenProductsList import dic_hpList
    
    if not check_zope_admin():
        return 'checkInstance run with a non admin user: we go out'
    try:
        out = []

        is_Production_Instance=False
        if isProductInstance not in ('', '0', 'False', 'false'):
            is_Production_Instance=True
        allSiteObj = get_all_site_objects(self)
        isProductInstance = self.getId()
        
        #0.Check if hiddenProducts properties exists, and if yes, check discrepancies
        if not hasattr(self, 'hiddenProducts'):
            out.append(" !! No hiddenProducts properties defined")
        else:                   
            #Search the "type" of application hosted by the zope instance (website, urban, teleservice,..)
            type = ""
            for productname in dic_hpList.keys():
                #Determine it by checking if the product is installable
                if productname in self.Control_Panel.Products.objectIds():
                    type = productname
                    break             
            #Once the type is known, look for discrepancies in the "hidden products" list for this type of product
            external_hp_list = set(dic_hpList[type])
            internal_hp_list = set(self.hiddenProducts)
            for hiddenProduct in external_hp_list.symmetric_difference(internal_hp_list):
                if hiddenProduct not in internal_hp_list:
                    out.append("!! the product '%s' is in the hidden products external list but not in the site list"%(hiddenProduct))
                else:
                    out.append("!! the product '%s' is in the hidden products site list but not in the external list"%(hiddenProduct))
        
        for obj in allSiteObj:
            objid = obj.getId()  
            objPath = ""
            for i in range(1,len(obj.getPhysicalPath())-1):
                objPath = objPath + obj.getPhysicalPath()[i] + '/'            
            #out.append(">> Site in analyse : %s"%objPath+objid)     
            #1. Check if we are in debugMode (only for product instance)
            if is_Production_Instance:
                #out.append(">> Check debugMode")
                if hasattr(obj,"portal_css"):                
                    if obj.portal_css.debugmode:
                        obj.portal_css.setDebugMode(False)
                        out.append("!! %s (debugMode) >>> Css : %s"%(objPath+objid,obj.portal_css.debugmode))
                if hasattr(obj,"portal_javascripts"): 
                    if obj.portal_javascripts.debugmode:
                        obj.portal_javascripts.setDebugMode(False)
                        out.append("!! %s (debugMode) >>> Javascripts : %s"%(objPath+objid,obj.portal_javascripts.debugmode))
                if hasattr(obj,"portal_kss"): 
                    if obj.portal_kss.debugmode:
                        obj.portal_kss.setDebugMode(False)
                        out.append("!! %s (debugMode) >>> kss %s"%(objPath+objid,obj.portal_kss.debugmode))
            #2. Check if robot.txt exist in test instance and not exist in product instance
            #out.append(">> Check robots.txt")   
            if hasattr(obj,"portal_skins.custom"):            
                if is_Production_Instance and hasattr(obj.portal_skins.custom,"robots.txt"):
                    out.append("!! %s >>> Have a file named 'robots.txt'"%(objPath+objid))   
                elif not is_Production_Instance and not hasattr(obj.portal_skins.custom,"robots.txt"):
                    out.append("!! %s >>> Haven't a file named 'robots.txt'"%(objPath+objid))        
            #3. Check if connexion plugins is activate
            #out.append(">> Check connexion plugins")
            plugins = obj.acl_users.plugins
            auth_plugins = plugins.getAllPlugins(plugin_type='IAuthenticationPlugin')
            if not auth_plugins['active']:
                out.append('!! %s >>> No connexion plugins is activate'%(objPath+objid))           
            #4. Check if Ids is correct (without space)
            #out.append(">> Check Ids")
            if objid.find(' ') >= 0:                
                out.append("!! %s >>> this site (%s) contain space characters in id"%(objPath+objid,objid))            
            #5. Check if cache setup is installed (only for product instance)
            if is_Production_Instance:
                #out.append(">> Check CacheSetup")
                if hasattr(obj,"portal_quickinstaller"):
                    if  not obj.portal_quickinstaller.isProductInstalled("CacheSetup"):
                        out.append("!! %s >>> cache setup isn't installed"%(objPath+objid))
            #out.append("")
        return '\n'.join(out)
    except Exception, message:
        out.append("!! error in checkinstance %s"%str(message))
        return '\n'.join(out) 

###############################################################################

def list_portlets(self):
    if not check_zope_admin():
        return 'checkInstance run with a non admin user: we go out'

    from zope.annotation.interfaces import IAnnotations
    #import pdb; pdb.set_trace()
    out = []
    ann = IAnnotations(self)
    out.append("left: "+str(dict(ann['plone.portlets.contextassignments']['plone.leftcolumn'])))
    out.append("right: "+str(dict(ann['plone.portlets.contextassignments']['plone.rightcolumn'])))
    return "\n".join(out)

###############################################################################

def rename_long_ids(self, length='255', dochange='', fromfile=''):
    """
        Renames too long ids, not permitting transmogrifier export
        1) run on orig site first, writing correspondences in output file
        2) renames as orig filenames from correspondences file
    """
    from Products.CMFCore.utils import getToolByName
    from Acquisition import aq_base
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
    if fromfile not in ('', '0', 'False', 'false'):
        from_file = True
    do_change = False
    if dochange not in ('', '0', 'False', 'false'):
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
            i = oid.find('-', i+1, plen)
        if lasti:
            return oid[0:lasti]
        else:
            return oid[0:plen]

    if not from_file:
        results = portal.portal_catalog.searchResults()
        otn['/'] = {}
        otn['/']['obj'] = portal
        otn['/']['npathid'] = ''

        #cannot get results sorted by path index !
        for r in results:
            obj = r.getObject()
            rpathid = "/%s" % '/'.join(portal_url.getRelativeContentPath(obj))
            otn[rpathid] = {}
            otn[rpathid]['obj'] = obj

        txt = []
        #sort objects by path, handling parents to childs
        for opathid in sorted(otn.keys()):
            if opathid == '/': continue
            (opath, oid) = os.path.split(opathid)
            noid = oid
            npath = otn[opath]['npathid']
            if len(oid) > max_len:
                cont = otn[opath]['obj']
                baseoid = noid = cut_oid(oid)
                i = 1
                while hasattr(aq_base(cont), noid) or nto.has_key("%s/%s"%(npath, noid)):
                    noid = "%s-%d"%(baseoid, i)
                    i += 1
            npathid = "%s/%s"%(npath, noid)
            otn[opathid]['npathid'] = npathid
            nto[npathid] = opathid
            if opathid != npathid:
                txt.append("%s => %s"%(opathid, npathid))
                out.append("%s => %s"%(opathid, npathid))

        if do_change:
            #reverse sort objects by path to change id, handling childs to parents
            for opathid in sorted(otn.keys(), reverse=True):
                if opathid == '/' or opathid == otn[opathid]['npathid']:
                    continue
                obj = portal.restrictedTraverse(opathid[1:])
                nid = os.path.split(otn[opathid]['npathid'])[1]
                obj.setId(nid)
                obj.reindexObject('id')
            
        if 'rename_long_ids' not in portal.objectIds():
            portal.manage_addDTMLDocument(id='rename_long_ids', title='Correspondences for long ids rename')
            out.append("<br />Document '%s/rename_long_ids' added"%'/'.join(portal.getPhysicalPath()))
        doc = self.rename_long_ids
        if txt:
            doc.raw = '\n'.join(txt)
            out.append("Document '%s/rename_long_ids' updated !"%'/'.join(portal.getPhysicalPath()))
    else:
        if 'rename_long_ids' not in portal.objectIds():
            return "You must import at the root site the DTMLDocument named 'rename_long_ids'"
        #first we load the correspondences
        doc = portal.rename_long_ids
        lines = doc.raw.splitlines()
        #reverse sort objects by path to change id, handling childs to parents
        for line in sorted(lines, reverse=True):
            opathid, npathid = line.split(' => ')
            opath, oid = os.path.split(opathid)
            out.append("%s => %s"%(npathid, oid))
            if do_change:
                obj = portal.restrictedTraverse(npathid[1:])
                obj.setId(oid)
                obj.reindexObject('id')

    if do_change:
        out.append("<br />Rename applied !")
    return '<br />'.join(out)
    
###############################################################################
    
def list_newsletter_users (self, activity='all', format ='all'):
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
    out.append("\nexample:  .../cputils_list_newsletter_users?activity=active&format=Text\n")
    out.append("##########################################################################################################")
    
        
    options = {'activity':['all','active','inactive'] , 'format':['all','HTML','Text'] }
    
    if activity not in options['activity']:
        activity = options['activity'][0]
    if format not in options['format']:
        format = options['format'][0]
    
    header = ['EMAIL', 'ACTIVE', 'FORMAT']
    header = ','.join(header)
    
    results = self.portal_catalog.searchResults(portal_type = "NewsletterBTree")
    for brain in results:
        obj = brain.getObject()
        out.append("\nSucribers list of the folder '"+obj.Title()+"' from the newsletter '"+obj.aq_parent.Title()+"'\n")
        out.append(header)
        for sub in obj.objectValues():
            line = [sub.email]
            
            if activity != 'all' and (activity == 'active') != sub.active:
                continue
            
            if sub.active:
                act = '*'
            else:
                act = ''
            line.append(act)
            
            if format != 'all' and format != sub.format:
                continue 
            line.append(sub.format)
                
            out.append(",".join(line))
    
    return "\n".join(out) 

###############################################################################

def zmi(self):
    if not check_role(self):
        return "You must have a manager role to run this script"

    servers = { 'plonegov' : 'plonegov-0000.proxy.pilotsystems.net',
                'villesetcommunes' : 'villesetcommunes.all2all.org:0000',
                'villesetcommunes3' : 'villesetcommunes3.all2all.org:0000',}
    import socket
    infos = self.Control_Panel.getServers()
    hostname = socket.gethostname()
    out = []
    server = 'localhost:0000'
    if infos and len(infos[0]) > 1:
        port = infos[0][1]
        out.append(port)
        port = port.replace('Port: ', '')
        if servers.has_key(hostname):
            server = servers[hostname]
        server = server.replace('0000', port)
        url = "http://%s/manage_main"%server
        out.append('<a href="%s">%s</a>'%(url,url))
        return self.REQUEST.RESPONSE.redirect(url)
    #out.append(infos[1])
    return '<br />\n'.join(out)

###############################################################################
def removeStep(self,step=''):
    """
        Remove an import step
    """
    from Products.CMFCore.utils import getToolByName
    out = []

    out.append("You can call the script with following parameters:\n")
    out.append("-> step=name of step to delete")
    out.append("##########################################################################################################")
    
    setup = getToolByName(self, 'portal_setup')

    ir = setup.getImportStepRegistry()

    out.append('before delete')
    out.append(str(ir.listSteps()))  # for debugging and seeing what steps are available

    # delete the offending step
    try:
        del ir._registered[step]
    except KeyError:
        pass

    import transaction
    transaction.commit()        

    out.append('after delete')
    out.append(str(ir.listSteps()))  # for debugging and seeing what steps are available
    return '<br />\n'.join(out)

###############################################################################
def removeRegisteredTool(self,tool=''):
    """
        Remove a tool
    """
    from Products.CMFCore.utils import getToolByName
    out = []

    out.append("You can call the script with following parameters:\n")
    out.append("-> tool=name of tool to delete")
    out.append("##########################################################################################################")
    
    setup = getToolByName(self, 'portal_setup')

    toolset = setup.getToolsetRegistry()

    out.append('before delete')
    out.append(str(toolset.listRequiredTools()))  

    # delete the offending step
    try:
        del toolset._required[tool]
    except KeyError:
        pass

    import transaction
    transaction.commit()        

    out.append('after delete')
    out.append(str(toolset.listRequiredTools()))
    return '<br />\n'.join(out)
