tracbuildbot plugin
==============

This trac(http://trac.edgewall.org/) plugin provides intergration with 
build system buildbot(http://buildbot.net/).

Features:
- status page with last builds
- attaching builder to source (links to revisions, changesets)
- launch build
- uses jsonapi(buildbot >= 0.8.0)
- timeline events
- filter for status page and timeline
- deferred caching events to trac db

maxim.kaskevich@gmail.com

Installation
------------------------

1. build egg:
 - `git clone --progress -v "https://github.com/Tramort/tracbuildbot.git" "tracbuildbot"`
 - `cd tracbuildbot`
 - `python setup.py bdist_egg`

2. copy egg file from "tracbuildbot/dist" to "plugins" dir in trac enviroment
