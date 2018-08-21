# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


import os
import time
import logging

from lib.api.utils import get_package_name, get_filename_from_path
from lib.definitions.constants import ANALYSES_DIR
from modules.monitoring.api_mon import APIMonitor
from modules.monitoring.tcpdump import TCPDUMP
from modules.connection.droidbot import DroidBot
from modules.connection.adb import ADB
from modules import startup


class AnalysisManager(object):

    """
    Launches an analysis task
    """

    def __init__(self, apk_path, device_serial):

        self.logger = logging.getLogger(self.__class__.__name__)

        self.apk_path = apk_path
        self.device_serial = device_serial
        self.adb_connection = ADB(device_serial)

        p = ANALYSES_DIR
        analysis_num = 0 if not os.listdir(p) else int(max(os.listdir(p), key=int))+1
        self.analysis_path = os.path.join(p, analysis_num)

        self.backup_path = os.path.join(self.analysis_path, 'backup', 'backup.ab')
        os.makedirs(self.backup_path[0:len('backup.ab')])

    def start(self):

        self.logger.info('Analysis started with task ID: '
                         + get_filename_from_path(self.analysis_path))
        self.adb_connection.unlock()
        # store a backup of the device's current state
        self.adb_connection.backup_device(self.backup_path)
        startup.run_startup(self.adb_connection)

        # install the target application
        self.adb_connection.install(self.apk_path)

        # fire the target application
        package_name = get_package_name(self.apk_path)
        pid = self.adb_connection.get_pid_from_package_name(package_name)
        self.adb_connection.start_app(package_name)

        # start api hooking ... but suspend target app before
        self.adb_connection.suspend_process(pid)

        api_monitor = APIMonitor(package_name, self.device_serial, self.analysis_path)
        api_monitor.start()

        tcpdump = TCPDUMP(self.adb_connection, self.analysis_path)
        tcpdump.start()

        self.adb_connection.resume_process(pid)

        # interact with the device using DroidBot: https://github.com/honeynet/droidbot
        DroidBot().interact()

        time.sleep(1)

        ############################
        ############################

        self.adb_connection.restore_backup(self.backup_path)
