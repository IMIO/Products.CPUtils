#utilities
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
    
def sendmail(self, mailfrom, mailto, mailBody, subject = None):
    """"""    
    from Products.CMFCore.utils import getToolByName
    portal = getToolByName(self, 'portal_url').getPortalObject()
    mail_host = getattr(self, 'MailHost', None) 
    mail_host.secureSend(mailBody, mailto, mailfrom, subject=subject)

###############################################################################

def install(self):
    """
        Install cputils methods where the user is (root of zope?)
    """
    from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod
    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    methods = []
    for method in ('object_info', 'audit_catalog', 'change_user_properties', 'configure_fckeditor', 'list_users', 'checkPOSKey', 'store_user_properties', 'load_user_properties', 'recreate_users_groups', 'sync_properties'):
        method_name = 'cputils_'+method
        if not hasattr(self.aq_inner.aq_explicit, method_name):
            #without aq_explicit, if the id exists at a higher level, it is found !
            manage_addExternalMethod(self, method_name, '', 'CPUtils.utils', method)
            methods.append(method_name)
    return "Those methods have been added: "+' ,'.join(methods)

###############################################################################

def pack_db(self, days=0):
    """
        pack a db of the zope instance
    """
    out = []
    from Products.CMFCore.utils import getToolByName
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
    for u in portal.acl_users.getUserIds():
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
    for u in portal.acl_users.getUserIds():
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
#    userids = [ud['userid'] for ud in portal.acl_users.searchUsers()]
    count = 1
    for dic in portal.acl_users.searchUsers():
        user = dic['userid']
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
    from DateTime.DateTime import DateTime

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

def configure_fckeditor(self, default=1, allusers=1, custom=1):
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
            fckprops.manage_changeProperties(fck_custom_toolbar="[\n ['Templates','rtSpellCheck'],\n ['Cut','Copy','Paste','PasteText','PasteWord'],\n ['Undo','Redo','-','Find','Replace'],\n ['Bold','Italic','Underline','StrikeThrough'],\n ['OrderedList','UnorderedList'],\n ['JustifyLeft','JustifyCenter','JustifyRight','JustifyFull'],\n ['Link','Unlink'],\n ['Image','imgmapPopup','Table','Rule','SpecialChar'],\n ['Style','FontFormat','TextColor'],\n ['FitWindow'],['Source']\n]")
            fckprops.manage_changeProperties(fck_toolbar='Custom')

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
    for userid in portal.acl_users.getUserIds():
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
            newuser = prg.addMember(user.getUserId(), passwords[user.getUserId()], roles=user.getRoles(), domains=user.getDomains())
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
    if not errors:
        errors.append('No POSKey errors found')
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
    separator = ','
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

def correct_language(self, default='', search='all', dochange='', filter=0):
    """
        correct language objects, set as neutral if no translation exists
    """
    if not check_zope_admin():
        return "You must be a zope manager to run this script"

    lf = '\n'
#    lf = '<br />'
    separator = ','
    change_property = False
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
    out.append("-> filter=1 or filter=123 => filter numbers (default to all objects)<br />")
    out.append("-> &nbsp;&nbsp;&nbsp;&nbsp;1 => displays only canonical objects<br />")
    out.append("-> &nbsp;&nbsp;&nbsp;&nbsp;2 => displays only translations<br />")
    out.append("-> &nbsp;&nbsp;&nbsp;&nbsp;3 => displays if object language is different from default<br />")
    out.append("-> &nbsp;&nbsp;&nbsp;&nbsp;4 => displays unchanged objects<br />")
    out.append("-> dochange=1 => really do the change. By default, only prints changes<br />")
    out.append("by example /cputils_correct_language?default=fr&dochange=1</p>")
    out.append('<p>New value in <span class="red">red</span> will be changed</p>')

    if 'LinguaPlone' not in [p['id'] for p in pqi.listInstalledProducts()]:
        out.append("<p>LinguaPlone not installed ! Not necessary to do this operation</p>")
        return lf.join(out)
    
    kw = {}
    #kw['portal_type'] = ('Document','Link','Image','File','Folder','Large Plone Folder','Wrapper','Topic')
    #kw['review_state'] = ('private',) #'published'
    #kw['path'] = '/' # '/'.join(context.getPhysicalPath())
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
    out.append("<th>Path</th>")
    out.append("<th>New value</th>")
    out.append("</tr></thead><tbody>")

    #out.append("<tr><td>%s</td></tr>"%';'.join(filters))

    for brain in results:
        obj = brain.getObject()
        #we first search for translated objects: no change for those objects
        #condition= already language and canonical with translations
        if brain.Language and obj.isCanonical() and obj.getDeletableLanguages():
            if 1 in filters:
                out.append("""<tr><td>%s</td><td><a href="%s" target="_blank">%s</a></td><td class="green">canonical</td></tr>""" % (brain.Language, brain.getURL(), brain.getPath()))
        #condition= already language and not canonical = translation
        elif brain.Language and not obj.isCanonical():
            if 2 in filters:
                out.append("""<tr><td>%s</td><td><a href="%s" target="_blank">%s</a></td><td class="green">translation</td></tr>""" % (brain.Language, brain.getURL(), brain.getPath()))
        #no translation and language must be changed
        elif brain.Language != default:
            if 3 in filters:
                out.append("""<tr><td class="red">%s</td><td><a href="%s" target="_blank">%s</a></td><td class="red">%s</td></tr>""" % (brain.Language, brain.getURL(), brain.getPath(), default or "neutral"))
                if change_property:
                    obj.setLanguage(default)
                    obj.reindexObject()
        #no change
        elif 4 in filters:
            out.append("""<tr><td>%s</td><td><a href="%s" target="_blank">%s</a></td><td>unchanged</td></tr>""" % (brain.Language, brain.getURL(), brain.getPath()))

    out.append('</tbody></table>')

    return lf.join(out)
    
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
	    from plone.browserlayer.interfaces import ILocalBrowserLayerType
	    from Products.CMFCore.utils import getToolByName
	    from five.customerize.interfaces import ITTWViewTemplate
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
                    obj.portal_quickinstaller.installProducts(productName, reinstall=True) 
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
    
def send_adminMail(self, dochange='', subject='Aux administrateurs du site plone', bodyText=''):
    """
        send mail to all admin user
    """

    if not check_zope_admin():
        return "You must be a zope manager to run this script"
    
    out=[]

    send_mail=False
    if dochange not in ('', '0', 'False', 'false'):
        send_mail=True

    if not send_mail:
        out.append("The following changes are not applied: you must run the script with the parameter '...?dochange=1'")

    from Products.CMFPlone.utils import base_hasattr, safe_unicode
    import email.Message
    import email.Utils
    from email.Header import Header         
    
    #get all site on root or in first folder (by mountpoint)
    allSiteObj = get_all_site_objects(self) 
    for obj in allSiteObj:
        objid = obj.getId()      
        users_mail = []
        #get contact email
        properties_names = dict(obj.propertyItems())
        authorEmail = properties_names['email_from_address']
        if authorEmail:            
            users_mail.append(authorEmail)
        #get admin email      
        for userid in obj.acl_users.getUserIds():
            member = obj.portal_membership.getMemberById(userid)
            if member.has_role('Manager'):
                user_mail = member.getProperty('email')
                if user_mail != "" and user_mail not in users_mail:
                    users_mail.append(user_mail)
        objPath = ""
        for i in range(1,len(obj.getPhysicalPath())-1):
            objPath = objPath + obj.getPhysicalPath()[i] + '/'     
        out.append("EMAIL for site %s"%objPath+objid)     
        To = ""
        for user_mail in users_mail:
            out.append(user_mail) 
            if To != "":
                To = To + ';'
            To = To + user_mail
        if send_mail:
            mailMsg=email.Message.Message()
            mailMsg["To"]=To            
            mailMsg["From"]=authorEmail
            mailMsg["Subject"]=str(Header(safe_unicode(subject), 'utf8'))
            mailMsg["Date"]=email.Utils.formatdate(localtime=1)
            mailMsg["Message-ID"]=email.Utils.make_msgid()
            mailMsg["Mime-version"]="1.0"
            mailMsg["Content-type"]="text/plain"
            mailMsg.set_payload(safe_unicode(bodyText).encode('utf8'), 'utf8')
            mailMsg.epilogue="\n" # To ensure that message ends with newline
            out.append('From : %s, To : %s, Mail subject : %s, mail data : %s '%(authorEmail,To,mailMsg["Subject"],str(safe_unicode(bodyText).encode('utf8'))))

            try:
                sendmail(obj,authorEmail, To, mailMsg, subject = mailMsg['subject'])
            except Exception, e:
                # The email could not be sent, probably the specified address doesn't exist
                out.append("error in send mail !!!")
                continue        
   
    return '\n'.join(out)
    
###############################################################################

def checkInstance(self, isProductInstance=''):
    if not check_zope_admin():
        return 'checkInstance run with a non admin user: we go out'    
    try:
        out = []
        
        is_Product_Instance=False
        if isProductInstance not in ('', '0', 'False', 'false'):
            is_Product_Instance=True
        if is_Product_Instance:
            out.append('>> ---Start checkInstance on "product instance" in threat---')
        else:
            out.append('>> ---Start checkInstance "test instance" in threat---')

        allSiteObj = get_all_site_objects(self)  
        isProductInstance = self.getId()
        
        from Products.CMFCore.utils import getToolByName
        for obj in allSiteObj:
            objid = obj.getId()  
            objPath = ""
            for i in range(1,len(obj.getPhysicalPath())-1):
                objPath = objPath + obj.getPhysicalPath()[i] + '/'            
            out.append(">> Site in analyse : %s"%objPath+objid)     
            #1. Check if we are in debugMode (only for product instance)
            if is_Product_Instance:
                out.append(">> Check debugMode")
                if hasattr(obj,"portal_css"):                
                    if obj.portal_css.debugmode:
                        out.append("!! Css : %s"%obj.portal_css.debugmode)
                if hasattr(obj,"portal_javascripts"): 
                    if obj.portal_javascripts.debugmode:
                        out.append("!! Javascripts : %s"%obj.portal_javascripts.debugmode)
                if hasattr(obj,"portal_kss"): 
                    if obj.portal_kss.debugmode:
                        out.append("!! Kss : %s"%obj.portal_kss.debugmode) 
            #2. Check if robot.txt exist in test instance and not exist in product instance
            out.append(">> Check robots.txt")   
            if hasattr(obj,"portal_skins.custom"):            
                if is_Product_Instance and hasattr(obj.portal_skins.custom,"robots.txt"):
                    out.append("!! Have a file named 'robots.txt'")   
                elif not is_Product_Instance and not hasattr(obj.portal_skins.custom,"robots.txt"):
                    out.append("!! Haven't a file named 'robots.txt'") 
            #3. Check if hidden product properties exist
            out.append(">> Check hidden product properties")
            portal = getToolByName(obj, 'portal_url').getPortalObject()
            if not hasattr(portal, 'hiddenProducts'):
                out.append("!! No hidden product properties")            
            #4. Check if connexion plugins is activate
            out.append(">> Check connexion plugins")
            plugins = obj.acl_users.plugins
            auth_plugins = plugins.getAllPlugins(plugin_type='IAuthenticationPlugin')
            if not auth_plugins['active']:
                out.append('!! No connexion plugins is activate')           
            #5. Check if Ids is correct (without space)
            out.append(">> Check Ids")
            if objid.find(' ') >= 0:                
                out.append("!! this site (%s) contain space characters in id"%objid)            
            #6. Check if cache setup is installed (only for product instance)
            if is_Product_Instance:
                out.append(">> Check CacheSetup")
                if hasattr(obj,"portal_quickinstaller"):
                    if  not obj.portal_quickinstaller.isProductInstalled("CacheSetup"):
                        out.append("!! cache setup isn't installed")
            out.append("")
        return '\n'.join(out)
    except Exception, message:
        out.append("!! error in checkinstance %s"%str(message))
        return '\n'.join(out) 
