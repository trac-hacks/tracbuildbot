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
                'force_regex'      : self.config.get('buildbot','force_regex'),
            })


    def _save_options(self, args):
        errors = []
        options = {}

        def save_str_option(option_name, required=False, label=None):
            if args.get(option_name, False):
                options[option_name] = args[option_name]
            elif required:
                errors.append('%s is required ' % (label if label else option_name))

        def save_list_option(option_name):
            if args.get(option_name, False):
                if type(args[option_name]) is list:
                    options[option_name] = args[option_name]
                else:
                    builder = args[option_name]
                    options[option_name] = [option_name]
            else:
                options[option_name] = []


        save_str_option('base_url', required=True)
        if 'base_url' in options:
            options['base_url'].strip("/")

        save_str_option('username')
        save_str_option('password')
        save_list_option('page_builders')
        save_list_option('timeline_builders')

        sources = dict()
        source_postfix = '_source'
        for name, value in args.iteritems():
            if name.endswith(source_postfix):
                sources[name[:-len(source_postfix)]] = value
        options['sources'] = [builder + "=" + source
                              for builder, source in sources.iteritems()]

        # check and save 
        if not errors:
            for key,value in options.items():
                if type(value) is list:
                    value = ",".join(value)
                self.config.set('buildbot',key,value)
            self.config.save()
        return options, errors
