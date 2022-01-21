from Acquisition import aq_base
from config import PLONE_VERSION
from config import product_globals
from Products.CMFCore import DirectoryView
from Products.CMFCore.utils import getToolByName
from Products.CMFQuickInstallerTool.QuickInstallerTool import QuickInstallerTool
from Products.validation.validators.SupplValidators import MaxSizeValidator
from ZPublisher.HTTPRequest import FileUpload

import logging


logger = logging.getLogger("CPUtils")
logger.info("Installing Product")

try:
    from Products.validation.i18n import PloneMessageFactory as _
    from Products.validation.i18n import recursiveTranslate
    from Products.validation.i18n import safe_unicode
except ImportError:
    pass

try:
    from Products.CMFQuickInstallerTool.utils import get_packages
except ImportError:
    pass


DirectoryView.registerDirectory("skins", product_globals)
DirectoryView.registerDirectory("skins/CPUtils", product_globals)


def getQIFilteringInformation(self):
    from AccessControl.SecurityManagement import getSecurityManager

    doFiltering = True
    hiddenProducts = ["def"]
    shownProducts = ["def"]
    user = getSecurityManager().getUser()
    portal = getToolByName(self, "portal_url").getPortalObject()
    if user.__module__ == "Products.PluggableAuthService.PropertiedUser":
        doFiltering = False
    if hasattr(portal, "hiddenProducts"):
        hp = list(portal.hiddenProducts)
        hiddenProducts += [p.strip() for p in hp]
    if hasattr(portal, "shownProducts"):
        sp = list(portal.shownProducts)
        shownProducts += [p.strip() for p in sp]
    return doFiltering, hiddenProducts, shownProducts


def listInstallableProducts25(self, skipInstalled=1):
    """List candidate CMF products for
    installation -> list of dicts with keys: (id, hasError, status)
    """
    try:
        from zpi.zope import not_installed

        # print 'Packman support(hotplug) installed'
    except ImportError:

        def not_installed(s):
            return []

    # reset the list of broken products
    self.errors = {}
    pids = self.Control_Panel.Products.objectIds() + not_installed(self)
    pids = [pid for pid in pids if self.isProductInstallable(pid)]

    if skipInstalled:
        installed = [p["id"] for p in self.listInstalledProducts(showHidden=1)]
        pids = [r for r in pids if r not in installed]

    from Products.CPUtils.__init__ import getQIFilteringInformation

    (doFiltering, hiddenProducts, shownProducts) = getQIFilteringInformation(self)

    res = []
    for r in pids:
        p = self._getOb(r, None)
        if doFiltering and r in hiddenProducts and r not in shownProducts:
            continue
        if p:
            res.append({"id": r, "status": p.getStatus(), "hasError": p.hasError()})
        else:
            res.append({"id": r, "status": "new", "hasError": 0})
    res.sort(lambda x, y: cmp(x.get("id", None), y.get("id", None)))
    return res


def listInstalledProducts25(self, showHidden=0):
    """Returns a list of products that are installed -> list of
    dicts with keys: (id, hasError, status, isLocked, isHidden,
    installedVersion)
    """
    pids = [
        o.id
        for o in self.objectValues()
        if o.isInstalled() and (o.isVisible() or showHidden)
    ]

    from Products.CPUtils.__init__ import getQIFilteringInformation

    (doFiltering, hiddenProducts, shownProducts) = getQIFilteringInformation(self)

    res = []
    for r in pids:
        p = self._getOb(r, None)
        if doFiltering and r in hiddenProducts and r not in shownProducts:
            continue
        res.append(
            {
                "id": r,
                "status": p.getStatus(),
                "hasError": p.hasError(),
                "isLocked": p.isLocked(),
                "isHidden": p.isHidden(),
                "installedVersion": p.getInstalledVersion(),
            }
        )
    res.sort(lambda x, y: cmp(x.get("id", None), y.get("id", None)))
    return res


def listInstallableProducts31(self, skipInstalled=True):
    """List candidate CMF products for installation -> list of dicts
       with keys: (id, title, hasError, status)
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
        if p.startswith("Products."):
            p = p[9:]
        if p not in pids:
            pids.append(p)

    if skipInstalled:
        installed = [i["id"] for i in self.listInstalledProducts(showHidden=True)]
        pids = [r for r in pids if r not in installed]

    from Products.CPUtils.__init__ import getQIFilteringInformation

    (doFiltering, hiddenProducts, shownProducts) = getQIFilteringInformation(self)

    res = []
    for r in pids:
        if doFiltering and r in hiddenProducts and r not in shownProducts:
            continue
        p = self._getOb(r, None)
        name = r
        profile = self.getInstallProfile(r)
        if profile:
            name = profile["title"]
        if p:
            res.append(
                {
                    "id": r,
                    "title": name,
                    "status": p.getStatus(),
                    "hasError": p.hasError(),
                }
            )
        else:
            res.append({"id": r, "title": name, "status": "new", "hasError": False})
    res.sort(
        lambda x, y: cmp(
            x.get("title", x.get("id", None)), y.get("title", y.get("id", None))
        )
    )
    return res


def listInstalledProducts31(self, showHidden=False):
    """Returns a list of products that are installed -> list of
    dicts with keys: (id, title, hasError, status, isLocked, isHidden,
    installedVersion)
    """
    pids = [
        o.id
        for o in self.objectValues()
        if o.isInstalled() and (o.isVisible() or showHidden)
    ]
    pids = [pid for pid in pids if self.isProductInstallable(pid)]

    from Products.CPUtils.__init__ import getQIFilteringInformation

    (doFiltering, hiddenProducts, shownProducts) = getQIFilteringInformation(self)

    res = []
    for r in pids:
        if doFiltering and r in hiddenProducts and r not in shownProducts:
            continue
        p = self._getOb(r, None)
        name = r
        profile = self.getInstallProfile(r)
        if profile:
            name = profile["title"]

        res.append(
            {
                "id": r,
                "title": name,
                "status": p.getStatus(),
                "hasError": p.hasError(),
                "isLocked": p.isLocked(),
                "isHidden": p.isHidden(),
                "installedVersion": p.getInstalledVersion(),
            }
        )
    res.sort(
        lambda x, y: cmp(
            x.get("title", x.get("id", None)), y.get("title", y.get("id", None))
        )
    )
    return res


def listInstallableProducts40(self, skipInstalled=True):
    """List candidate CMF products for installation -> list of dicts
       with keys: (id, title, hasError, status)
    """
    # reset the list of broken products
    try:
        self.errors = {}
    except AttributeError:
        pass

    # Returns full names with Products. prefix for all packages / products
    packages = get_packages()

    pids = []
    for p in packages:
        if not self.isProductInstallable(p):
            continue
        if p.startswith("Products."):
            p = p[9:]
        pids.append(p)

    # Get product list from the extension profiles
    profile_pids = self.listInstallableProfiles()

    for p in profile_pids:
        if p in pids or p in packages:
            continue
        if not self.isProductInstallable(p):
            continue
        pids.append(p)

    if skipInstalled:
        installed = [p["id"] for p in self.listInstalledProducts(showHidden=True)]
        pids = [r for r in pids if r not in installed]

    from Products.CPUtils.__init__ import getQIFilteringInformation

    (doFiltering, hiddenProducts, shownProducts) = getQIFilteringInformation(self)

    res = []
    for r in pids:
        if doFiltering and r in hiddenProducts and r not in shownProducts:
            continue
        p = self._getOb(r, None)
        name = r
        profile = self.getInstallProfile(r)
        if profile:
            name = profile["title"]
        if p:
            res.append(
                {
                    "id": r,
                    "title": name,
                    "status": p.getStatus(),
                    "hasError": p.hasError(),
                }
            )
        else:
            res.append({"id": r, "title": name, "status": "new", "hasError": False})
    res.sort(
        lambda x, y: cmp(
            x.get("title", x.get("id", None)), y.get("title", y.get("id", None))
        )
    )
    return res


def listInstallableProducts434(self, skipInstalled=True):
    """List candidate CMF products for installation -> list of dicts
       with keys: (id, title, hasError, status)
    """
    # reset the list of broken products
    if getattr(self, "_v_errors", True):
        self._v_errors = {}

    # Returns full names with Products. prefix for all packages / products
    packages = get_packages()

    pids = []
    for p in packages:
        if not self.isProductInstallable(p):
            continue
        if p.startswith("Products."):
            p = p[9:]
        pids.append(p)

    # Get product list from the extension profiles
    profile_pids = self.listInstallableProfiles()

    for p in profile_pids:
        if p in pids or p in packages:
            continue
        if not self.isProductInstallable(p):
            continue
        pids.append(p)

    if skipInstalled:
        installed = [p["id"] for p in self.listInstalledProducts(showHidden=True)]
        pids = [r for r in pids if r not in installed]

    from Products.CPUtils.__init__ import getQIFilteringInformation

    (doFiltering, hiddenProducts, shownProducts) = getQIFilteringInformation(self)

    res = []
    for r in pids:
        if doFiltering and r in hiddenProducts and r not in shownProducts:
            continue
        p = self._getOb(r, None)
        name = r
        profile = self.getInstallProfile(r)
        if profile:
            name = profile["title"]
        if p:
            res.append(
                {
                    "id": r,
                    "title": name,
                    "status": p.getStatus(),
                    "hasError": p.hasError(),
                }
            )
        else:
            res.append({"id": r, "title": name, "status": "new", "hasError": False})
    res.sort(
        lambda x, y: cmp(
            x.get("title", x.get("id", None)), y.get("title", y.get("id", None))
        )
    )
    return res


def listInstallableProducts437(self, skipInstalled=True):
    """List candidate CMF products for installation -> list of dicts
       with keys:(id,title,hasError,status)
    """
    self._init_errors(reset=True)

    # Returns full names with Products. prefix for all packages / products
    packages = get_packages()

    pids = []
    for pkg in packages:
        if not self.isProductInstallable(pkg):
            continue
        if pkg.startswith("Products."):
            pkg = pkg[9:]
        pids.append(pkg)

    # Get product list from the extension profiles
    profile_pids = self.listInstallableProfiles()

    for pp in profile_pids:
        if pp in pids or pp in packages:
            continue
        if not self.isProductInstallable(pp):
            continue
        pids.append(pp)

    from Products.CPUtils.__init__ import getQIFilteringInformation

    (doFiltering, hiddenProducts, shownProducts) = getQIFilteringInformation(self)

    if skipInstalled:
        installed = [p["id"] for p in self.listInstalledProducts(showHidden=True)]
        pids = [r for r in pids if r not in installed]

    res = []
    for pid in pids:
        if doFiltering and pid in hiddenProducts and pid not in shownProducts:
            continue
        installed_product = self._getOb(pid, None)
        name = pid
        profile = self.getInstallProfile(pid)
        if profile:
            name = profile["title"]
        record = {"id": pid, "title": name}
        if installed_product:
            record["status"] = installed_product.getStatus()
            record["hasError"] = installed_product.hasError()
        else:
            record["status"] = "new"
            record["hasError"] = False
        res.append(record)
    res.sort(
        lambda x, y: cmp(
            x.get("title", x.get("id", None)), y.get("title", y.get("id", None))
        )
    )
    return res


def CallMaxSizeValidator(self, value, *args, **kwargs):
    instance = kwargs.get("instance", None)
    field = kwargs.get("field", None)
    type_doc = instance.getPortalTypeName().replace(" ", "").lower() + "_maxsize"
    # get max size
    if "maxsize" in kwargs:
        maxsize = kwargs.get("maxsize")
    elif hasattr(aq_base(instance), "getMaxSizeFor"):
        maxsize = instance.getMaxSizeFor(field.getName())
    elif hasattr(field, "maxsize"):
        maxsize = field.maxsize
    elif hasattr(instance, type_doc):
        maxsize = getattr(instance, type_doc)
    else:
        # set to given default value (default defaults to 0)
        maxsize = self.maxsize

    if not maxsize:
        return True

    # calculate size
    elif (
        isinstance(value, FileUpload)
        or isinstance(value, file)
        or hasattr(aq_base(value), "tell")
    ):
        value.seek(0, 2)  # eof
        size = value.tell()
        value.seek(0)
    else:
        try:
            size = len(value)
        except TypeError:
            size = 0
    size = float(size)
    sizeMB = size / (1024 * 1024)

    if sizeMB > maxsize:
        msg = _(
            "Validation failed($name: Uploaded data is too large: ${size}MB (max ${max}MB)",
            mapping={
                "name": safe_unicode(self.name),
                "size": safe_unicode("%.3f" % sizeMB),
                "max": safe_unicode("%.3f" % maxsize),
            },
        )
        return recursiveTranslate(msg, **kwargs)
    else:
        return True


def initialize(context):
    logger.info("ADDING MONKEY PATCHS !")
    if not PLONE_VERSION:
        logger.error("CMFPlone version NOT FOUND: MONKEY PATCH NOT APPLIED")
        return
    elif PLONE_VERSION.startswith("2.5"):
        QuickInstallerTool.listInstallableProducts = listInstallableProducts25
        QuickInstallerTool.listInstalledProducts = listInstalledProducts25
        logger.info("QuickInstallerTool MONKEY PATCHED FOR PLONE %s!" % PLONE_VERSION)
    elif PLONE_VERSION.startswith("3."):
        QuickInstallerTool.listInstallableProducts = listInstallableProducts31
        QuickInstallerTool.listInstalledProducts = listInstalledProducts31
        logger.info("QuickInstallerTool MONKEY PATCHED FOR PLONE %s!" % PLONE_VERSION)
        MaxSizeValidator.__call__ = CallMaxSizeValidator
        logger.info("MaxSizeValidator MONKEY PATCHED FOR PLONE %s!" % PLONE_VERSION)
    elif PLONE_VERSION < "4.3.4":
        QuickInstallerTool.listInstallableProducts = listInstallableProducts40
        QuickInstallerTool.listInstalledProducts = listInstalledProducts31
        logger.info("QuickInstallerTool MONKEY PATCHED FOR PLONE %s!" % PLONE_VERSION)
        MaxSizeValidator.__call__ = CallMaxSizeValidator
        logger.info("MaxSizeValidator MONKEY PATCHED FOR PLONE %s!" % PLONE_VERSION)
        try:
            # Patching tinymce to load as html in Ploneboard
            from Products.TinyMCE.utility import TinyMCE

            old_getContentType = TinyMCE.getContentType

            def getContentType(self, object=None, field=None, fieldname=None):
                if (
                    object is not None
                    and fieldname == "text"
                    and object.meta_type
                    in ("PloneboardForum", "PloneboardConversation")
                ):
                    return "text/html"
                return old_getContentType(
                    self, object=object, field=field, fieldname=fieldname
                )

            # TinyMCE.getContentType = getContentType
            logger.info(
                "TinyMCE getContentType MONKEY PATCHED FOR PLONE %s!" % PLONE_VERSION
            )
        except BaseException:
            pass
    elif PLONE_VERSION >= "4.3.4":
        QuickInstallerTool.listInstallableProducts = listInstallableProducts434
        QuickInstallerTool.listInstalledProducts = listInstalledProducts31
        logger.info("QuickInstallerTool MONKEY PATCHED FOR PLONE %s!" % PLONE_VERSION)
        MaxSizeValidator.__call__ = CallMaxSizeValidator
        logger.info("MaxSizeValidator MONKEY PATCHED FOR PLONE %s!" % PLONE_VERSION)
    elif PLONE_VERSION >= "4.3.7":
        QuickInstallerTool.listInstallableProducts = listInstallableProducts437
        QuickInstallerTool.listInstalledProducts = listInstalledProducts31
        logger.info("QuickInstallerTool MONKEY PATCHED FOR PLONE %s!" % PLONE_VERSION)
        MaxSizeValidator.__call__ = CallMaxSizeValidator
        logger.info("MaxSizeValidator MONKEY PATCHED FOR PLONE %s!" % PLONE_VERSION)
