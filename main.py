import requests
import re
import json
import utils

URL = "https://i.imgur.com/EH0u0aD.jpg"
test_file = "test.txt"
with open("test.txt") as fh:
    body = fh.read()
    ids = utils.fetch_image_ids(body)
    utils.fetch_extensions(body,ids[0])
# img_page = requests.get(URL).content
# #print(img_page)
# with open(test_file, "wb") as fh:
#     fh.write(img_page)