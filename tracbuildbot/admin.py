# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Max Kaskevich <maxim.kaskevich@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import *
from trac.admin.api import IAdminPanelProvider
from trac.perm import IPermissionRequestor
from trac.web.chrome import add_script, add_stylesheet
from trac.web import HTTPForbidden

from buildbot_api import BuildbotException
from buildbot_provider import BuildbotProvider


class BuildbotAdmin(Component, BuildbotProvider):
    implements(IAdminPanelProvider,IPermissionRequestor)

    # IPermissionRequestor
    def get_permission_actions(self):
        actions = ['BUILDBOT_BUILD']
        return actions + [('BUILDBOT_ADMIN', actions)]


    def get_admin_panels(self,req):
        if req.perm.has_permission('BUILDBOT_ADMIN'):
            yield('buildbot','Buildbot','options','Options')

    def render_admin_panel(self,req,category,page,path_info):
        if not req.perm.has_permission('BUILDBOT_ADMIN'):
            raise HTTPForbidden('You are not allowed to configure Buildbot plugin')
        if req.method == 'POST':
            options,errors = self._save_options(req.args)
            if not errors:
                # redirect here
                req.redirect(req.href(req.path_info))
        else:
            options,errors = self._get_options(),[]
        
        builders = []

        try:
            if not options or not 'base_url' in options:
                raise BuildbotException('Base url is required')

            builders = self.get_connector().get_builders()
        except BuildbotException as e:
            errors.append("Fix base config options. %s" % str(e).decode('utf-8', "replace"))
            t_data = {'options':options,'projects':{},'errors':errors}
            return 'buildbot_admin.html',t_data
        projects = []
        for build in builders:
            projects.append({
                'name': build,
                'url': options['base_url'] + "/builders/" + build,
                'page': dict({'checked':'true'})
                        if build in options.get('page_builders',[]) else {},
                'timeline': dict({'checked':'true'})
                            if build in options.get('timeline_builders',[]) else {},
                'source': options['sources'].get(build, ""),
            })
        add_stylesheet(req,'tracbuildbot/css/admin.css')
        t_data = {'options': options, 'projects' : projects,
                  'errors' : errors}
        return 'buildbot_admin.html',t_data

