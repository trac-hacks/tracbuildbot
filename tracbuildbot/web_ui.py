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
import json

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
import tools

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
        add_stylesheet(req,'tracbuildbot/css/futu_alert.css')
        add_script(req,'tracbuildbot/js/futu_alert.js')
        add_script(req,'tracbuildbot/js/buildbot.js')

        trac_path = self.config.get('project','url')
        if not trac_path.startswith('http'):
            trac_path = 'http://' + trac_path

        builders_str_list = ', '.join(["'%s'" % builder for builder in options['page_builders']])

        sources = ", ".join(["'%s': '%s'" % (builder, source) for builder, source in options['sources'].iteritems()])

        return "buildbot_builds.html", {"builders": options['page_builders'],
                                        "builders_str_list": builders_str_list,
                                        'view_build_buttons': str(add_build_buttons).lower(),
                                        'buildbot_url': options['base_url'],
                                        'trac_url': trac_path,
                                        'sources': sources,
                                        }, None

class BuildbotJsonApiHandler(Component, BuildbotSettings):
    """Renders pages with build results."""
    implements(IRequestHandler)

    #IRequestHandler methods
    def match_request(self, req):
        return re.match('/buildbot/json/lastbuilds$', req.path_info)

    def process_request(self, req):
        options = self._get_options()
        bc = BuildbotConnection(options['base_url'])
        last_builds = dict()
        builders = req.args['builders'].split(',')
        for builder in builders:
            try:
                build = bc.get_build(builder, -1)
            except Exception as e:
                #last_builds[builder] = str(e)
                pass
            else:
                last_builds[builder] = build

        content = json.dumps(last_builds, default=tools.date_handler)

        req.send_header('Content-Type', 'application/javascript')
        req.send_header('Content-Length', len(content))
        req.end_headers()
        req.write(content)

class BuildbotBuildHandler(Component, BuildbotSettings):
    implements(IRequestHandler)

    #IRequestHandler methods
    def match_request(self,req):
        return req.path_info == '/buildbot/build'

    def process_request(self,req):
        if not req.perm.has_permission('BUILDBOT_BUILD'):
            return 

        builder = req.args['builder']
        options = self._get_options()

        bc = BuildbotConnection(options['base_url'])
        try:
            bc.login(options['username'], options['password'])
            bc.build(builder)
        except BuildbotException as e:
            content = str(e)
            req.send_response(500)
        else:
            content = 'Build pending'
            req.send_response(200)

        req.send_header('Content-Type', 'text/html')
        req.send_header('Content-Length', len(content))
        req.end_headers()

        req.write(content)


