# XenDroid project

from modules.definitions.exceptions import XenDroidDependencyError, XenDroidConnectionError
import subprocess
import backports.lzma
import os
import requests

try:
    from frida import __version__ as FRIDA_VERSION
except ImportError:
    raise XenDroidDependencyError('frida is not installed, try: pip install frida')


def get_package_name(path_to_apk):

    cmd = 'aapt dump badging {} | grep package:\ name'.format(os.path.abspath(path_to_apk)).split()
    out = subprocess.check_output(cmd)
    package_name = out.split()[1].split('=')[1][1:-1]
    return package_name


def push_and_execute_frida(frida_path, cmd_prefix):

    """This function pushes the frida server file and runs the server on the device"""

    push_cmd = 'adb push {} /data/local/tmp/frida-server'.format(frida_path)
    chmod_cmd = 'chmod 0755 /data/local/tmp/frida-server'
    kill_cmd = 'killall frida-server'
    execute_cmd = '/data/local/tmp/frida-server&'
    exec_shell = '{} shell su'.format(' '.join(cmd_prefix))

    # using shell argument is not safe but the commands aren't passed as the function's parameters so it should be OK
    try:
        subprocess.check_call(push_cmd)

        subprocess.check_call(chmod_cmd, shell=True, executable=exec_shell)

        subprocess.check_call(kill_cmd, shell=True, executable=exec_shell)

        subprocess.check_call(execute_cmd, shell=True, executable=exec_shell)

    except subprocess.CalledProcessError:
        raise XenDroidConnectionError('failed to setup frida on the device')


def download_frida(arch, download_path):

    # inspired by: https://github.com/AndroidTamer/frida-push/blob/master/frida_push/command.py

    """ This function downloads the compatible frida version with the one installed on the system
    it extracts the compressed file then returns its path
    :returns path of extracted file
    """
    url = "https://github.com/frida/frida/releases/download/{}/frida-server-{}-android-{}.xz".format(
                                                                                    FRIDA_VERSION, FRIDA_VERSION, arch)
    f_name = 'frida-server-{}-android-{}.xz'.format(FRIDA_VERSION, arch)
    f_path = os.path.join(download_path, f_name)
    req = requests.get(url, stream=True)

    data = None
    if req.status_code == 200:

        # Downloading and writing the archive.
        req.raw.decode_content = True
        with open(f_path, "wb") as fh:
            for chunk in req.iter_content(1024):
                fh.write(chunk)
        with backports.lzma.open(f_path) as fh:
            data = fh.read()

        os.unlink(f_path)

    if data:
        with open(f_path[:-3], "wb") as frida_server:
            frida_server.write(data)
        return f_path[:-3]
    return None
