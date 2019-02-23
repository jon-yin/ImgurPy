
class Post():
    IMAGE_LOCATION = "https://i.imgur.com/%s"

    def __init__(self, metadata):
        self.metadata = metadata
        if (metadata is None):
            raise ValueError

    def file_name(self):
        return self.metadata["hash"] + self.metadata["ext"]

    def image_location(self):
        filename = self.metadata["hash"] + self.metadata["ext"]
        return Post.IMAGE_LOCATION % filename