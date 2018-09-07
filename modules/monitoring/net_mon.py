# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


import os
import logging

from lib.definitions.classes import MonitoringModule
from lib.definitions.exceptions import XenDroidCommunicationError


class TrafficMonitor(MonitoringModule):

    """This is responsible for analysing the network traffic via tcpdump"""

    def __init__(self, analysis_path, adb_connection):

        MonitoringModule.__init__(self, analysis_path)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.adb_connection = adb_connection

        self.t_executable = '/data/local/tmp/tcpdump'

        self.t_dump = self.t_executable + '.pcap'
        self.t_log = self.t_executable + '.log'

    def pull_output(self):

        """
        Pull the tcpdump traffic output files from the device
        :return:
        """
        pull_to = os.path.join(self.analysis_path, 'logs', 'net_dump.pcap')
        self.adb_connection.pull(self.t_dump, pull_to)

        pull_to = os.path.join(self.analysis_path, 'logs', 'net_log.log')
        self.adb_connection.pull(self.t_log, pull_to)

    def start(self):

        """
        Start tcpdump traffic monitoring on the device
        :return: process id
        """

        # save a pcap file to the target directory
        args = [self.t_executable, '-w', self.t_dump, '&']
        self.logger.info('Starting network monitoring module on the device...')

        try:
            self.adb_connection.shell(args)
        except XenDroidCommunicationError:
            self.logger.error('Failed to start network monitoring module, '
                              'some error occurred with tcpdump...')
            return

        self._running = True
        self.pid = self.adb_connection.shell('echo $!')
        self.logger.debug('Network monitoring module started successfully!')

    def stop(self):

        """
        Stop the tcpdump process and pull the logs
        :return:
        """
        if self.isRunning():
            self.logger.debug('Exiting network monitoring...')
            self.adb_connection.kill_process(self.pid)

            args = [self.t_executable, '-ttttnnql', '-r', self.t_dump, '>', self.t_log]
            self.adb_connection.shell(args)

            self.pull_output()
            self._running = False
            self.logger.debug('Network monitoring process has been killed!')
