#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import json
import os

def meddle_directory():
    if os.path.isdir(os.path.dirname(__file__)):
        return os.path.dirname(__file__)
    else:
        return os.path.dirname(os.path.dirname(__file__))

def system_user_directory():
    return os.path.expanduser('~')

def get_version_info():
    _version_file = os.path.join(meddle_directory(), 'version')
    return json.loads(open(_version_file).read())

def get_version():
    return tuple(get_version_info()['common'])

def get_min_client_version():
    return tuple(get_version_info()['min_client'])
