from Acquisition import aq_base
from io import TextIOWrapper
from Products.CMFCore import DirectoryView
from Products.validation.i18n import PloneMessageFactory as _
from Products.validation.i18n import recursiveTranslate
from Products.validation.i18n import safe_unicode
from Products.validation.validators.SupplValidators import MaxSizeValidator
from ZPublisher.HTTPRequest import FileUpload

import logging


logger = logging.getLogger("CPUtils")
logger.info("Installing Product")

DirectoryView.registerDirectory("skins", globals())
DirectoryView.registerDirectory("skins/CPUtils", globals())


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
        or isinstance(value, TextIOWrapper)
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
    MaxSizeValidator.__call__ = CallMaxSizeValidator
    logger.info("MaxSizeValidator MONKEY PATCHED!")
