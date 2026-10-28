*** Settings ***
Documentation  Products.CPUtils keywords, built on the ui_plone${PLONE_MAJOR}.robot keywords.
...            Robot Framework 3.0 syntax (shared with the Plone 4.3 environment).
Resource  ui_plone${PLONE_MAJOR}.robot


*** Variables ***
${DOC_URL}  ${PLONE_URL}/doc
${NOT_ZOPE_ADMIN}  You must be a zope manager to run this script


*** Keywords ***
Open a manager browser with a document
    [Documentation]  Site Manager (autologin test user, not the Zope admin) and a Document "doc"
    Open test browser
    Enable autologin as  Manager
    Create content  type=Document  id=doc  title=My document

Log in as the Zope admin
    Log in with the login form  ${SITE_OWNER_NAME}  ${SITE_OWNER_PASSWORD}

Run the external method
    [Documentation]  External method of the Zope root, called on the document: cputils_<name>?<query>
    [Arguments]  ${name}  ${query}=
    Go to  ${DOC_URL}/cputils_${name}?${query}

The document exists
    Go to  ${DOC_URL}
    Page should contain  My document

The document is deleted
    Go to  ${DOC_URL}
    Page should contain  ${NOT_FOUND_TEXT}
