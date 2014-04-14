import random
from base import *
from bnw.core.base import config
import bnw.core.bnw_objects as objs


class SimpleSetting(object):
    def __init__(self, default=None):
        self.default = default

    def get(self, request, name):
        setts = request.user.get('settings', {})
        return setts.get(name, self.default)

    def write(self, request, name, value):
        if len(value) > 2048:
            return False, ('%s value is too long.' % (name,))
        objs.User.mupdate({'name': request.user['name']},
                          {'$set': {'settings.' + name: value}})
        return (True,)


class ServiceJidSetting(SimpleSetting):
    def get(self, request, name):
        setts = request.user.get('settings', {})
        return setts.get(name, config.srvc_name)

    def write(self, request, name, value):
        return SimpleSetting.write(self, request, name, request.to.userhost())

optionnames = {
    'usercss': SimpleSetting(),
    'password': SimpleSetting(),
    'servicejid': ServiceJidSetting(),
    'baseurl': SimpleSetting(),
    'about': SimpleSetting(),
}


@require_auth
def cmd_set(request, **kwargs):
    if not kwargs:
        # Show current settings.
        current = {}
        for n, v in optionnames.iteritems():
            current[n] = v.get(request, n)
        return dict(ok=True, format='settings', settings=current)
    else:
        if 'name' in kwargs:
            # Simplified interface.
            name, value = kwargs['name'], kwargs['value']
            if value is None:
                value = ''
        else:
            # Redeye interface.
            name, value = kwargs.items()[0]
        if not name in optionnames:
            return dict(ok=False, desc='Unknown setting: %s' % kwargs['name'])
        else:
            res = optionnames[name].write(request, name, value)
            if not res[0]:
                return dict(ok=False, desc=res[1])
        return dict(ok=True, desc='Settings updated.')
