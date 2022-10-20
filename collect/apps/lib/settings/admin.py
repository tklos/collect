from django.contrib import admin

from django.conf.locale.en import formats as en_formats
en_formats.DATETIME_FORMAT = 'Y-m-d H:i:s'


ordering = {
    'Users': 0,
    'Devices': 1,
    'Runs': 2,
    'Measurements': 3,
}


def get_app_list(self, request):
    """
    Return a sorted list of all the installed apps that have been
    registered in this site.
    """
    app_dict = self._build_app_dict(request)
    app_dict = {k: v for k, v in app_dict.items() if v['name'] in ordering}

    # Sort the apps alphabetically.
    # app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())
    app_list = sorted(app_dict.values(), key=lambda x: ordering[x['name']])

    # Sort the models alphabetically within each app.
    for app in app_list:
        app['models'].sort(key=lambda x: x['name'])

    return app_list


import types
admin.site.get_app_list = types.MethodType(get_app_list, admin.site)

