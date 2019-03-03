
class Post():
    IMAGE_LOCATION = "https://i.imgur.com/%s"

    def __init__(self, metadata):
        self.metadata = metadata
        if (metadata is None):
            raise ValueError

    def file_name(self):
        ext = self.metadata["ext"]
        ext = ext[0:4]
        return self.metadata["hash"] + ext

    def image_location(self):
        filename = self.metadata["hash"] + self.metadata["ext"]
        return Post.IMAGE_LOCATION % filename
