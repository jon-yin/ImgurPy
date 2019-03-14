import os
import os.path
from functools import wraps
from concurrent.futures import as_completed

import requests

from loggers.PbarLogger import PbarLogger
from post import Post

global_logger = PbarLogger

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


def get_image_data(posts, executor, logger):
    if executor is None:
        urls = [post.image_location(logger) for post in posts if post is not None]
        logger.start_log(len(urls), "Fetching image data")
        image_data = [log_this(requests.get)(url, logger=logger).content for url in urls]
        logger.finish_log()
    else:
        image_data = []
        futures = []
        for post in posts:
            futures.append(executor.submit(get_single_image_data, post))
        logger.start_log(len(futures), "Fetching image data")
        for future in futures:
            image_data.append(future.result())
            logger.update(1)
        logger.finish_log()
    return image_data

def get_single_image_data(post):
    url = post.image_location()
    return requests.get(url).content

def download(filepath, *args, executor = None, create_album_directory=False, logger):
    flattened_posts = [post for posts in args for post in posts[1]]
    image_data = get_image_data(flattened_posts, executor, logger)
    if create_album_directory:
        filenames = [os.path.join(elem[0], post.file_name()) for elem in args for post in elem[1] if post is not None]
    else:
        filenames = [post.file_name() for elem in args for post in elem[1] if post is not None]
    logger.start_log(len(filenames), "Writing files")
    for i in range(len(filenames)):
        fullpath = os.path.join(filepath, filenames[i])
        dirname = os.path.dirname(fullpath)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        if executor is not None:
            futures = []
            futures.append(executor.submit(write_image_file, fullpath, image_data[i]))
            for future in as_completed(futures):
                logger.update(1)
        else:
            log_this(write_image_file)(fullpath, image_data[i], logger=logger)
    logger.finish_log()


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

def set_logger(new_logger):
    global global_logger
    global_logger = new_logger

def log_this(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        logger = kwargs.pop("logger")
        result = func(*args , **kwargs)
        logger.update(1)
        return result
    return wrapped
