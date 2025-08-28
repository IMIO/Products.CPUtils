Changelog
=========


1.26 (2025-08-28)
-----------------

- Completed `object_info`, display `externalIdentifier` if exists.
  [gbastien]

1.25 (2024-04-10)
-----------------

- Imported `safe_encode` from imio.pyutils.
  [sgeulette]

1.24 (2024-02-12)
-----------------

- Improved `set_attr`.
  [sgeulette]
- Added `obj_from_uid`
  [sgeulette]

1.23 (2023-06-26)
-----------------

- Added parameter `use_registry=False` to `configure_ckeditor`, set it to `True`
  with `collective.ckeditor 4.11+`.
  [gbastien]
- Removed file `CONTRIBUTORS.rst`.
  [gbastien]
- `utils.check_zope_admin` has been moved to `imio.helpers.security`.
  [gbastien]
- Removed `utils.safe_encode` as already imported from `imio.helpers.content`.
  [gbastien]

1.22 (2022-09-19)
-----------------

- Automatically install External methods at the root of Zope app.
  [odelaere]

1.21 (2022-03-15)
-----------------

- Modified del_objects.
  [sgeulette]
- Added parameter `removeWsc=1` to `utils.configure_ckeditor`, this will disable
  the WSC link (Spellcheck) in the scayt menu of CKeditor as it is broken for years.
  [gbastien]

1.20 (2021-11-08)
-----------------

- Completed `object_info`, display `UID` and class name
  (as `meta_type` is not more relevant with `DX`).
  [gbastien]

1.19 (2021-09-28)
-----------------

- Added `del_object` to bypass link integrity check.
  [sgeulette]
- Improved `set_attr` to set a None value
  [sgeulette]
- Added `get_user_pwd_hash` and `set_user_pwd_hash` methods
  [sgeulette]
- Added `check_groups_users` method
  [sgeulette]
- Do not break when generating output log in `utils.change_user_properties`,
  in some cases, like when using an LDAP, a `UnicodeDecodeError` may be raised.
  [gbastien]

1.18 (2021-04-21)
-----------------
- Added Check all catalog intids for registration method
  [fngaha]
- Fix for password validation that was validating the hash
  [bleybaert]
- Added uid method to display current uid
  [sgeulette]
- Modified ged ckeditor configuration
  [sgeulette]
- Added `filtering` option in `configure_ckeditor` method
  [sgeulette]
- Added `target` option in `object_link`
  [sgeulette]
- Added `show_object_relations` method to display zc relations
  [sgeulette]

1.17 (2020-04-02)
-----------------

- Add a function to cleanup documentviewer generated previews
  [mpeeters]
- Added redirect after order.
  [sgeulette]

1.16 (2019-08-23)
-----------------

- Corrected list_users.
  [sgeulette]
- Improved object_link function.
  [sgeulette]

1.15 (2019-06-08)
-----------------

- The list_users method returns also global roles of groups/users.
  [odelaere]

1.14 (2019-05-20)
-----------------

- Added function to construct link to object
  [sgeulette]
- Added function to set an attribute on context
  [sgeulette]
- Improved dv_conversion
  [sgeulette]
- Improved dv_images_size
  [sgeulette]
- Added script to remove dependency step from import registry
  [sgeulette]
- Improved configure_ckeditor and list_portlets
  [sgeulette]
- Improved order_folder
  [sgeulette]

1.13 (2017-11-27)
-----------------

- In utils.configure_ckeditor, removed FontSize from default
  PloneMeeting CKeditor toolbar.
  [gbastien]
- Update unlock_webdav_objects to search locked objects in context
  [sgeulette]

1.12 (2017-08-11)
-----------------

- Check Missing.Value on tobytes method. It's prevent error on bad indexed object on cputils_audit_catalog.
  [bsuttor]
- Added method check_blobs
  [sgeulette]
- Added del_objects method
  [sgeulette]

1.11 (2017-05-08)
-----------------

- list_users script: added fullname and email, added separator option
  [sgeulette]
- Added 'Subscript' and 'Superscript' to the CKeditor custom toolbar
  used for 'plonemeeting'.
  [gbastien]

1.10 (2017-01-24)
-----------------

- Improve zmi scripts for Docker instances.
  [bsuttor]
- Added correct_intids (Correct intids key references after a zodb change: mount point to main).
  [sgeulette]

1.9 (2017-01-17)
----------------

- Corrected default value.
  [sgeulette]
- Added method to change UID (after zmi import by example).
  [sgeulette]
- Added Link and Unlink in ckeditor config to configure correctly messagesviewlet
  [sgeulette]

1.8 (2016-11-24)
----------------

- configure_ckeditor : added buttons 'FontSize', 'NbSpace' and 'NbHyphen' and
  removed button 'Blockquote', from the default CKeditor custom toolbar used
  for 'plonemeeting'.
  [gbastien]
- resources_order : function to list resources and output order.
  [sgeulette]
- configure_ckeditor : disable tinymce resources.
  [sgeulette]
- load_site : load site during specified time
  [sgeulette]
- objects_stats : output as csv
  [sgeulette]
- fileSize : force format
  [sgeulette]
- dv_conversion : function to list documentviewer stats or do conversion
  [sgeulette]
- dv_images_size : return documentviewer blobs information
  [sgeulette]
- remove_empty_related_items : remove broken related items
  [bsuttor]
- creators : change recursively creators
  [sgeulette]

1.7 (2016-02-16)
----------------

- configure_ckeditor : added buttons 'Link', 'Unlink' and 'Image' to the
  default CKeditor custom toolbar used for 'plonemeeting'.
  [gbastien]

1.6 (2015-11-24)
----------------

- configure_ckeditor: added ged config, added scayt activation
  [sgeulette]
- list_users: output users without group
  [sgeulette]
- Added method to update version in portal_quickinstaller.
  [sgeulette]
- Added safe_encode method. Improved list_users
  [sgeulette]
- Updated listInstallableProducts for Plone 4.3.4 and Plone 4.3.7
  [sgeulette]
- Added method "list_objects" to view all objects path for specific type
  [boulch]

1.5 (2015-04-21)
----------------

- Added check_users method to check email validity.
  [sgeulette]


1.4 (2015-03-20)
----------------

- Added try except to avoid plone 4.3.3 to 4.3.4 migration error.
  [sgeulette]


1.3 (2015-02-24)
----------------

- Added method to clear and rebuild zc.relation.catalog
  [sgeulette]
- Added method to display portal types used in site
  [sgeulette]
- Added method to reset passwords
  [sgeulette]
- Modified user & group listing
  [sgeulette]
- Modified user properties export information
  [sgeulette]
- Added method to move or copy objects
  [sgeulette]
- Adapted CKEditor toolbar for PloneMeeting
  [gbastien]


1.2 (2014-09-01)
----------------

- Plone 4 compatibility Plone version detection
  [sgeulette]
- Corrected and improved views listing method
  [sgeulette]
- Improved users and groups migration method
  [sgeulette]


1.1 (2014-03-18)
----------------

- Added utils module.
  [sgeulette]


1.0 (2014-03-10)
----------------

- First release.
  [sgeulette]
