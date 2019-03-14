import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

import utils
from handlers.AlbumHandler import AlbumHandler


class SearchHandler():
    IMG_IDS = re.compile('''"/gallery/(.*?)"''')
    IMAGE_LINK = "https://imgur.com/gallery/{}"

    def __init__(self, query, limit=float("inf")):
        self._album_handler = AlbumHandler()
        self.limit = limit
        self.multithread = False
        self.query = query
        self.logger = utils.global_logger()

    def __enter__(self):
        self._album_handler.executor = ThreadPoolExecutor()
        self.multithread = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._album_handler.executor.shutdown()
        self.multithread = False
        self._album_handler.executor = None

    def fetch_image_ids(self):
        collected_results = set()
        last_found = 0
        found_ids = 0
        page = 1
        cont = found_ids < self.limit
        self.logger.start_log(self.limit, "Fetching imgur ids")
        while cont:
            data = self.query.fetch_page(page)
            collected_results.update(SearchHandler.IMG_IDS.findall(data))
            last_found = found_ids
            found_ids = len(collected_results)
            page += 1
            if (last_found == found_ids):
                # found all possible results, exit
                break
            if (found_ids > self.limit):
                self.logger.update(found_ids - last_found - (found_ids - self.limit))
            else:
                self.logger.update(found_ids - last_found)
            cont = found_ids < self.limit
        res = list(collected_results)
        self.logger.finish_log()
        if (len(res) > self.limit):
            return res[:self.limit]
        return res

    def fetch_metadata(self, id):
        res = requests.get(self.IMAGE_LINK.format(id))
        body = str(res.content, encoding="utf-8")
        return (id, self._album_handler.fetch_metadatas(body))

    def fetch_metadatas(self, ids, executor):
        if self.multithread:
            futures = [executor.submit(self.fetch_metadata, id) for id in ids]
            results = []
            self.logger.start_log(len(futures), "Fetching metadatas for each id")
            for future in as_completed(futures):
                comp = future.result()
                results.append(comp)
                self.logger.update(1)
            self.logger.finish_log()
            return results
        self.logger.start_log(len(ids), "Fetching metadatas for each id")
        results = [utils.log_this(self.fetch_metadata)(id, logger=self.logger) for id in ids]
        self.logger.finish_log()
        return results

    def download(self, filepath, create_album):
        ids = self.fetch_image_ids()
        metadatas = self.fetch_metadatas(ids, self._album_handler.executor)
        posts = utils.create_posts(metadatas)
        utils.download(filepath, *posts, executor=self._album_handler.executor, create_album_directory=create_album, logger=self.logger)

class SearchQuery():
    allowed_times = {"day", "week", "month", "year", "all"}
    allowed_types = {"time", "score", "relevance"}
    PAGED_SEARCH_URL = "https://imgur.com/search/{0}/{1}/page/{2}"
    FIRST_PAGE_URL = PAGED_SEARCH_URL[:33]

    def __init__(self, type, time):
        if type not in self.allowed_types:
            raise ValueError("Type not one of " + str(self.allowed_types))
        if time not in self.allowed_times:
            raise ValueError("Time not one of " + str(self.allowed_times))
        self.type = type
        self.time = time

    def set_params(self, params):
        self.params = params

    def set_simple_query(self, query):
        self.params = {"q":query}

    def fetch_page(self, page):
        if (page == 1):
            res =requests.get(self.FIRST_PAGE_URL.format(self.type, self.time), params=self.params)
        else:
            res = requests.get(self.PAGED_SEARCH_URL.format(self.type, self.time, page-1), params=self.params)
        if (res.status_code != 200):
            return None
        return str(res.content, encoding="utf-8")
