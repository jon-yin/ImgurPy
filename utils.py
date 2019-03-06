import re
import json
import requests
import os.path, os
from concurrent.futures import ThreadPoolExecutor,as_completed
import tqdm

class AlbumHandler():
    IMG_IDS = re.compile('''\{.+?"hash":(.*?),''')

    def fetch_metadatas(self, data):
        first_match =  next(AlbumHandler.IMG_IDS.finditer(data))
        index = first_match.start(0)
        parsed_json = parse_json(data[index+1:])
        res_json = json.loads(parsed_json)
        try:
            return res_json["album_images"]["images"]
        except KeyError:
            return [res_json]

    def handle_urls(self,urls):
        datas = [requests.get(url) for url in urls]
        return [self.fetch_metadatas(data) for data in datas]



class SearchHandler():
    IMG_IDS = re.compile('''"/gallery/(.*?)"''')
    IMAGE_LINK = "https://imgur.com/gallery/{}"

    def __init__(self, query, limit=-1):
        self.album_handler = AlbumHandler()
        self.limit = limit
        if isinstance(query, SearchQuery):
            self.query = query
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
            collected_results.update(SearchHandler.IMG_IDS.findall(data))
            last_found = found_ids
            found_ids = len(collected_results)
            page += 1
            if (last_found == found_ids):
                # found all possible results, exit
                break
            cont = found_ids < self.limit or self.limit == -1
        res = list(collected_results)
        if (len(res) > self.limit and self.limit != -1):
            return res[:self.limit]
        return res

    def fetch_metadata(self, id):
        res = requests.get(self.IMAGE_LINK.format(id))
        body = str(res.content, encoding="utf-8")
        return (id, self.album_handler.fetch_metadatas(body))

    def fetch_metadatas(self, ids, multithread = False):
        if multithread:
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.fetch_metadata, id) for id in ids]
            results = []
            with tqdm.tqdm(total=len(futures)) as pbar:
                pbar.desc = "Fetching and parsing metadata"
                for future in as_completed(futures):
                    comp = future.result()
                    results.append(comp)
                    pbar.update(1)
            return results
        return [self.fetch_metadata(id) for id in ids]


class SearchQuery():
    allowed_times = {"day", "week", "month", "year", "all"}
    allowed_types = {"time", "score", "relevance"}
    PAGED_SEARCH_URL = "https://imgur.com/search/{0}/{1}/page/{2}"
    FIRST_PAGE_URL = PAGED_SEARCH_URL[:33]

    def __init__(self, type, time, terms):
        if type not in self.allowed_types:
            raise ValueError("Type not one of " + str(self.allowed_types))
        if time not in self.allowed_times:
            raise ValueError("Time not one of " + str(self.allowed_times))
        self.type = type
        self.time = time
        self.params = {"q":terms}

    def fetch_page(self, page):
        if (page == 1):
            res =requests.get(self.FIRST_PAGE_URL.format(self.type, self.time), params=self.params)
        else:
            res = requests.get(self.PAGED_SEARCH_URL.format(self.type, self.time, page-1), params=self.params)
        if (res.status_code != 200):
            return None
        return str(res.content, encoding="utf-8")

    class SearchType():
        TIME = "time"
        SCORE = "score"
        RELEVANCE = "relevance"

    class SearchTime():
        DAY = "day"
        WEEK = "week"
        MONTH = "month"
        YEAR = "year"
        ALL = "all"

def parse_json(body):
    res_str = "{"
    inner_braces = 1
    while inner_braces > 0:
        index = body.find("{")
        index_2 = body.find("}")
        if index == -1 and index_2 == -1:
            raise ValueError("Expected Json to end")
        if index == -1:
            index = index_2 + 1
        elif index_2 == -1:
            index_2 = index + 1
        first_index = min(index, index_2)
        res_str += body[:first_index + 1]
        body = body[first_index+1:]
        if (first_index == index):
            inner_braces += 1
        else:
            inner_braces -= 1
    return res_str


def get_image_data(posts, executor=None, log=True):
    if executor is None:
        urls = [post.image_location() for post in posts if post is not None]
        if log:
            print("Downloading images")
        futures = [requests.get(url).content for url in urls]
        if log:
            print("Downloading complete")
    else:
        image_data = []
        futures = []
        for post in posts:
            futures.append(executor.submit(get_single_image_data, post))
        if log:
            pbar = tqdm.tqdm(total=len(futures))
            pbar.set_description("Downloading images")
        for future in futures:
            image_data.append(future.result())
            if log:
                pbar.update(1)
        if log:
            pbar.close()
    return image_data

def get_single_image_data(post):
    url = post.image_location()
    return requests.get(url).content

def download(filepath, *args, multithread=False, create_album_directory=False, log=True):
    flattened_posts = [post for posts in args for post in posts[1]]

    if multithread:
        executor = ThreadPoolExecutor()
        image_data = get_image_data(flattened_posts, executor,log)
    else:
        image_data = get_image_data(flattened_posts,log=log)
    if create_album_directory:
        filenames = [os.path.join(elem[0], post.file_name()) for elem in args for post in elem[1] if post is not None]
    else:
        filenames = [post.file_name() for elem in args for post in elem[1] if post is not None]
    print("Writing Files")
    for i in range(len(filenames)):
        fullpath = os.path.join(filepath, filenames[i])
        dirname = os.path.dirname(fullpath)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        if multithread:
            futures = []
            futures.append(executor.submit(write_image_file, fullpath, image_data[i]))
        else:
            write_image_file(fullpath, image_data[i])
    print("Writing Complete")
    if multithread:
        executor.shutdown(wait=True)


def write_image_file(filename, body):
    with open(filename, "wb") as fh:
        fh.write(body)

def append_parent_dir(posts):
    for elem in posts:
        dir_name = elem[0].split(".")[0]
        for i in range(len(elem)):
            elem[i] = os.path.join(dir_name, elem[i])
    return posts



