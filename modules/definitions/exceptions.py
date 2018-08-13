import traceback
import sys


def exception_hook(type, value, tb):
    msg = ''.join(traceback.format_exception(type, value, tb))
    print msg


sys.excepthook = exception_hook


class XenDroidDependencyError(Exception):
    pass


class XenDroidConnectionTimeOut(Exception):
    pass


class XenDroidConnectionError(Exception):
    pass


class XenDroidRunTimeError(Exception):
    pass


class XenDroidStartupError(XenDroidRunTimeError):
    pass
