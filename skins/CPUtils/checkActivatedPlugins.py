plugins = context.acl_users.plugins

auth_plugins = plugins.getAllPlugins(plugin_type='IAuthenticationPlugin')
return list(auth_plugins['active'])
