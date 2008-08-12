# -*- coding: utf-8 -*-
#
# File: config.py
#
# Copyright (c) 2006 by CommunesPlone
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

__author__ = """Gauthier BASTIEN <gbastien@commune.sambreville.be>"""
__docformat__ = 'plaintext'

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.exceptions import BadRequest

from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod
import logging

logger = logging.getLogger('contacts')

def install(self, reinstall=False):
    """ 
     We add the ExternalMethods and the contacts Plone Property Sheet
    """
    manage_addExternalMethod(self,
                             'getEmailAddress',
                             'getEmailAddress',
                             'contacts.dict',
                             'getEmailAddress')

    manage_addExternalMethod(self,
                             'getContacts',
                             'getContacts',
                             'contacts.dict',
                             'getContacts')

    manage_addExternalMethod(self,
                             'getSubjectsByContact',
                             'getSubjectsByContact',
                             'contacts.dict',
                             'getSubjectsByContact')

    manage_addExternalMethod(self,
                             'getLink',
                             'getLink',
                             'contacts.dict',
                             'getLink')

    #we add the Plone Property Sheet to portal_properties
    #we try/except every property as it could be a new property... during reinstallation
    try:
        self.portal_properties.addPropertySheet('contacts_properties', 'contacts Properties', propertysheet=None) 
    except BadRequest:
        logger.warn("The contacts_properties sheet already exists")
    #we add the properties to the Property Sheet
    try:
        self.portal_properties.contacts_properties.manage_addProperty('contacts', ('service1', 'service2', 'service3'), 'lines')
    except BadRequest:
        logger.warn("The contacts property already exists")
    try:
        self.portal_properties.contacts_properties.manage_addProperty('links', ('news', 'events', 'Members'), 'lines')
    except BadRequest:
        logger.warn("The links property already exists")
    try:
        self.portal_properties.contacts_properties.manage_addProperty('emails', ('email1@test.be', 'email1@test.be|email2@test.be', 'email1@test.be|email2@test.be|email3@test.be'), 'lines')
    except BadRequest:
        logger.warn("The emails property already exists")
    try:
        self.portal_properties.contacts_properties.manage_addProperty('subjects', ('subject1|subject2', 'subject', 'subject1|subject2|subject3'), 'lines')
    except BadRequest:
        logger.warn("The subjects property already exists")
    try:
        self.portal_properties.contacts_properties.manage_addProperty('sendToManager', False, 'boolean')
    except BadRequest:
        logger.warn("The sendToManager property already exists")
    try:
        self.portal_properties.contacts_properties.manage_addProperty('managerEmailAddress', '', 'string')
    except BadRequest:
        logger.warn("The managerEmailAddress property already exists")
    
def uninstall(self, reinstall=False):
    """ We remove the contacts Plone Property Sheet """
    #only remove contacts_properties if we are uninstalling the product
    #if we reinstall, we want to keep the changes !!!
    if not reinstall:
        try:
            self.portal_properties.manage_delObjects(['contacts_properties'])
        except BadRequest:
            #if we do not find the contacts_properties Property Sheet, we pass
            logger.warn("Unable to delete contacts_properties during uninstall of contacts!")
            pass
    
    #remove the external methods
    externalMethodsIds = ['getEmailAddress', 'getContacts', 'getSubjectsByContact', 'getLink']
    
    #get the portal as External Methods are added at the root of the site
    portal = getToolByName(self, 'portal_url').getPortalObject()
    for emi in externalMethodsIds:
        try:
            portal.manage_delObjects(emi)
        except AttributeError:
            logger.warn("The '%s' ExternalMethod could not be found, we continue..." % emi)