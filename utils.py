import re
import json
import requests
import os.path, os

IMG_IDS = re.compile('''\{"hash":(.*?),''')
ext_str = "(\{\"hash\":%s.*?\})"


def fetch_image_ids(data):
    return IMG_IDS.findall(data)

def fetch_metadata(data,id):
    res = re.search(ext_str % id,data)
    if res is None:
        return None
    else:
        return json.loads(res.group(1))

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




