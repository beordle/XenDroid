# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


import logging
import subprocess

from multiprocessing import Process
from lib.definitions.exceptions import XenDroidADBError


class ADB(object):
    """
    interface of ADB
    send adb commands via this
    """

    def __init__(self, serial):
        """
        initiate a ADB connection from serial no
        the serial no should be in output of `adb devices`
        :param serial: serial no.
        :return:
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cmd_prefix = ['adb', "-s", serial]

    def run_cmd(self, extra_args):
        """
        run an adb command and return the output
        :return: output of adb command or None
        @param extra_args: arguments to run in adb
        """
        if isinstance(extra_args, str) or isinstance(extra_args, unicode):
            extra_args = extra_args.split()

        args = [] + self.cmd_prefix
        args += extra_args

        p = subprocess.Popen(args, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = p.communicate()

        if p.returncode != 0:
            msg = 'adb command: `{}` failed\nERROR:{}'.format(' '.join(args[3:]), err)
            raise XenDroidADBError(msg)

        if out == '':
            return None
        else:
            return out

    def shell(self, extra_args):
        """
        run an `adb shell` command
        @param extra_args:
        @return: output of adb shell command or None
        """
        if isinstance(extra_args, str) or isinstance(extra_args, unicode):
            extra_args = extra_args.split()

        shell_extra_args = ['shell'] + extra_args
        return self.run_cmd(shell_extra_args)

    def install(self, apk_path):
        """
        install application on device with `adb install`
        :param apk_path: Path to the APK file
        :return:
        """
        self.run_cmd('install %s' % apk_path)

    def touch(self, x, y):
        """
        Simulate a screen touch at the specified coordinates
        :param x: x-coordinate
        :param y: y-coordinate
        :return:
        """
        self.shell("input tap %d %d" % (x, y))

    def get_view_coordinates_by_name(self, element_name):
        """
        This function gets the coordinates of a specific element
        on the screen given its name
        :param element_name:
        :return:
        """

        self.shell("uiautomator dump")
        layout = self.shell("cat /mnt/sdcard/window_dump.xml")

        if element_name.lower() in layout.lower():
            bounds = layout.split(element_name)[1].split("bounds=")[1].\
                    split()[0].split("][")[0][2:]

            x, y = map(int, bounds.split(","))

            return x, y
        else:
            return None

    def get_prop(self, _property):
        """
        return the property specified by the parameter _parameter
        :param _property: property file name
        :return:
        """
        prop_arg = 'getprop {}'.format(_property)
        return self.shell(prop_arg)

    def get_device_arch(self):
        """
        This function attempts to determine the architecture of the device
        :return: the architecture of the device
        """
        arch = None
        _property = 'ro.product.cpu.abi'

        # MIPS is not supported
        getprop_abi = ["armeabi", "armeabi-v7a", "arm64-v8a", "x86", "x86_64"]
        res = self.get_prop(_property).lower().strip().decode("utf-8")

        if res in getprop_abi:
            if res in ["armeabi", "armeabi-v7a"]:
                arch = "arm"
            elif res == "arm64-v8a":
                arch = "arm64"
            else:
                arch = res

        return arch

    def get_api_level(self):
        """
        Get the API level of the device
        :return:
        """
        _property = 'ro.build.version.sdk'
        return self.get_prop(_property)

    def push_to_path(self, source_p, target_p):
        """
        Push a file specified by the source to a target path
        :param target_p:
        :param source_p:
        :return:
        """
        push_arg = 'push {} {}'.format(source_p, target_p)
        self.run_cmd(push_arg)

    def pull_from_path(self, source_p, target_p):
        """
        Push a file specified by the source to the tmp folder
        :param source_p:
        :param target_p:
        :return:
        """
        pull_arg = 'pull {} {}'.format(source_p, target_p)
        self.run_cmd(pull_arg)

    def kill_process(self, pid):
        """
        Stops a running process given its pid
        :param pid:
        :return:
        """
        args = 'kill -s 9 {}'.format(pid)
        self.shell(args)

        self.logger.debug('target process with PID {} is suspended'.format(pid))

    def run_ui_based_cmd(self, args, view_to_click):
        """
        Run a process that requires a UI action
        :param args:
        :param view_to_click:
        :return:
        """
        process = Process(target=ADB.run_cmd, args=(self, args))
        process.start()

        while process.is_alive():
            coords = self.get_view_coordinates_by_name(view_to_click)
            if coords is not None:
                self.touch(coords[0], coords[1])
        process.join()

    def backup_device(self, backup_to_path):
        """
        Store a backup of the device to the specified path
        :param backup_to_path:
        :return:
        """
        self.logger.info(
            'Backing up the device...'
        )
        args = 'backup -all -f {}'.format(backup_to_path)
        self.run_ui_based_cmd(args, "back up my data")
        self.logger.info(
            'Device backed up successfully!'
        )

    def restore_backup(self, backup_path):
        """
        Restore the state of the device from a backup file given its path
        :param backup_path:
        :return:
        """
        self.logger.info(
            'Restoring the device state from backup'
        )
        args = 'restore {}'.format(backup_path)
        self.run_ui_based_cmd(args, "restore my data")
        self.logger.info(
            'Backup restored successfully!'
        )
