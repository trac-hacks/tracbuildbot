#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Max Kaskevich <maxim.kaskevich@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import find_packages, setup

setup(
    name='TracBuildbotPlugin',
    author='Max Kaskevich',
    author_email='maxim.kaskevich@gmail.com',
    version='0.1',
    license='BSD 3-Clause',
    url="???",
    packages=find_packages(exclude=['*.tests*']),
    install_requires=[],
    entry_points = """
    [trac.plugins]
    buildbot.web_ui = tracbuildbot.web_ui
    buildbot.timeline = tracbuildbot.timeline
    buildbot.admin = tracbuildbot.admin
    buildbot.env = tracbuildbot.environmentSetup
    """,
    package_data={'tracbuildbot': ['templates/*.html',
                                   'htdocs/css/*.css',
                                   'htdocs/img/*.gif',
                                   'htdocs/js/*.js',
                                  ]},
)
