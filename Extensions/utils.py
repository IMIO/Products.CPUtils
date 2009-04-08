#utilities
def check_role(self, role='Manager', context=None):
    from Products.CMFCore.utils import getToolByName
    pms = getToolByName(self, 'portal_membership')
    return pms.getAuthenticatedMember().has_role(role, context)

###############################################################################

def install(self):
    """
        Install cputils methods where the user is (root of zope?)
    """
    from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod
    from AccessControl.SecurityManagement import getSecurityManager
    user = getSecurityManager().getUser()
    if not user.has_role('Manager'):
        return "You must be a zope manager to run this script"
    for method in ('object_info', 'audit_catalog'):
        method_name = 'cputils_'+method
        if not hasattr(self.aq_inner.aq_explicit, method_name):
            #without aq_explicit, if the id exists at a higher level, it is found !
            manage_addExternalMethod(self, method_name, '', 'CPUtils.utils', method)

###############################################################################

def pack_db(self, days=0):
    """
        pack a db of the zope instance
    """
    from Products.CMFCore.utils import getToolByName
    from AccessControl.SecurityManagement import getSecurityManager
    user = getSecurityManager().getUser()
    if not user.has_role('Manager'):
        return "You must be a zope manager to run this script"
    import time
    t=time.time()-days*86400
    db=self._p_jar.db()
    t=db.pack(t)
    return "well packed"

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


###############################################################################


###############################################################################

