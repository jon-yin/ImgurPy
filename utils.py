import re
import json
import requests
import os.path, os
from concurrent.futures import ThreadPoolExecutor,as_completed
import tqdm
from post import Post

class AlbumHandler():
    IMG_IDS = re.compile('''\{.+?"hash":(.*?),''')

    def __init__(self):
        self.executor = None

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
        parsed_json = parse_json(data[index+1:])
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
            bodies = [future.result() for future in futures]
        else:
            bodies = [self.download_link(link) for link in links]
        zipped = zip(ids, bodies)
        zipped = [item for item in zipped if item[1] is not None]
        metadatas = [(body[0], self.fetch_metadatas(body[1])) for body in zipped]
        posts = [(metadata[0], [Post(entry)]) for metadata in metadatas for entry in metadata[1]]
        download(filepath, *posts, executor=self.executor, create_album_directory=create_album)

    def download_link(self, link):
        res = requests.get(link)
        if (res.status_code != 200):
            return None
        return str(res.content, encoding="utf-8")


class SearchHandler():
    IMG_IDS = re.compile('''"/gallery/(.*?)"''')
    IMAGE_LINK = "https://imgur.com/gallery/{}"

    def __init__(self, query, limit=float("inf")):
        self._album_handler = AlbumHandler()
        self.limit = limit
        self.multithread = False
        if isinstance(query, SearchQuery):
            self.query = query
        else:
            raise ValueError("expected SearchQuery object")

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
        while cont:
            data = self.query.fetch_page(page)
            collected_results.update(SearchHandler.IMG_IDS.findall(data))
            last_found = found_ids
            found_ids = len(collected_results)
            page += 1
            if (last_found == found_ids):
                # found all possible results, exit
                break
            cont = found_ids < self.limit
        res = list(collected_results)
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
            for future in as_completed(futures):
                comp = future.result()
                results.append(comp)
            return results
        return [self.fetch_metadata(id) for id in ids]

    def download(self, filepath, create_album):
        ids = self.fetch_image_ids()
        metadatas = self.fetch_metadatas(ids, self._album_handler.executor)
        posts = create_posts(metadatas)
        download(filepath, *posts, executor=self._album_handler.executor, create_album_directory=create_album)

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


def get_image_data(posts, executor, log=True):
    if executor is None:
        urls = [post.image_location() for post in posts if post is not None]
        image_data = [requests.get(url).content for url in urls]
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

def download(filepath, *args, executor = None, create_album_directory=False, log=False):
    flattened_posts = [post for posts in args for post in posts[1]]
    image_data = get_image_data(flattened_posts, executor, log=log)
    if create_album_directory:
        filenames = [os.path.join(elem[0], post.file_name()) for elem in args for post in elem[1] if post is not None]
    else:
        filenames = [post.file_name() for elem in args for post in elem[1] if post is not None]
    for i in range(len(filenames)):
        fullpath = os.path.join(filepath, filenames[i])
        dirname = os.path.dirname(fullpath)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        if executor is not None:
            futures = []
            futures.append(executor.submit(write_image_file, fullpath, image_data[i]))
        else:
            write_image_file(fullpath, image_data[i])
    print("Writing Complete")


def write_image_file(filename, body):
    with open(filename, "wb") as fh:
        fh.write(body)

def append_parent_dir(posts):
    for elem in posts:
        dir_name = elem[0].split(".")[0]
        for i in range(len(elem)):
            elem[i] = os.path.join(dir_name, elem[i])
    return posts

def create_posts(metadatas):
    return [(elem[0], [Post(item) for item in elem[1]]) for elem in metadatas if elem is not None]

