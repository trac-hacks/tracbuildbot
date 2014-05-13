# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Max Kaskevich <maxim.kaskevich@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import socket
import httplib
import json
import urllib
from datetime import datetime


def singleton(cls):
    instances = {}
    def getinstance(*args):
        if cls not in instances:
            instances[cls] = cls(*args)
        return instances[cls]
    return getinstance

class BuildbotException(Exception):
    def __init__(self, args):
        Exception.__init__(self, args)

@singleton
class BuildbotConnection:
    headers = {'connection': 'Keep-Alive',
               'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
    user=""
    password=""

    def __init__(self, address=None):
        if address: self.connect_to(address)

    def connect_to(self, address):
        self.address = address
        self.connection = httplib.HTTPConnection(address)

    def _raw_request(self, request_msg, method="GET", **kwagrs):
        if kwagrs:
            kwagrs = urllib.urlencode(kwagrs)
        else:
            kwagrs = None

        r = None
        try:
            self.connection.request(method, request_msg, kwagrs, self.headers)
            r = self.connection.getresponse()
        except (socket.error, httplib.CannotSendRequest, httplib.ResponseNotReady):
            self.connect_to(self.address)
            try:
                self.connection.request(method, request_msg, kwagrs, self.headers)
                r = self.connection.getresponse()
            except (socket.gaierror, httplib.CannotSendRequest):
                raise BuildbotException("Request failed")

        if not (200 <= r.status < 400):
            raise BuildbotException("Request failed (%s %s)" % (r.status, r.reason))
        return r

    def _request(self, request_msg):
        return json.loads(self._raw_request(request_msg).read())

    def get_builders(self):
        return self._request('/json/builders')

    def get_last_builds(self, builders):
        request = "/json/builders?"
        for builder in builders:
            request += "select=%s/builds/-1&" % builder
        return self._request(request)

    def get_all_builds(self, builders):
        request = "/json/builders?"
        for builder in builders:
            request += "select=%s/builds/_all&" % builder
        return self._request(request)

    def login(self, user, password):
        self.connect_to(self.address)
        r = self._raw_request("/login?username=%s&passwd=%s" % (user, password))
        r.read()
        cookie = r.getheader('set-cookie')
        if not cookie:
            return False
        self.headers['cookie'] = cookie # yam yam, tasty cookie
        self.user = user
        self.password = password
        return True

    def build(self, builder):
        r = self._raw_request("/builders/%s/force" % builder, method="POST",
                              reason='launched from trac', forcescheduler='force')
        #if r.read().find('authfail'):
        #    if not self.login(self.user, self.password):
        #        raise BuildbotException('Authorization failed')
        #    r = self._raw_request("/builders/%s/force" % builder, method="POST",
        #                          reason='launched from trac', forcescheduler='force')


    def _parse_build(self, build):
        if not 'results' in build or not (type(build['results']) == int):
            status = "running"
        else:
            status = "success" if build['results'] == 0 else "failed"

        data = dict({
                'status': status,
                'start' : datetime.fromtimestamp(int(build['times'][0])),
                'num': build['number'],
                })

        if len(build['times']) > 1 and type(build['times'][1]) == float:
            data['finish'] = datetime.fromtimestamp(int(build['times'][1]))
            data['duration'] = data['finish'] - data['start']


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
        return data

    def get_build(self, builder, num):
        build = self._request("/json/builders/%s/builds/%d" % (builder, num))
        return self._parse_build(build)
