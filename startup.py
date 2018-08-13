# This is where xendroid starts

from xendroid import XenDroid
import argparse
import subprocess
import time
from modules.definitions.exceptions import XenDroidConnectionError


def parse_args():
    parser = argparse.ArgumentParser(description="Analyse malware dynamically on your real device/ emulator")

    parser.add_argument("-s", action="store", required=True, dest="serial",
                        help="device serial as per the output of 'adb devices'")

    parser.add_argument("-p", action="store", required=True, dest="path_to_apk", help="path to the apk file")

    parser.add_argument("-d", action="store_true", required=False, dest="debug_mode", help="run XenDroid in debug mode")

    options = parser.parse_args()
    return options


def main():
    options = parse_args()

    if options.serial is None:
        cmd = ["adb", "devices"]
        try:
            r = subprocess.check_output(cmd).split('\n')
        except subprocess.CalledProcessError:
            raise XenDroidConnectionError('Failed to communicate through adb, try installing it.')

        if len(r) < 4:
            print 'Waiting for a connected device...'
            while True:
                r = subprocess.check_output(cmd).split('\n')
                if len(r) == 4:
                    break
            options.serial = r[1].split('\t')[0]

        elif len(r) == 4:
            options.serial = r[1].split('\t')[0]
        else:
            print 'More than one device is attached, try with -s to specify a device serial'
            time.sleep(2)
            return

    xendroid_instance = XenDroid(options.path_to_apk, options.serial, options.debug_mode)
    xendroid_instance.run()
    return


if __name__ == "__main__":
    main()
