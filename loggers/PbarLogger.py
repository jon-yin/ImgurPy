from loggers.AbstractLogger import AbstractLogger
import tqdm
import shutil

class PbarLogger(AbstractLogger):

    def start_log(self, num_elems, des):
        self._pbar = tqdm.tqdm(total=num_elems)
        self._pbar.set_description(des)

    def update(self, progress):
        self._pbar.update(progress)

    def finish_log(self):
        self._pbar.close()
        self._pbar = None

