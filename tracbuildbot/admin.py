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
from buildbot_api import BuildbotConnection, BuildbotException
from trac.web.chrome import add_script, add_stylesheet
from trac.web import HTTPForbidden


class BuildbotSettings:
    def _get_options(self):
        return dict({
                'base_url':  self.config.get('buildbot','base_url'),
                'username':  self.config.get('buildbot','username'),
                'password':  self.config.get('buildbot','password'),
                'builds':    dict([tuple(builder.split('='))
                                   for builder in self.config.getlist('buildbot','builds')]
                                  )
        })

    def _save_options(self, args):
        errors = []
        new_options = {}
        if args.get('base_url',False):
            if args['base_url'][-1] == '/': # remove trailing slash
                args['base_url'] = args['base_url'][:-1]
            new_options['base_url'] = args['base_url']
        else:
            errors.append('Base url is required')
        if args.get('username',False):
            new_options['username'] = args['username']
        else:
            errors.append('Username is required')
        if args.get('password',False):
            new_options['password'] = args['password']
        else:
            errors.append('Password is required')
        if args.get('builds',False):
            if type(args['builds']) is list:
                new_options['builds'] = [builder + "=" + args['build_' + builder + '_source']
                                         for builder in args['builds']]
            else: # only one build was specified
                new_options['builds'] = [args['builds'] + "=" +
                                         args['build_'+ args['builds'] +'_source']]
        else:
            # no builds was specified
            new_options['builds'] = []
        if not errors:
            for key,value in new_options.items():
                if type(value) is list:
                    value = ",".join(value)
                self.config.set('buildbot',key,value)
            self.config.save()
        return new_options,errors


class BuildbotAdmin(Component, BuildbotSettings):
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
            bc = BuildbotConnection()
            bc.connect_to(options['base_url'])
            builders = bc.get_builders()
        except BuildbotException as e:
            errors.append("Fix base config options: %s" % e)
            t_data = {'options':options,'projects':{},'errors':errors}
            return 'buildbot_admin.html',t_data
        projects = []
        for build in builders:
            projects.append({
                    'name': build,
                    'url': "http://" + options['base_url'] + "/builders/" + build,
                    'checked': build in options.get('builds',[]),
                    'source': options['builds'].get(build, ""),
            })
        add_stylesheet(req,'tracbuildbot/css/admin.css')
        t_data = {'options':options,'projects':projects,'errors':errors}
        return 'buildbot_admin.html',t_data

