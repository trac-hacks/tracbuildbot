# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Max Kaskevich <maxim.kaskevich@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import buildbot_api
import datetime

bc = buildbot_api.BuildbotConnection()
bc.connect_to("localhost:8010")
builders = bc.get_builders()
print "BUILDERS:", [name for name in builders],"\n"

#print "LAST BUILDS:",bc.get_last_builds(builders),"\n"
print "LAST BUILDS:"
for name, builder in bc.get_last_builds(builders).iteritems():
    last_build = builder['builds']['-1']  
    print name, ":"
    print "build " + ( "successful " if last_build['results'] == 0 else "failed (%s)" % last_build['results'])
    print "started at", datetime.datetime.fromtimestamp(last_build['times'][0])
    print "finished at", datetime.datetime.fromtimestamp(last_build['times'][1])
    print "buildnumber - ", last_build['number']

    for prop in  last_build['properties']:
        if prop[0] == 'got_revision':
            print "revision - ", prop[1]
            break
    print ""

#print "BUILD TEST:"
#try:
#    bc.build('runtests')
#except buildbot_api.BuildbotException as e:
#    print (e)


print "LOGIN TEST:"
print(bc.login("qwe","qwe"))

print "BUILD TEST:"
print (bc.build('runtests'))
