from threading import Thread
from abc import abstractmethod, ABCMeta


class RunTimeModule(Thread):

    __metaclass__ = ABCMeta

    def __init__(self):
        Thread.__init__(self)
        self.output_path = None

    def set_paths(self):
        self.output_path = ''

    @abstractmethod
    def run(self):
        raise NotImplementedError
