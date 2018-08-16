# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


import logging
import os

from modules.api.utils import download_and_extract_archive_from_url, get_filename_from_path
from modules.connection.adb import ADB
from modules.definitions.constants import MISC_FOLDER
from modules.definitions.exceptions import XenDroidStartupError, XenDroidDependencyError

try:
    from frida import __version__ as FRIDA_VERSION

except ImportError as e:
    raise XenDroidDependencyError(e)


class DependenciesBuilder(object):

    def __init__(self, device_serial):

        self.logger = logging.getLogger(self.__class__.__name__)
        self.adb_connection = ADB(device_serial)

        self.device_arch = self.adb_connection.get_device_arch()
        if self.device_arch is None:
            raise XenDroidStartupError('Unable to determine device architecture')

        self.frida_server_path = \
            os.path.join(MISC_FOLDER, 'frida-server-{}-android-{}.xz'.
                         format(self.device_arch, FRIDA_VERSION))

    def remove_user_files(self):

        """
        Remove user files from the device storage to prepare for running the sample
        :return:
        """

        all_dirs = self.adb_connection.shell('ls -R').split('\n\n')

        extensions = ('.jpg', '.png',
                      '.jpeg', '.mp4'
                               '.db', '.xml')

        self.logger.info('Safe deleting your data before running the target application...')

        for _dir in all_dirs:
            dir_name = _dir.split(':')[0]
            dir_files = _dir.split(':')[1].split('\n')

            for filename in dir_files:
                if filename.lower().endswith(extensions):
                    self.adb_connection.shell('su -c rm {}/{}'.format(dir_name, filename))

        self.remove_apps_data_on_device()

    def remove_apps_data_on_device(self):

        """
        Remove application's data from all the installed apps
        :return:
        """

        t_folders = ('files', 'databases'
                              'shared_prefs')

        packages = self.adb_connection.shell('ls /data/data').split('\n')

        for package_name in packages:
            for folder_name in t_folders:
                cmd = 'su -c rm /data/data/{}/{}/*'.format(package_name, folder_name)
                self.adb_connection.shell(cmd)

    def download_frida_server(self):

        # inspired from: https://github.com/AndroidTamer/frida-push
        """Download the compatible frida version with the one installed on the system
        extracting the compressed file
        """

        self.logger.debug('Downloading the frida server...')

        url = "https://github.com/frida/frida/releases/download/{}/{}". \
            format(FRIDA_VERSION, get_filename_from_path(self.frida_server_path))

        f_name = url.split('/')[-1]
        f_path = os.path.join(MISC_FOLDER, f_name)

        data = download_and_extract_archive_from_url(url, f_path)

        if data:
            with open(f_path[:-3], "wb") as frida_server:
                frida_server.write(data)
        else:
            raise XenDroidStartupError('frida server download failed, aborting...')

    def push_and_execute_frida(self):

        """
        Push the frida server file and run the server on the device
        :return:
        """

        push_cmd = 'push {} /data/local/tmp/frida-server'.format(self.frida_server_path)

        shell_cmds = ['chmod 0755 /data/local/tmp/frida-server',
                      'killall frida-server', '/data/local/tmp/frida-server&']

        self.logger.debug('Pushing and running the frida server on the device...')

        self.adb_connection.run_cmd(push_cmd)
        for cmd in shell_cmds:
            self.adb_connection.shell('su -c {}'.format(cmd))

    def start(self):

        self.adb_connection.run_cmd('root')
        self.adb_connection.run_cmd('remount')

        self.remove_user_files()

        if not self.frida_server_path.exists():
            self.download_frida_server()
        self.push_and_execute_frida()

        self.logger.debug('Device is ready!')
