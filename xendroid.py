import logging
from modules.analysis_manager import AnalysisManager


class XenDroid(object):

    def __init__(self, apk_path, device_serial, debug_mode):

        logging.basicConfig(level=logging.DEBUG if debug_mode else logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.apk_path = apk_path
        self.device_serial = device_serial

    def run(self):

        analysis = AnalysisManager(self.apk_path, self.device_serial)
        analysis.start()
