
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

from trac.core import *
from trac.timeline import ITimelineEventProvider
from trac.web.chrome import add_script, add_stylesheet
from genshi.builder import tag

from buildbot_api import BuildbotException
from buildbot_provider import BuildbotProvider


class BuildbotTimeline(Component, BuildbotProvider):
    """Provides timeline events"""
    implements(ITimelineEventProvider)

    # ITimelineEventProvider methods
    def get_timeline_filters(self, req):
        """Returns a list of filters that this event provider supports.

        Full description here http://trac.edgewall.org/browser/trunk/trac/timeline/api.py
        """
        yield ('buildbot', 'Buildbot Builds')

    def get_timeline_events(self, req, start, stop, filters):
        """Returns a list of events in the time range given by the `start` and
        `stop` parameters.

        Full description here http://trac.edgewall.org/browser/trunk/trac/timeline/api.py
        """
        if 'buildbot' not in filters:
            return

        options = self._get_options()
        if not options.get('timeline_builders',True):
            return

        all_builds = []
        builders = options['timeline_builders']
        try:
            if not options or not 'base_url' in options:
                raise BuildbotException('Base url is required')

            cache = self.get_cache()
            cache.cache(builders)
            all_builds = cache.get_builds(builders, start, stop)
        except BuildbotException as e:
            self.log.error("tracbuildbot: fail to get builds %s" % e)
            return 

        add_stylesheet(req,'tracbuildbot/css/buildbot.css')
        for build in all_builds:
            timestamp = build['finish']
            build["source"] = options['sources'].get(build['builder'])
            build["url"] = ("%s/builders/%s/builds/%s" % 
                (options['base_url'], build['builder'], build['num']))
            yield build['status'], timestamp, 'buildbot server', build

    def render_timeline_event(self, context, field, event):
        """Display the title of the event in the given context.

        Full description here http://trac.edgewall.org/browser/trunk/trac/timeline/api.py
        """
        if field == 'url':
            return event[3]['url']
        elif field == 'title':
            return "Build %s #%s was %s" % (event[3]['builder'], event[3]['num'], event[0])
        elif field == 'description':
            data = event[3]
            msg = tag.span()
            if data['source'] and data["rev"]:
                rev_msg = tag.div("rev: ",
                    tag.a(data['rev'][:7], href=context.href("/browser/%s" % data['source'], rev=data['rev'])),
                    " ",    
                    tag.a(tag.img(src=context.href("/chrome/common/changeset.png")),
                          href=context.href("/changeset/%s/%s" % (data['rev'], data['source'])))
                    )
                msg.append(rev_msg)

            if 'error' in event[3] and  event[3]['error']:
                error_msg = tag.div(event[3]['error'], " ")
                if 'error_log' in event[3] and event[3]['error_log']:
                    error_msg.append(tag.a("Log", href=event[3]['error_log']))
                msg.append(error_msg)
            return msg
