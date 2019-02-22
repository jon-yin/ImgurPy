import re
import json

IMG_IDS = re.compile('''div id=(.*?) class="post-image-container"''')
ext_str = "(\{.*\"hash\":%s.*?\})"

def fetch_image_ids(data):
    return IMG_IDS.findall(data)

def fetch_extensions(data,ids):
    print(ext_str % ids)
    res = re.search(ext_str % ids,data)
    res = re.search(ext_str % ids,data,res.pos + 1)
    if res is None:
        return None
    else:
        print(res.group(1))
        print(json.loads(res.group(1)))