# This class in responsible for starting the analysis

import time
from modules.adapter.adb import *
from modules.api.utils import *
import os
import logging
from modules.definitions.exceptions import XenDroidConnectionError, XenDroidStartupError
from modules.runtime.procmon import ProcessMonitor


class AnalysisManager(object):

    def __init__(self, apk_path, device_serial):

        self.logger = logging.getLogger(self.__class__.__name__)

        self.device_serial = device_serial
        self.apk_path = apk_path
        self.adb_connection = ADB(device_serial)
        self.misc_path = os.path.abspath(os.path.join(os.getcwd(), 'xendroid_storage', 'misc'))

        p = os.path.abspath(os.path.join(os.getcwd(), 'xendroid_storage', 'analyses'))
        analysis_num = 0 if not os.listdir(p) else int(max(os.listdir(p), key=int))+1
        self.analysis_path = os.path.join(p, analysis_num)

        self.backup_path = os.path.join(self.analysis_path, 'backup', 'backup.ab')
        os.makedirs(self.backup_path[0:len('backup.ab')])
        self.output_path = os.path.join(self.analysis_path, 'out')

    def prepare_device(self):

        self.adb_connection.backup_device(self.backup_path)  # store a backup of the current state of the device

        dirs_list = self.adb_connection.shell('ls -R').split('\n\n')
        self.logger.info('Deleting your data before running the target application...')

        for DIR in dirs_list:
            dir_name = DIR.split(':')[0]
            for filename in DIR.split(':')[1].split('\n'):

                if filename.lower().endswith(('.jpg', '.png', '.jpeg', '.mp4')):
                    self.adb_connection.shell('su -c rm ' + dir_name + '/' + filename)

        packages = self.adb_connection.shell('ls /data/data').split('\n')

        for package_name in packages:
            if "com.android" not in package_name and "com.google.android" not in package_name:
                # ?
                self.adb_connection.shell('su -c rm /data/data/' + package_name + '/*')

        # determine device architecture to download the proper frida server
        device_arch = self.adb_connection.get_device_arch()
        if device_arch is None:
            self.logger.warning('Unable to determine the device architecture')
            device_arch = 'arm'  # ?

        self.logger.info('Downloading frida server..')
        res_path = download_frida(device_arch, self.misc_path)

        if res_path is not None:
            self.logger.debug('frida is downloaded successfully!')

            self.logger.debug('now pushing frida into the device..')

            push_and_execute_frida(res_path, self.adb_connection.cmd_prefix)
            self.logger.info('frida is pushed successfully into the device!')

        else:
            # if the download failed and no path was returned
            self.logger.debug('download failed...')
            raise XenDroidStartupError('frida server downloading failed, aborting ...')

        self.logger.info('Device is now ready!')

    def run_droidbot(self):
        pass

    def reset_device(self):
        # restore the device data from the stored backup
        pass

    def start(self):

        if not self.adb_connection.check_connectivity():
            raise XenDroidConnectionError('Device is not connected, aborting...')

        self.prepare_device()

        # install the target application
        self.adb_connection.run_cmd('install %s' % self.apk_path)

        # fire the target application
        package_name = get_package_name(self.apk_path)
        pid = self.adb_connection.get_pid_from_package_name(package_name)
        self.adb_connection.start_app(package_name)

        # start api monitoring ... but suspend target app before
        self.adb_connection.suspend_app(pid)

        api_monitor = ProcessMonitor(package_name, self.device_serial, self.analysis_path)
        api_monitor.start()

        self.adb_connection.resume_app(pid)

        # interact with the device using DroidBot: https://github.com/honeynet/droidbot
        self.run_droidbot()

        time.sleep(1)

        ############################
        ############################

        self.reset_device()

    def stop(self):
        pass
