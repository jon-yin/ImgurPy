from loggers.AbstractLogger import AbstractLogger

class TextLogger(AbstractLogger):
    progress_str = "{} {}/{}"

    def start_log(self, num_elems, des):
        self.total = num_elems
        self.des = des
        self.progress = 0

    def update(self, progress):
        self.progress += progress
        print(self.progress_str.format(self.des, self.progress, self.total))

    def finish_log(self):
        print("Finished", self.des)

