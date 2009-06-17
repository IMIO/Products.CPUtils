# -*- coding: utf-8 -*-
#
# File: CPUtils.py
#
# Copyright (c) 2008 by CommunesPlone
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

__author__ = """Stephan GEULETTE <stephan.geulette@uvcw.be>"""
__docformat__ = 'plaintext'

import logging
logger = logging.getLogger('CPUtils')
logger.info('Installing Product')

import os, os.path
from Globals import package_home
from Products.CMFCore import utils as cmfutils

try: # New CMF
    from Products.CMFCore import permissions as CMFCorePermissions 
except: # Old CMF
    from Products.CMFCore import CMFCorePermissions

from Products.CMFCore import DirectoryView
from Products.CMFPlone.utils import ToolInit
from Products.Archetypes.atapi import *
from Products.Archetypes import listTypes
from Products.Archetypes.utils import capitalize
from config import *

DirectoryView.registerDirectory('skins', product_globals)
DirectoryView.registerDirectory('skins/CPUtils',
                                    product_globals)


from Products.CMFQuickInstallerTool.QuickInstallerTool import QuickInstallerTool
from Products.CMFCore.utils import getToolByName

def getPloneVersion():
    pv = ''
#    import pdb; pdb.set_trace()
    import Products.CMFPlone as cmfp
    plonedir = cmfp.__path__[0]
    if os.path.exists(plonedir):
        for name in ('version.txt', 'VERSION.txt', 'VERSION.TXT'):
            versionfile = os.path.join(plonedir,name)
            if os.path.exists(versionfile):
                file=open(versionfile, 'r')
                data=file.readline()
                file.close()
                pv = data.strip()
                return pv
    return pv

def getQIFilteringInformation(self):
    from AccessControl.SecurityManagement import getSecurityManager
    doFiltering = True
    hiddenProducts = ['def']
    shownProducts = ['def']
    user = getSecurityManager().getUser()
    portal = getToolByName(self, 'portal_url').getPortalObject()
    if user.__module__ == 'Products.PluggableAuthService.PropertiedUser':
        doFiltering = False
    if hasattr(portal, 'hiddenProducts'):
        hp = list(portal.hiddenProducts)
        hiddenProducts += [p.strip() for p in hp]
    if hasattr(portal, 'shownProducts'):
        sp = list(portal.shownProducts)
        shownProducts += [p.strip() for p in sp]
    return doFiltering, hiddenProducts, shownProducts

def listInstallableProducts25(self,skipInstalled=1):
    """List candidate CMF products for
    installation -> list of dicts with keys:(id,hasError,status)
    """
    try:
        from zpi.zope import not_installed, hot_plug
        #print 'Packman support(hotplug) installed'
    except ImportError:
        def not_installed(s): return []

    # reset the list of broken products
    self.errors = {}
    pids = self.Control_Panel.Products.objectIds() + not_installed(self)
    pids = [pid for pid in pids if self.isProductInstallable(pid)]

    if skipInstalled:
        installed=[p['id'] for p in self.listInstalledProducts(showHidden=1)]
        pids=[r for r in pids if r not in installed]

    from Products.CPUtils.__init__ import getQIFilteringInformation
    (doFiltering, hiddenProducts, shownProducts) = getQIFilteringInformation(self)

    res=[]
    for r in pids:
        p=self._getOb(r,None)
        if doFiltering and r in hiddenProducts and r not in shownProducts:
            continue
        if p:
            res.append({'id':r, 'status':p.getStatus(),
                        'hasError':p.hasError()})
        else:
            res.append({'id':r, 'status':'new', 'hasError':0})
    res.sort(lambda x,y: cmp(x.get('id',None),y.get('id',None)))
    return res

def listInstalledProducts25(self, showHidden=0):
    """Returns a list of products that are installed -> list of
    dicts with keys:(id, hasError, status, isLocked, isHidden,
    installedVersion)
    """
    pids = [o.id for o in self.objectValues()
            if o.isInstalled() and (o.isVisible() or showHidden)]

    from Products.CPUtils.__init__ import getQIFilteringInformation
    (doFiltering, hiddenProducts, shownProducts) = getQIFilteringInformation(self)

    res=[]
    for r in pids:
        p = self._getOb(r,None)
        if doFiltering and r in hiddenProducts and r not in shownProducts:
            continue
        res.append({'id':r, 'status':p.getStatus(),
                    'hasError':p.hasError(),
                    'isLocked':p.isLocked(),
                    'isHidden':p.isHidden(),
                    'installedVersion':p.getInstalledVersion()})
    res.sort(lambda x,y: cmp(x.get('id',None),y.get('id',None)))
    return res

def listInstallableProducts31(self, skipInstalled=True):
    """List candidate CMF products for installation -> list of dicts
       with keys:(id,title,hasError,status)
    """
    # reset the list of broken products
    self.errors = {}

    # Get product list from control panel
    pids = self.Control_Panel.Products.objectIds()
    pids = [p for p in pids if self.isProductInstallable(p)]

    # Get product list from the extension profiles
    profile_pids = self.listInstallableProfiles()
    profile_pids = [p for p in profile_pids if self.isProductInstallable(p)]
    for p in profile_pids:
        if p.startswith('Products.'):
            p = p[9:]
        if p not in pids:
            pids.append(p)

    if skipInstalled:
        installed=[p['id'] for p in self.listInstalledProducts(showHidden=True)]
        pids=[r for r in pids if r not in installed]

    from Products.CPUtils.__init__ import getQIFilteringInformation
    (doFiltering, hiddenProducts, shownProducts) = getQIFilteringInformation(self)

    res=[]
    for r in pids:
        if doFiltering and r in hiddenProducts and r not in shownProducts:
            continue
        p=self._getOb(r,None)
        name = r
        profile = self.getInstallProfile(r)
        if profile:
            name = profile['title']
        if p:
            res.append({'id':r, 'title':name, 'status':p.getStatus(),
                        'hasError':p.hasError()})
        else:
            res.append({'id':r, 'title':name,'status':'new', 'hasError':False})
    res.sort(lambda x,y: cmp(x.get('title', x.get('id', None)),
                             y.get('title', y.get('id', None))))
    return res

def listInstalledProducts31(self, showHidden=False):
    """Returns a list of products that are installed -> list of
    dicts with keys:(id, title, hasError, status, isLocked, isHidden,
    installedVersion)
    """
    pids = [o.id for o in self.objectValues()
            if o.isInstalled() and (o.isVisible() or showHidden)]
    pids = [pid for pid in pids if self.isProductInstallable(pid)]

    from Products.CPUtils.__init__ import getQIFilteringInformation
    (doFiltering, hiddenProducts, shownProducts) = getQIFilteringInformation(self)

    res=[]
    for r in pids:
        if doFiltering and r in hiddenProducts and r not in shownProducts:
            continue
        p = self._getOb(r,None)
        name = r
        profile = self.getInstallProfile(r)
        if profile:
            name = profile['title']
        
        res.append({'id':r,
                    'title':name,
                    'status':p.getStatus(),
                    'hasError':p.hasError(),
                    'isLocked':p.isLocked(),
                    'isHidden':p.isHidden(),
                    'installedVersion':p.getInstalledVersion()})
    res.sort(lambda x,y: cmp(x.get('title', x.get('id', None)),
                             y.get('title', y.get('id', None))))
    return res

def initialize(context):
    logger.info("MONKEY PATCHING QuickInstallerTool!")
    #import pdb; pdb.set_trace()
    plone_version = getPloneVersion()
    if not plone_version:
        logger.error('CMFPlone version NOT FOUND: MONKEY PATCH NOT APPLIED')
        return
    elif plone_version.startswith('2.5'):
        QuickInstallerTool.listInstallableProducts = listInstallableProducts25
        QuickInstallerTool.listInstalledProducts = listInstalledProducts25
    elif plone_version.startswith('3.1') or plone_version.startswith('3.2'):
        QuickInstallerTool.listInstallableProducts = listInstallableProducts31
        QuickInstallerTool.listInstalledProducts = listInstalledProducts31

    logger.info("QuickInstallerTool MONKEY PATCHED FOR PLONE %s!"%plone_version)
