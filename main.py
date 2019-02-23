from post import Post
import utils
import requests

test_file = "test.txt"

def driver(source):
    ids = utils.fetch_image_ids(source)
    metadatas = [utils.fetch_metadata(source, id) for id in ids]
    posts = [Post(metadata) for metadata in metadatas]
    utils.download("./test_files/album1", *posts)

with open(test_file) as fh:
    body = fh.read()

body = str(requests.get(TEST_URL).content, encoding="utf-8")
#with open("test_file_2.txt", "w")as fh:
#    fh.write(body)
driver(body)