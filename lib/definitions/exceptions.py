# Copyright (C) 2018  Muhammed Ziad
# This file is part of XenDroid - https://github.com/muhzii/XenDroid
#
# An instrumented sandbox for Android
# This program is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License


import sys
import traceback


def exception_hook(_type, val, tb):
    msg = ''.join(traceback.format_exception(_type, val, tb))
    print(msg)


sys.excepthook = exception_hook


class XenDroidModuleError(Exception):
    pass


class XenDroidStartupError(Exception):
    pass


class XenDroidAnalysisError(Exception):
    pass


class XenDroidCommunicationError(Exception):
    pass


class XenDroidADBError(XenDroidCommunicationError):
    pass


class XenDroidFridaError(XenDroidCommunicationError):
    pass


class XenDroidTimeOutError(Exception):

    def __init__(self):
        msg = 'Timeout reached, Exiting...'
        Exception.__init__(self, msg)


class XenDroidDependencyError(Exception):

    def __init__(self, err, arg=''):
        msg = err.message
        if isinstance(err, ImportError):
            msg = 'The module `{}` is missing, ' \
                  'try installing with `pip`'.format(err.message.split()[-1])
        elif isinstance(err, OSError):
            msg = 'Command `{}` is not found, ' \
                  'make sure your $PATH variable is configured properly'.format(arg)
        Exception.__init__(self, msg)
