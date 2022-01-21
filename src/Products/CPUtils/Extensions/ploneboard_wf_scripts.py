# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.CPUtils.Extensions.utils import sendmail


# def notifyManagerByMail(self, state_change, **kw):
# """ WF script used for ploneboard_conversation_workflow """
# object = state_change['object']

# send_from_address_param = "support@communesplone.be"
# send_to_address_param = "support@communesplone.be"
# subject_param = "Nouvelle conversation '%s'" % object.Title()
# comment_param = "Une nouvelle conversation a été ajoutée à %s" % object.aboslute_url()

# try:
# plone_tool = getToolByName(self, 'plone_utils')
# host = plone_tool.getMailHost()
# encoding = plone_tool.getSiteEncoding()
# message = comment_param
# send_to_address = send_to_address_param
# send_from_address = send_from_address_param
# subject = subject_param
# return host.secureSend(message, send_to_address,
# send_from_address, subject=subject,
# subtype='plain', charset=encoding,
# debug=False, From=send_from_address)
# except Exception, message:
# print "There was a problem during the send of an e-mail for object : %s." % object
# print "The exception is : %s." % message

# return


def notifyConvMembersByMail(self, state_change, **kw):
    """
        This script is used to send mail to :
            * all persons participating to a conversation
            * a list of fixed emails (optional)
        To activate the functionality :
            1) go in the ZMI to "portal_workflow/ploneboard_comment_workflow/scripts"
            2) add an "External Method"
            3) complete the following information :
                . id = "notifyConvMembersByMail" or whatever you want
                . title = "notifyConvMembersByMail" or whatever you want
                . module name = "CPUtils.ploneboard_wf_scripts"
                . function name = "notifyConvMembersByMail"
            4) go in the ZMI to the appropriate transition (by example autopublish)
            5) select for an empty field "Script (before)" or "Script (after)" your External Method id
            6) add a property in portal_ploneboard with the following information
                . name = "auto_send_to_addresses"
                . type = "string"
                . value = "test@x.be test2@x.be" all addresses separated by spaces
    """
    object = state_change["object"]
    portal = getToolByName(self, "portal_url").getPortalObject()

    # get the container, the PloneboardConversation
    container = object.getParentNode()

    # we will build a list of e-mails to send to
    emails = []
    if portal.portal_ploneboard.hasProperty("auto_send_to_addresses"):
        emails = portal.portal_ploneboard.auto_send_to_addresses.strip().split()

    plone_tool = getToolByName(self, "plone_utils")
    mt = portal.portal_membership

    # loop on every comments...
    comments = portal.portal_catalog.searchResults(
        portal_type="PloneboardComment", path="/".join(container.getPhysicalPath())
    )
    i = 0
    for comment in comments:
        i = i + 1
        creator = comment.Creator
        user = mt.getMemberById(creator)
        if user is not None:
            email = user.getProperty("email")
            if email not in emails:
                emails.append(email)

    # we remove the e-mail of the current comment creator as it is not necessary for him to be warned
    creator = object.Creator()
    user = mt.getMemberById(creator)
    email = user.getProperty("email")
    emails.remove(email)

    send_from_address_param = portal.email_from_address
    send_to_address_param = emails
    if i == 1:
        # a new conversation has been started and contain only one comment
        subject_param = "Nouvelle conversation '%s'" % container.Title()
        comment_param = "Une nouvelle conversation '%s' a démarré à %s." % (
            container.Title(),
            container.absolute_url(),
        )
    else:
        subject_param = (
            "Nouveau commentaire pour la conversation '%s'" % container.Title()
        )
        comment_param = (
            "Un nouveau commentaire a été ajouté à la conversation '%s' à %s."
            % (container.Title(), container.absolute_url())
        )

    try:
        host = plone_tool.getMailHost()
        encoding = plone_tool.getSiteEncoding()
        message = comment_param
        send_to_address = ""
        mbcc = ",".join(send_to_address_param)
        send_from_address = send_from_address_param
        subject = subject_param
        # MUST BE REPLACED AS FOLLOWING METHOD
        host.secureSend(
            message,
            send_to_address,
            send_from_address,
            mbcc=mbcc,
            subject=subject,
            subtype="plain",
            charset=encoding,
            debug=False,
            From=send_from_address,
        )
        # print result
    except Exception, message:
        print "There was a problem during the send of an e-mail for object : %s." % object
        print "The exception is : %s." % message

    return


def notifyConvMembersByMailRIC(self, state_change, **kw):
    """
        This script is used to send mail to :
            * all persons participating to a conversation
            * a list of fixed emails (optional)
        To activate the functionality :
            1) go in the ZMI to "portal_workflow/ploneboard_comment_workflow/scripts"
            2) add an "External Method"
            3) complete the following information :
                . id = "notifyConvMembersByMail" or whatever you want
                . title = "notifyConvMembersByMail" or whatever you want
                . module name = "CPUtils.ploneboard_wf_scripts"
                . function name = "notifyConvMembersByMailRIC"
            4) go in the ZMI to the appropriate transition (by example autopublish)
            5) select for an empty field "Script (before)" or "Script (after)" your External Method id
            6) add a property in portal_ploneboard with the following information
                . name = "auto_send_to_addresses"
                . type = "string"
                . value = "test@x.be test2@x.be" all addresses separated by spaces
    """
    #    return  # WHEN REPLACING WORKFLOW
    object = state_change["object"]
    portal = getToolByName(self, "portal_url").getPortalObject()

    # get the container, the PloneboardConversation
    container = object.getParentNode()

    # we will build a list of e-mails to send to
    emails = []
    if portal.portal_ploneboard.hasProperty("auto_send_to_addresses"):
        emails = portal.portal_ploneboard.auto_send_to_addresses.strip().split()

    mt = portal.portal_membership

    # loop on every comments...
    comments = portal.portal_catalog.searchResults(
        portal_type="PloneboardComment", path="/".join(container.getPhysicalPath())
    )
    i = 0
    for comment in comments:
        i = i + 1
        creator = comment.Creator
        user = mt.getMemberById(creator)
        if user is not None:
            email = user.getProperty("email")
            if email not in emails:
                emails.append(email)

    # we remove the e-mail of the current comment creator as it is not necessary for him to be warned
    creator = object.Creator()
    user = mt.getMemberById(creator)
    email = user.getProperty("email")
    if email in emails:
        emails.remove(email)

    if i == 1:
        # a new conversation has been started and contain only one comment
        subject_param = "Nouvelle conversation '%s'" % container.Title()
        comment_param = "Une nouvelle conversation '%s' a démarré à %s." % (
            container.Title(),
            container.absolute_url(),
        )
    else:
        subject_param = (
            "Nouveau commentaire pour la conversation '%s'" % container.Title()
        )
        comment_param = (
            "Un nouveau commentaire a été ajouté à la conversation '%s' à %s."
            % (container.Title(), container.absolute_url())
        )

    sendmail(
        self,
        mfrom=portal.email_from_address,
        to="",
        body=comment_param,
        bcc=",".join(emails),
        subject=subject_param,
    )

    # object.manage_delLocalRoles(creator)
    object.manage_addLocalRoles(creator, ("Owner", "Editor",))
    return


def setCommentLocalRoles(self, state_change, **kw):
    """
        This script is used to set local roles on a comment, permitting only a comment owner to modify his comment.
        To activate the functionality :
            1) go in the ZMI to "portal_workflow/ploneboard_comment_workflow/scripts"
            2) add an "External Method"
            3) complete the following information :
                . id = "setCommentLocalRoles" or whatever you want
                . title = "setCommentLocalRoles" or whatever you want
                . module name = "CPUtils.ploneboard_wf_scripts"
                . function name = "setCommentLocalRoles"
            4) go in the ZMI to the appropriate transition (by example autopublish)
            5) select for an empty field "Script (before)" or "Script (after)" your External Method id
    """
    object = state_change["object"]
    # object.manage_delLocalRoles(creator)
    object.manage_addLocalRoles(object.Creator(), ("Owner", "Editor",))
    return
