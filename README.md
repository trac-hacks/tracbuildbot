tracbuildbot plugin
==============

This trac(http://trac.edgewall.org/) plugin provides intergration with 
build system buildbot(http://buildbot.net/).

Features:
- page with status of last buildbot builds
- filter of builder to view
- link builder to source repo
- launch builds

In future:
- timeline events

maxim.kaskevich@gmail.com

Installation
------------------------

1. build egg:
 - `git clone --progress -v "https://github.com/Tramort/tracbuildbot.git" "tracbuildbot"`
 - `cd tracbuildbot`
 - `python setup.py bdist_egg`

2. copy egg file from "tracbuildbot/dist" to "plugins" dir in trac enviroment
