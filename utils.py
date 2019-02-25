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
    PAGED_SEARCH_URL = "https://imgur.com/search/time/all/page/%s?q=spongebob&q_size_is_mpx=off&qs=thumbs"

    def fetch_image_ids(self, data):
        return SearchHandler().IMG_IDS.findall(data)

    def fetch_metadata(self, ids):
        pass

    def fetch_additional_results(self):
        pass

class SortType(Enum):
    TIME = "time"
    SCORE = "score"
    RELEVANCE = "relevance"

class SearchQuery():
    def __init__(self, type, terms):
        self.type = type
        self.terms = terms
        self.page = 1



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




