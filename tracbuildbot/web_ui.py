# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Max Kaskevich <maxim.kaskevich@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import os
import re
import urlparse
import urllib2
from datetime import datetime

import pkg_resources
from trac.core import *
from trac.util.html import html
from trac.web import HTTPNotFound, HTTPBadGateway, HTTPForbidden
from trac.web.main import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.chrome import add_script, add_stylesheet

from admin import BuildbotSettings
from buildbot_api import BuildbotConnection, BuildbotException

class BuildbotChrome(Component):
    """Provides plugin templates and static resources."""
    implements(ITemplateProvider)

    # ITemplatesProvider methods
    def get_htdocs_dirs(self):
        """Return the directories containing static resources."""
        return [('tracbuildbot', pkg_resources.resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [pkg_resources.resource_filename(__name__, 'templates')]


class BuildbotPage(Component, BuildbotSettings):
    """Renders pages with build results."""
    implements(IRequestHandler,INavigationContributor)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'buildbot'

    def get_navigation_items(self, req):
        yield 'mainnav', 'buildbot', html.A('BuildBot', href=req.href.buildbot())

    #IRequestHandler methods
    def match_request(self, req):
        return re.match('/buildbot/?$',req.path_info)


    def process_request(self, req):
        add_build_buttons = False
        if req.perm.has_permission('BUILDBOT_BUILD'):
            add_build_buttons = True

        errors = []
        options = self._get_options()

        add_stylesheet(req,'tracbuildbot/css/buildbot.css')

        builds = {}
        try:
            if not options or not 'base_url' in options:
                raise BuildbotException('Base url is required')
            if not options or not 'page_builders' in options:
                raise BuildbotException("No builds to view")

            bc = BuildbotConnection(options['base_url'])
            for builder in options['page_builders']:
                builds[builder] = bc.get_build(builder, -1)
        except BuildbotException as e:
            errors.append("Fail to get builds info: %s" % e)
            return "buildbot_builds.html", {"builds": [],"errors":errors}, None

        trac_path = self.config.get('project','url')
        if not trac_path.startswith('http'):
            trac_path = 'http://' + trac_path

        builds_desc = []
        for builder, build  in builds.iteritems():
            build['builder'] = builder
            build["source"] = options['sources'].get(builder)
            if 'num' in build:
                build["url"] = ("http://%s/builders/%s/builds/%s" % 
                    (options['base_url'], builder, str(build['num'])))

            builds_desc.append(build)

        return "buildbot_builds.html", {"builds": builds_desc, "errors":errors, 
                                        'view_build_buttons': add_build_buttons,
                                        'trac_url': trac_path}, None

class BuildbotBuildHandler(Component, BuildbotSettings):
    implements(IRequestHandler)

    #IRequestHandler methods
    def match_request(self,req):
        match = re.match('/buildbot/build/(\w+)?$',req.path_info)
        if match:
            req.args['builder'] = match.group(1)
            return True


    def process_request(self,req):
        content = '<meta http-equiv="Refresh" content="0; URL=../../buildbot">'

        req.send_header('Status', 303)
        req.send_header('Location', '../../buildbot')
        req.end_headers()
        req.send_header('Content-Type', 'text/html')
        req.send_header('Content-Length', len(content))

        req.write(content)


        if not req.perm.has_permission('BUILDBOT_BUILD'):
            return 

        builder = req.args['builder']
        options = self._get_options()

        bc = BuildbotConnection()
        bc.login(options['username'], options['password'])
        bc.build(builder)


