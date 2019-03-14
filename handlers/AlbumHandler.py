import re
from concurrent.futures import ThreadPoolExecutor
import json
import requests
import utils
from loggers.DummyLogger import DummyLogger
from post import Post

class AlbumHandler():
    IMG_IDS = re.compile('''\{.+?"hash":(.*?),''')

    def __init__(self):
        self.executor = None
        self.logger = utils.global_logger()

    def __enter__(self):
        self.executor = ThreadPoolExecutor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.executor.shutdown()
        self.executor = None

    def fetch_metadatas(self, data):
        '''
        Fetches image metadata from an imgur gallery album
        :param data: html data corresponding to a imgur gallery
        :return: Corresponding gallery metadatas.
        '''
        first_match =  next(AlbumHandler.IMG_IDS.finditer(data))
        index = first_match.start(0)
        parsed_json = utils.parse_json(data[index+1:])
        res_json = json.loads(parsed_json)
        try:
            return res_json["album_images"]["images"]
        except KeyError:
            return [res_json]

    def download(self, links, filepath, create_album):
        multithread = (self.executor is not None)
        ids = [link.split("/")[-1].strip() for link in links]
        if (multithread):
            futures = (self.executor.submit(self.download_link, link) for link in links)
            self.logger.start_log(len(links),"Fetching imgur ids")
            bodies = [utils.log_this(future.result)(logger=self.logger) for future in futures]
            self.logger.finish_log()
        else:
            self.logger.start_log(len(links), "Fetching imgur ids")
            bodies = [utils.log_this(self.download_link)(link, logger=self.logger) for link in links]
            self.logger.finish_log()
        zipped = zip(ids, bodies)
        zipped = [item for item in zipped if item[1] is not None]
        self.logger.start_log(len(zipped), "Fetching metadatas for each id")
        metadatas = [(body[0], utils.log_this(self.fetch_metadatas)(body[1], logger=self.logger)) for body in zipped]
        self.logger.finish_log()
        posts = [(metadata[0], [Post(entry)]) for metadata in metadatas for entry in metadata[1]]
        utils.download(filepath, *posts, executor=self.executor, create_album_directory=create_album, logger=self.logger)

    @staticmethod
    def download_link(link):
        res = requests.get(link)
        if (res.status_code != 200):
            return None
        return str(res.content, encoding="utf-8")

