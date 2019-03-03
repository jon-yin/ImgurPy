import re
import json
import requests
import os.path, os
from concurrent.futures import ThreadPoolExecutor,as_completed, wait

'''
{"id":18999119,"hash":"64XlUaS","account_id":"1085967","account_url":"Seanhiruki","title":"Attack on Persona 4","score":73,"starting_score":0,"virality":6011.151723,"size":255023,"views":"343","is_hot":false,"is_album":false,"album_cover":null,"album_cover_width":0,"album_cover_height":0,"mimetype":"image\/jpeg","ext":".jpg","width":644,"height":910,"animated":false,"looping":false,"ups":73,"downs":0,"points":73,"reddit":null,"description":"","bandwidth":"83.42 MB","timestamp":"2013-11-09 06:42:06","hot_datetime":null,"gallery_datetime":"2013-11-09 06:42:06","in_gallery":true,"section":"","tags":["0","0"],"subtype":null,"spam":"0","pending":"0","comment_count":2,"nsfw":false,"topic":null,"topic_id":0,"meme_name":null,"meme_top":null,"meme_bottom":null,"prefer_video":false,"video_source":null,"video_host":null,"num_images":1,"platform":null,"readonly":false,"ad_type":0,"ad_url":"","weight":-1,"favorite_count":56,"favorited":false,"adConfig":{"safeFlags":["in_gallery","onsfw_mod_safe","gallery","page_load"],"highRiskFlags":["age_gate"],"unsafeFlags":[],"showsAds":true},"vote":null}'''

class AlbumHandler():
    ext_str = '''(\{.*?"hash":%s)'''
    IMG_IDS = re.compile('''\{.*?"hash":(.*?),''')

    def fetch_image_ids(self, data):
        return list(set(AlbumHandler.IMG_IDS.findall(data)))

    def fetch_metadata(self, data,id):
        match = next(re.finditer(self.ext_str % id,data))
        index = match.start(1)
        json_data = parse_json(data[index:])
        return json.loads(json_data)

    def fetch_metadatas(self, data, ids):
        return [self.fetch_metadata(data, id) for id in ids]



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
        ids = self.album_handler.fetch_image_ids(body)
        return self.album_handler.fetch_metadatas(body, ids)

    def fetch_metadatas(self, ids, multithread = False):
        if multithread:
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.fetch_metadata, id) for id in ids]
            results = []
            num_done = 0
            num_futs = 0
            for future in as_completed(futures, timeout=1):
                num_futs += 1
                comp = future.result()
                num_done += len(comp)
                results.append(comp)
                print("NUM_DONE", num_futs)
                print(len(results))
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
    index = 1
    res_str = "{"
    inner_braces = 1
    while inner_braces > 0:
        body.find("{")
    return res_str


def get_image_data(posts):
    urls = [post.image_location() for post in posts if post is not None]
    image_data = [requests.get(url).content for url in urls]
    return image_data

def download(filepath, *args, multithread=False, create_album_directory=False):
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    filenames = [post.file_name() for post in args if post is not None]
    image_data = get_image_data(args)
    for i in range(len(filenames)):
        if multithread:
            executor = ThreadPoolExecutor()
            executor.submit(write_image_file,os.path.join(filepath, filenames[i]), image_data[i])
        else:
            write_image_file(os.path.join(filepath, filenames[i]), image_data[i])
    if multithread:
        executor.shutdown(wait=True)


def write_image_file(filename, body, create_dir=False):
    with open(filename, "wb") as fh:
        fh.write(body)



