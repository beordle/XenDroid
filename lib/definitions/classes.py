# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


class MonitoringModule(object):

    def __init__(self, analysis_path, description):
        self.pid = None
        self._running = False
        self.analysis_path = analysis_path
        self.description = description

    def start(self):
        self._running = True

    def stop(self):
        self._running = False
        self.pid = None

    def isRunning(self):
        return self._running


class AnalysisModule(object):
    pass
