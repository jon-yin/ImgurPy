from post import Post
import utils
import requests

test_file = "test.txt"
TEST_URL = "https://imgur.com/search/score/week?q=spongebob"
SCROLL = "https://imgur.com/search/time/all/page/1?scrolled&q=spongebob&q_size_is_mpx=off&qs=thumbs"

def driver(source):
    ids = utils.fetch_image_ids(source)
    metadatas = [utils.fetch_metadata(source, id) for id in ids]
    posts = [Post(metadata) for metadata in metadatas]
    utils.download("./test_files/album1", *posts)

# with open(test_file) as fh:
#     body = fh.read()

body = str(requests.get(SCROLL).content, encoding="utf-8")
with open("test_file_scroll.txt", "w")as fh:
     fh.write(body)
# handler = utils.SearchHandler()
# print(len(handler.fetch_image_ids(body)))
#  driver(body)