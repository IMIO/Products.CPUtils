from OFS.Application import Application
from Products.ExternalMethod.ExternalMethod import manage_addExternalMethod
from zope.i18nmessageid import MessageFactory


_ = MessageFactory("CPUtils")


def install(context):
    app = context.getSite()
    count = 0
    while not isinstance(app, Application) and count < 10:
        app = app.getParentNode()
        count += 1

    if not isinstance(app, Application):
        raise ValueError("Couldn't find parent Application")

    if not hasattr(app, 'cputils_install'):
        manage_addExternalMethod(app, 'cputils_install', '', 'CPUtils.utils', 'install')
    # we run this method
    app.cputils_install(app)
