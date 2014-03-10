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

__author__ = """Stephan GEULETTE <stephan.geulette@uvcw.be>, Gauthier BASTIEN <gbastien@commune.sambreville.be>"""
__docformat__ = 'plaintext'

from Products.CMFCore.utils import getToolByName

from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod
import logging

logger = logging.getLogger('CPUtils')

def install(self, reinstall=False):
    """ 
        Specific installation steps
    """
    portal = getToolByName(self, 'portal_url').getPortalObject()
    #Add of some external methods
    # pack_db method must not be added here
    for method in ('object_info', 'audit_catalog'):
        method_name = 'cputils_'+method
        if not hasattr(portal.aq_inner.aq_explicit, method_name):
            logger.info("REALLY Adding external method '%s'" % method_name)
            #without aq_explicit, if the id exists at a higher level, it is found !
            manage_addExternalMethod(self, method_name, '', 'CPUtils.utils', method)
    
def uninstall(self, reinstall=False):
    """
        Specific uninstallation steps
    """
    portal = getToolByName(self, 'portal_url').getPortalObject()
    #remove the external methods
    for method in ('object_info', 'audit_catalog'):
        method_name = 'cputils_'+method
        try:
            portal.manage_delObjects(method_name)
            logger.info("Deleted external method '%s'" % method_name)
        except AttributeError:
            logger.warn("The '%s' ExternalMethod could not be found, we continue..." % method_name)

