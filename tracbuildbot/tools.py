# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Max Kaskevich <maxim.kaskevich@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

class SingletonMeta(type):
    def __init__(cls, name, bases, dict):
        super(SingletonMeta, cls).__init__(name, bases, dict)
        cls.instance = None
    def __call__(self,*args,**kw):
        if self.instance is None:
            self.instance = super(SingletonMeta, self).__call__(*args, **kw)
        return self.instance
 
class Singleton(object):
    __metaclass__ = SingletonMeta

def singleton(cls):
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance

def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj
