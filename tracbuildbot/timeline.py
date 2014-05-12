
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
from datetime import datetime

from trac.core import *
from trac.timeline import ITimelineEventProvider
from trac.web.chrome import add_script, add_stylesheet
from trac.util.datefmt import localtz
from genshi.builder import tag

from admin import BuildbotSettings
from buildbot_api import BuildbotConnection, BuildbotException


class BuildbotTimeline(Component, BuildbotSettings):
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

        all_builds = {}
        try:
            if not options or not 'base_url' in options:
                raise BuildbotException('Base url is required')
            bc = BuildbotConnection(options['base_url'])
            all_builds = bc.get_all_builds(options['timeline_builders'])
        except BuildbotException as e:
            return 

        trac_path = self.config.get('project','url')
        if not trac_path.startswith('http'):
            trac_path = 'http://' + trac_path

        for builder, builds in all_builds.iteritems():
            for number, build in builds['builds']['_all'].iteritems():
                if not 'times' in build:
                    continue
                if not (len(build['times']) > 1 and type(build['times'][1]) == float):
                    continue
                event_date = datetime.fromtimestamp(int(build['times'][1]))
                event_date = event_date.replace(tzinfo=localtz)

                if (event_date < start) or (event_date > stop): continue

                event_status = "successful" if build['results'] == 0 else "failed"

                data = dict({"builder": builder,
                             "source": options['sources'].get(builder),
                             "num": number,
                             "url": "http://" + options['base_url'] + "/builders/"
                             + builder + "/builds/" + str(number),
                             })
                for prop in build['properties']:
                    if prop[0] == 'got_revision' and prop[1] != "":
                        data["rev"] = prop[1]
                        break

                if event_status == "failed":
                    data['error'] = ', '.join(build['text'])
                    try:
                        for step in build['steps']:
                            if "results" in step and step["results"][0] != 0 and step["results"][0] != 3:
                                data['error_log'] = step['logs'][0][1]
                                break
                    except (IndexError, KeyError):
                        pass


                yield event_status, event_date, 'buildbot server', data

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
            msg = tag.div()
            if data['source'] and "rev" in data:                
                rev_msg = tag.div(
                    tag.a("revision", href=context.href("/browser/%s" % data['source'], rev=data['rev'])),
                    " ",    
                    tag.a("changeset", href=context.href("/changeset/%s/%s" % (data['rev'], data['source'])))
                    )
                msg.append(rev_msg)

            if 'error' in event[3]:
                error_msg = tag.div(event[3]['error'], " ")
                if 'error_log' in event[3]:
                    error_msg.append(tag.a("Log", href=event[3]['error_log']))
                msg.append(error_msg)
            return msg
