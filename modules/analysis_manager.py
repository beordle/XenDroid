# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


import os
import logging

from modules import startup
from modules.connection.adb import ADB
from modules.connection.Frida import Frida
from modules.connection.droidbot import DroidBot
from modules.monitoring.api_mon import APIMonitor
from modules.monitoring.net_mon import TrafficMonitor

from lib.definitions.constants import ANALYSES_DIR
from lib.definitions.exceptions import XenDroidModuleError
from lib.api.utils import get_package_name, get_filename_from_path


class AnalysisManager(object):

    """
    Launches an analysis task
    """

    def __init__(self, apk_path, device_serial):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.apk_path = apk_path
        self.adb_connection = ADB(device_serial)
        self.frida_connection = Frida(device_serial)

        self.modules = []

        self.analysis_path = None
        self.backup_path = None
        self._init_paths()

    def _init_paths(self):
        analysis_num = 0
        if os.path.exists(ANALYSES_DIR):
            analysis_num = int(max(os.listdir(ANALYSES_DIR),
                                   key=lambda x: int(x.split('_')[1]))) + 1

        self.analysis_path = os.path.join(ANALYSES_DIR, 'task_' + str(analysis_num))
        self.backup_path = os.path.join(self.analysis_path, 'backup', 'backup.ab')

        os.makedirs(os.path.join(self.analysis_path, 'backup'))
        os.makedirs(os.path.join(self.analysis_path, 'logs'))

    def stop_monitoring(self):
        for module in self.modules:
            try:
                module.stop()
            except XenDroidModuleError:
                self.logger.error(
                    'Failed at finalizing the capturing process for the '
                    '{} module, some logs might be missing!'.format(module.description)
                )
        self.modules = []

    def load_monitoring(self):
        modules = self.modules

        # Initialize the monitoring modules
        tm = TrafficMonitor(self.adb_connection, self.analysis_path)
        api_m = APIMonitor(self.frida_connection, self.analysis_path)

        try:
            api_m.start()
            modules.append(api_m)
        except XenDroidModuleError:
            self.logger.error('API monitoring module startup failed...')

        try:
            tm.start()
            modules.append(tm)
        except XenDroidModuleError:
            self.logger.error('Network sniffer module startup failed...')

    def roll_back(self):
        if self.backup_path.exists():
            self.adb_connection.restore_backup(self.backup_path)

    def start(self):
        self.logger.info('Analysis started with task ID: '
                         + get_filename_from_path(self.analysis_path))

        # store a backup of the device's current state
        self.adb_connection.backup_device(self.backup_path)
        startup.run_startup(self.adb_connection)

        # install the target application
        self.adb_connection.install(self.apk_path)

        # fire the target application
        package_name = get_package_name(self.apk_path)
        self.frida_connection.spawn_app(package_name)

        # start loading the monitoring modules
        self.load_monitoring()

        self.frida_connection.resume_app()

        # interact with the device using DroidBot
        DroidBot().interact()

        ############################

        self.stop_monitoring()
