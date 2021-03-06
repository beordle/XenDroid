# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License

import os
import lzma
import ntpath
import random
import string
import signal
import requests
import subprocess

from lib.definitions.exceptions import (
    XenDroidDependencyError,
    XenDroidTimeOutError
)

from lib.definitions.constants import XENDROID_TIMEOUT


def get_package_name(path_to_apk):
    """
    Get the package name from an apk file
    :param path_to_apk: Path to the apk file
    :return: package name
    """

    cmd = 'aapt dump badging {} | grep package:\ name'.format(os.path.abspath(path_to_apk)).split()
    try:
        out = subprocess.check_output(cmd)
    except OSError as err:
        raise XenDroidDependencyError(err, cmd[0])
    package_name = out.split()[1].split('=')[1][1:-1]
    return package_name


def download_and_extract_archive_from_url(url, t_path):
    """
    download archive from url, extract it then return the data
    :param url:
    :param t_path: Target path for the downloaded file
    :return: extracted data
    """
    req = requests.get(url, stream=True)

    data = None
    if req.status_code == 200:

        # Downloading and writing the archive.
        req.raw.decode_content = True
        with open(t_path, "wb") as fh:
            for chunk in req.iter_content(1024):
                fh.write(chunk)

        # Extracting data from the archive
        with lzma.open(t_path) as fh:
            data = fh.read()

        os.unlink(t_path)

    return data


def get_filename_from_path(path):
    """
    filename extraction from path.
    @param path: file path.
    @return: filename.
    """
    dirpath, filename = ntpath.split(path)
    return filename if filename else ntpath.basename(dirpath)


def get_rand_str(length, content=None):
    """
    generate a random string with specified length and content
    :param length:
    :param content: If left blank returns a string of digits
    :return:
    """
    if content is None:
        content = ['digits']

    chars = str()
    for type_ in content:
        if type_ == 'hex':
            chars += 'ABCDEF'
        else:
            chars += getattr(string, type_, None)
    return \
        ''.join(random.choice(chars) for _ in range(length))


def get_rand_mac_addr():
    """
    generate a random mac address
    :return: 12 character string mac address
    """
    mac = get_rand_str(12, ['digits', 'hex'])
    pretty_mac = ':'.join(map(''.join, zip(*[iter(mac)]*2)))
    return pretty_mac


def with_timeout(f):
    """
    A decorator for timeout-sensitive methods
    :return:
    """
    def handler(sig, frame):
        raise XenDroidTimeOutError()

    def wrapper(*args, **kwargs):

        signal.signal(signal.SIGALRM, handler)
        signal.alarm(XENDROID_TIMEOUT)

        ret = f(*args, **kwargs)

        signal.alarm(0)
        return ret

    return wrapper
