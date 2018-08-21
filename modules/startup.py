# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


import logging
import os

from lib.api.utils import download_and_extract_archive_from_url, get_filename_from_path
from lib.definitions.constants import MISC_FOLDER, UTILS_FOLDER
from lib.definitions.exceptions import XenDroidStartupError, XenDroidDependencyError

try:
    from frida import __version__ as FRIDA_VERSION

except ImportError as e:
    raise XenDroidDependencyError(e)

logger = logging.getLogger('Startup')

adb_connection, device_arch, frida_server_fp = None, None, None


def remove_apps_data_on_device():

    """
    Remove application's data from all the installed apps
    :return:
    """

    t_folders = ('files', 'databases'
                          'shared_prefs')

    packages = adb_connection.shell('ls /data/data').split('\n')

    for package_name in packages:
        for folder_name in t_folders:
            cmd = 'su -c rm /data/data/{}/{}/*'.format(package_name, folder_name)
            adb_connection.shell(cmd)


def remove_user_files():

    """
    Remove user files from the device storage to prepare for running the sample
    :return:
    """

    all_dirs = adb_connection.shell('ls -R').split('\n\n')

    extensions = ('.jpg', '.png',
                  '.jpeg', '.mp4'
                           '.db', '.xml')

    logger.info('Safe deleting your data before running the target application...')

    for _dir in all_dirs:
        dir_name = _dir.split(':')[0]
        dir_files = _dir.split(':')[1].split('\n')

        for filename in dir_files:
            if filename.lower().endswith(extensions):
                adb_connection.shell('su -c rm {}/{}'.format(dir_name, filename))

    remove_apps_data_on_device()


def download_frida_server():

    # inspired from: https://github.com/AndroidTamer/frida-push
    """
    Download the compatible frida version with the one installed on the system
    extracting the compressed file
    """
    logger.debug('Downloading the frida server...')

    url = "https://github.com/frida/frida/releases/download/{}/{}". \
        format(FRIDA_VERSION, get_filename_from_path(frida_server_fp))

    f_name = url.split('/')[-1]
    f_path = os.path.join(MISC_FOLDER, f_name)

    data = download_and_extract_archive_from_url(url, f_path)

    if data:
        with open(f_path[:-3], "wb") as frida_server:
            frida_server.write(data)
    else:
        raise XenDroidStartupError('frida server download failed, aborting...')


def push_and_execute_frida():

    """
    Push the frida server file and run the server on the device
    :return:
    """
    logger.debug('Pushing and running the frida server on the device...')
    t_executable = '/data/local/tmp/frida-server'

    adb_connection.push_to_tmp(frida_server_fp, t_executable)

    shell_cmds = ['chmod 0755 {}'.format(t_executable), 'killall frida-server',
                  '{}&'.format(t_executable)]

    for cmd in shell_cmds:
        adb_connection.shell('su -c {}'.format(cmd))


def push_tcpdump():

    """
    Push the compiled tcpdump executable for the connected device
    :return:
    """
    t_executable = '/data/local/tmp/tcpdump'
    tcpdump_sp = os.path.join(UTILS_FOLDER, 'tcpdump', device_arch[:3])

    adb_connection.push_to_tmp(tcpdump_sp, t_executable)


def run_startup(_connection):

    global adb_connection, device_arch, frida_server_fp

    os.makedirs(MISC_FOLDER)

    adb_connection = _connection
    device_arch = adb_connection.get_device_arch()

    if device_arch is None:
        raise XenDroidStartupError('Unable to determine device architecture')

    frida_server_fp = \
        os.path.join(MISC_FOLDER, 'frida-server-{}-android-{}.xz'.
                     format(device_arch, FRIDA_VERSION))

    adb_connection.run_cmd('root')
    adb_connection.run_cmd('remount')

    remove_user_files()

    if not frida_server_fp.exists():
        download_frida_server()
    push_and_execute_frida()

    push_tcpdump()

    logger.debug('Device is ready!')
