# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


import subprocess
import logging

from lib.definitions.exceptions import XenDroidConnectionError
from multiprocessing import Process


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

        if err:
            msg = 'adb command: `{}` failed\n{}'.format(' '.join(args[1:]), err)
            raise XenDroidConnectionError(msg)

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

    def unlock(self):

        """
        Unlock the screen of the device
        """
        self.shell("input keyevent MENU")
        self.shell("input keyevent BACK")

    def press(self, key_code):

        """
        Press a key
        """
        self.shell("input keyevent %s" % key_code)

    def touch(self, x, y):

        """
        Simulate a screen touch at the specified coordinates
        :param x: x-coordinate
        :param y: y-coordinate
        :return:
        """
        self.shell("input tap %d %d" % (x, y))

    def get_on_screen_element_coordinates_by_text(self, element_name):

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

        # MIPS is not supported so far
        getprop_abis = ["armeabi", "armeabi-v7a", "arm64-v8a", "x86", "x86_64"]
        output = self.get_prop(_property).lower().strip().decode("utf-8")

        if output in getprop_abis:
            if output in ["armeabi", "armeabi-v7a"]:
                arch = "arm"
            elif output == "arm64-v8a":
                arch = "arm64"
            else:
                arch = output

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

    def start_app(self, package_name):

        """
        Start an android package's launching activity via monkey
        :param package_name:
        :return:
        """
        args = 'monkey -p {} -c android.intent.category.LAUNCHER 1'.format(package_name)
        self.shell(args)
        self.logger.debug('started target application...')
        self.logger.debug('target application process name: {}'.format(package_name))

    def backup_device(self, backup_to_path):

        """
        Store a backup of the device to the specified path
        :param backup_to_path:
        :return:
        """
        self.logger.info('Backing up the device...')
        extra_arg = 'backup -all -f {}'.format(backup_to_path)
        proc = Process(target=ADB.run_cmd, args=(self, extra_arg))
        proc.start()

        while proc.is_alive():
            coords = self.get_on_screen_element_coordinates_by_text("back up my data")
            if coords is not None:
                self.touch(coords[0], coords[1])
        proc.join()
        self.logger.info('Device backed up successfully!')

    def stop_app(self, package_name):

        """
        Stop the target application's process by package name
        :param package_name:
        :return:
        """

        args = 'am force-stop {}'.format(package_name)
        self.shell(args)
        self.logger.debug('target application with process name {} is terminated'.format(package_name))

    def stop_process(self, pid):

        """
        Stops a running process given its pid
        :param pid:
        :return:
        """
        args = 'kill {}'.format(pid)
        self.shell(args)

        self.logger.debug('target process with PID {} is suspended'.format(pid))

    def suspend_process(self, pid):

        """
        Suspend a running process by its process id
        :param pid:
        :return:
        """
        args = 'kill -s 19 {}'.format(pid)
        self.shell(args)

        self.logger.debug('target process with PID {} is suspended!'.format(pid))

    def resume_process(self, pid):

        """
        Resume a target process given the pid if it was being suspended
        :param pid:
        :return:
        """

        args = 'kill -s 18 {}'.format(pid)
        self.shell(args)

        self.logger.debug('target process with PID {} is resumed'.format(pid))

    def get_pid_from_package_name(self, package_name):

        """
        Returns the pid of a given application by its package name
        :param package_name:
        :return:
        """
        args = 'ps | grep {}'.format(package_name)
        output = self.shell(args)
        if output is not None:
            return output.split('\n')[0].split()[1]

    def restore_backup(self, backup_path):

        """
        Restore the state of the device from a backup file given its path
        :param backup_path:
        :return:
        """

        self.logger.info('Restoring the device state from backup')

        extra_arg = 'restore {}'.format(backup_path)
        proc = Process(target=ADB.run_cmd, args=(self, extra_arg))
        proc.start()

        while proc.is_alive():
            coords = self.get_on_screen_element_coordinates_by_text("restore my data")
            if coords is not None:
                self.touch(coords[0], coords[1])
        proc.join()
        self.logger.info("Backup restored successfully!")
