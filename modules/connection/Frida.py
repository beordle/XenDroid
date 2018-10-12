# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


import time
import frida
import logging

from lib.api.utils import with_timeout
from lib.definitions.exceptions import XenDroidFridaError


class Frida(object):
    """
    Establishes a connection with a running process
    on the device via frida
    http://github.com/frida/frida
    """
    def __init__(self, device_serial):

        self.logger = logging.getLogger(self.__class__.__name__)

        self.pid = None
        self.pkg = None
        self.script = None
        self.session = None
        self.script_msg_handler = None

        try:
            self.device = frida.get_device(device_serial)
        except (frida.InvalidArgumentError, frida.TimedOutError):
            raise XenDroidFridaError('Frida connection failed, device not found')

    @with_timeout
    def spawn_app(self, package_name):
        """
        start a target application by package name
        :param package_name:
        :return:
        """
        self.pkg = package_name

        try:
            self.pid = self.device.spawn([package_name])

        except frida.NotSupportedError:
            raise XenDroidFridaError(
                'No application with such package name installed: {}'.format(self.pkg))
        except frida.ServerNotRunningError:
            raise XenDroidFridaError(
                "Unable to connect to frida's server on the device")
        except (frida.TransportError, frida.TimedOutError):
            self.logger.warning('Application startup failed, re-spawning the application...')
            self.spawn_app(self.pkg)
            return
        except frida.InvalidOperationError:
            # wait for a previous spawn operation to finish
            time.sleep(5)
            self.spawn_app(self.pkg)
            return

        self.logger.debug('Spawned target application...')
        self.logger.debug('Target application process name: {}'.format(self.pkg))

    def set_msg_handler(self, msg_handler):
        """
        set the handler function to handle messages
        exchanged with the script
        :param msg_handler:
        :return:
        """
        self.script_msg_handler = msg_handler

    def stop_app(self):
        """
        kill the currently running application
        :return:
        """
        self.pid = None
        self.pkg = None
        self.script_msg_handler = None

        if self.pid is None:
            return

        self.device.kill(self.pid)
        self.logger.debug(
            'Target application with process name {} is terminated'.format(self.pkg))

    def resume_app(self):
        """
        Resume the currently suspended application
        :return:
        """
        self.device.resume(self.pid)

    def start_session(self):
        """
        initiate a process session with frida on the device
        :return:
        """
        try:
            self.session = self.device.attach(self.pid)
        except frida.ProcessNotFoundError:
            raise XenDroidFridaError(
                'Failed to establish frida session, no such process found')

        self.logger.debug('Frida session established!')

    @with_timeout
    def load_script(self, _script):
        """
        load a script into the process
        :param _script: frida based JavaScript code
        :return:
        """
        if self.script is not None:
            self.terminate_session()
            self.spawn_app(self.pkg)
            self.start_session()

        try:
            self.script = self.session.create_script(_script)
            self.script.on('message', self.script_msg_handler)
            self.script.load()
        except frida.TransportError:
            self.logger.debug('Failed at loading the script, reloading...')
            self.load_script(_script)

    def terminate_session(self):
        """
        Close the session and unload the script
        :return:
        """
        if self.script is not None:
            self.script.unload()

        if self.session is not None:
            self.session.detach()

        self.script = None
        self.session = None
        self.logger.debug('Frida session terminated!')
