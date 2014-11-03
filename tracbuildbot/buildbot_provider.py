# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Max Kaskevich <maxim.kaskevich@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import *
from buildbot_api import BuildbotConnector, BuildbotException
from buildbot_cache import DeferredBuildbotCache


class BuildbotProvider:
    __connector = BuildbotConnector()
    __cache = None

    def get_connector(self):
        options = self._get_options()
        BuildbotProvider.__connector.connect_to(options["base_url"])
        return BuildbotProvider.__connector

    def get_cache(self):
        if not BuildbotProvider.__cache:
            BuildbotProvider.__cache = DeferredBuildbotCache(self.env, self.get_connector())
        options = self._get_options()
        BuildbotProvider.__cache.connect_to(options['base_url'])
        return BuildbotProvider.__cache

    def _get_options(self):
        return dict({
                'base_url'         : self.config.get('buildbot','base_url'),
                'username'         : self.config.get('buildbot','username'),
                'password'         : self.config.get('buildbot','password'),
                'page_builders'    : self.config.getlist('buildbot','page_builders'),
                'timeline_builders': self.config.getlist('buildbot','timeline_builders'),
                'sources'          : dict([tuple(builder.split('=')) for builder in
                                           self.config.getlist('buildbot','sources')]),
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

        if args.get('page_builders', False):
            if type(args['page_builders']) is list:
                new_options['page_builders'] = args['page_builders']
            else:
                builder = args['page_builders']
                new_options['page_builders'] = [builder]
        else:
            new_options['page_builders'] = []

        if args.get('timeline_builders', False):
            if type(args['timeline_builders']) is list:
                new_options['timeline_builders'] = args['timeline_builders']
            else:
                builder = args['timeline_builders']
                new_options['timeline_builders'] = [builder]
        else:
            new_options['timeline_builders'] = []

        sources = dict()
        for name, value in args.iteritems():
            if name.endswith('_source'):
                sources[name[:-7]] = value
        new_options['sources'] = [builder + "=" + source
                                  for builder, source in sources.iteritems()]

        if not errors:
            for key,value in new_options.items():
                if type(value) is list:
                    value = ",".join(value)
                self.config.set('buildbot',key,value)
            self.config.save()
        return new_options,errors
