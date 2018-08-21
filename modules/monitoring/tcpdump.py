# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


import logging
import os


class TCPDUMP(object):

    def __init__(self, adb_connection, analysis_path):

        self.adb_connection = adb_connection
        self.logger = logging.getLogger(self.__class__.__name__)
        self.pid = None
        self.analysis_path = analysis_path

        self.t_logs = '/data/local/tmp/tcpdump.pcap'

    def pull_logs(self):

        """
        Pull the tcpdump traffic logs from the device
        :return:
        """
        pull_to = os.path.join(self.analysis_path, 'logs', 'tcpdump.pcap')

        self.adb_connection.pull(self.t_logs, pull_to)

    def start(self):

        """
        Start tcpdump traffic monitoring on the device
        :return: process pid
        """
        t_executable = '/data/local/tmp/tcpdump'

        args = [t_executable, '-nnqUXs', '0', '-w', self.t_logs, '&']

        self.adb_connection.shell(args)
        self.pid = self.adb_connection.shell('echo $!')

        self.logger.debug('Network monitoring module started successfully!')

    def stop(self):

        """
        Stops the tcpdump process
        :return:
        """
        self.adb_connection.stop_process(self.pid)
