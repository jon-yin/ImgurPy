import abc

class AbstractLogger(abc.ABC):

    @abc.abstractmethod
    def start_log(self, num_elems, des):
        pass

    @abc.abstractmethod
    def update(self, progress):
        pass

    @abc.abstractmethod
    def finish_log(self):
        pass