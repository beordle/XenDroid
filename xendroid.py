#!/usr/bin/env python

# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


import argparse
import subprocess
import time
import logging

from lib.definitions.exceptions import XenDroidDependencyError
from modules.analysis_manager import AnalysisManager


def parse_args():

    """
    Parse command line arguments
    :return:
    """
    parser = argparse.ArgumentParser(description="Analyse malware dynamically on your real device/ emulator")

    parser.add_argument("-s", action="store", required=True, dest="serial",
                        help="device serial as per the output of 'adb devices'")

    parser.add_argument("-p", action="store", required=True, dest="path_to_apk", help="path to the apk file")

    parser.add_argument("-d", action="store_true", required=False, dest="debug_mode", help="run XenDroid in debug mode")

    options = parser.parse_args()
    return options


def run():
    options = parse_args()

    if options.serial is None:
        cmd = ["adb", "devices"]
        try:
            r = subprocess.check_output(cmd).split('\n')
        except OSError as e:
            raise XenDroidDependencyError(e, 'adb')

        if len(r) < 4:
            print 'Waiting for a connected device...'
            while True:
                r = subprocess.check_output(cmd).split('\n')
                if len(r) == 4:
                    break
            options.serial = r[1].split('\t')[0]
        elif len(r) > 4:
            print 'More than one device is attached, try with -s to specify a device serial'
            time.sleep(2)
            return
        else:
            options.serial = r[1].split('\t')[0]

    logging.basicConfig(level=logging.DEBUG if options.debug_mode else logging.INFO)
    am = AnalysisManager(options.path_to_apk, options.serial)
    try:
        am.start()
    finally:
        am.roll_back()


if __name__ == "__main__":
    run()
