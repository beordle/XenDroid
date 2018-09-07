# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


import os

XENDROID_TIMEOUT = 120

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ANALYSES_DIR = os.path.join(ROOT_DIR, 'xendroid_storage', 'analyses')

MISC_FOLDER = os.path.join(ROOT_DIR, 'xendroid_storage', 'misc')

UTILS_FOLDER = os.path.join(ROOT_DIR, 'utils')
