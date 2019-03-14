from loggers.AbstractLogger import AbstractLogger

class DummyLogger(AbstractLogger):

    def start_log(self, num_elems, des):
        pass

    def update(self, progress):
        pass

    def finish_log(self):
        pass