# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


import ntpath
import subprocess
import os
import requests

from lib.definitions.exceptions import XenDroidDependencyError

try:
    import backports.lzma
except ImportError as e:
    raise XenDroidDependencyError(e)


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
        with backports.lzma.open(t_path) as fh:
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
