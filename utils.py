import re
import json
import requests
import os.path, os
from enum import Enum

ext_str = "(\{\"hash\":%s.*?\})"

class AlbumHandler():
    IMG_IDS = re.compile('''\{"hash":(.*?),''')
    def fetch_image_ids(self, data):
        return AlbumHandler.IMG_IDS.findall(data)
    def fetch_metadata(self, data,id):
        res = re.search(ext_str % id,data)
        if res is None:
            return None
        else:
            return json.loads(res.group(1))

class SearchHandler():
    IMG_IDS = re.compile('''"/gallery/(.*?)"''')
    TYPES = re.compile('''<div class="post-info">(.*?)\&''')
    IMAGE_LINK = "https://imgur.com/gallery/{}"

    def __init__(self, query, limit=-1):
        self.album_handler = AlbumHandler()
        self.limit = limit
        if isinstance(query, SearchQuery):
            self.query =query
        else:
            raise ValueError("expected SearchQuery object")

    def fetch_image_ids(self):
        collected_results = set()
        last_found = 0
        found_ids = 0
        page = 1
        cont = found_ids < self.limit or self.limit == -1
        while cont:
            data = self.query.fetch_page(page)
            collected_results.update(SearchHandler().IMG_IDS.findall(data))
            last_found = found_ids
            found_ids = len(collected_results)
            page += 1
            if (last_found == found_ids):
                # found all possible results, exit
                break
            cont = found_ids < self.limit or self.limit == -1
        return list(collected_results)

    def fetch_metadata(self, id):
        body = requests.get(self.IMAGE_LINK.format(id))
        ids = self.album_handler.fetch_image_ids(body)
        return [self.album_handler.fetch_metadata(body, id) for id in ids]


class SearchQuery():
    allowed_times = {"day", "week", "month", "year", "all"}
    allowed_types = {"time", "score", "relevance"}
    PAGED_SEARCH_URL = "https://imgur.com/search/{0}/{1}/page/{2}"
    def __init__(self, type, time, terms):
        if type not in self.allowed_types:
            raise ValueError("Type not one of " + self.allowed_types)
        if time not in self.allowed_times:
            raise ValueError("Time not one of " + self.allowed_times)
        self.type = type
        self.params =  {"q":build_search_query(terms)}

    def fetch_page(self, page):
        res = requests.get(self.PAGED_SEARCH_URL.format((self.type, self.time, page)), params= self.params)
        if (res.status_code != 200):
            return None
        return res.content







def build_search_query(query : str):
    return query.replace(" ", "_")

def download(filepath, *args, multithread=False):
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    filenames = [post.file_name() for post in args if post is not None]
    urls = [post.image_location() for post in args if post is not None]
    for i in range(len(urls)):
        body = requests.get(urls[i]).content
        filename = os.path.join(filepath, filenames[i])
        with open(filename, "wb") as fh:
            fh.write(body)



