#utilities
def check_role(self, role='Manager', context=None):
    from Products.CMFCore.utils import getToolByName
    pms = getToolByName(self, 'portal_membership')
    return pms.getAuthenticatedMember().has_role(role, context)

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
    if not check_role(self):
        return "You must have a manager role to run this script"
    out = []
    from Products.CMFCore.utils import getToolByName
    from Products.CMFCore.WorkflowCore import WorkflowException
    try:
        purl = getToolByName(self, 'portal_url')
#        out.append("portal path='%s'" % purl.getPortalPath())
        out.append("current object path='/%s'" % '/'.join(purl.getRelativeContentPath(self)))
        out.append("current object id='%s'" % self.getId())
        out.append("current object portal type/class='%s'/'%s'" % (self.getPortalTypeName(),self.meta_type))
        out.append("folderish='%s'" % self.isPrincipiaFolderish)
        wtool = getToolByName(self, 'portal_workflow')
        try:
            workflows = ';'.join([wfw.getId() for wfw in wtool.getWorkflowsFor(self)])
            state = wtool.getInfoFor(self, 'review_state')
            transitions = ';'.join([trans['name'] for trans in wtool.getTransitionsFor(self)])
        except WorkflowException:
            workflows = '-'
            state = '-'
            transitions = '-'
        out.append("workflows='%s'" % workflows)
        out.append("state='%s'" % state)
        out.append("transitions='%s'" % transitions)
    except Exception, msg:
        out.append("! EXCEPTION !:%s"%msg)
    return '\n'.join(out)

###############################################################################



