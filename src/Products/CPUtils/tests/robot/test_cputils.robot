*** Settings ***
Documentation  External methods installed in the Zope root by the default profile.
Resource  cputils.robot
Test Setup  Open a manager browser with a document
Test Teardown  Close all browsers


*** Test Cases ***
A site manager gets the information of a document
    Run the external method  object_info
    Page should contain  current object id='doc'
    Page should contain  current object portal_type/meta_type/class='Document'

A site manager can't run a method reserved to the Zope admin
    Run the external method  del_object  doit=1
    Page should contain  ${NOT_ZOPE_ADMIN}
    The document exists

The Zope admin previews then deletes a document
    Log in as the Zope admin
    Run the external method  del_object
    Page should contain  Object deletion
    Page should contain  cputils_del_object?linki=0&doit=1
    Page should not contain  ${NOT_ZOPE_ADMIN}
    The document exists
    Run the external method  del_object  doit=1
    The document is deleted
