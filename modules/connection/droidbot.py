# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


import logging


class DroidBot(object):

    """
    Communicates with Droidbot to interact with the device
    """
    def __init__(self):

        self.logger = logging.getLogger(self.__class__.__name__)

    def interact(self):
        pass
