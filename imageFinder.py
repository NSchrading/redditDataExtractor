import requests
from image import Image


class ImageFinder():
    __slots__ = ()

    def __init__(self):
        pass

    @staticmethod
    def getFileType(URL):
        fileType = URL[URL.rfind("."):]
        return fileType

    def validURLImage(self, url):
        #Determine if the file is good to download.
        #Status Code must be 200 (valid page)
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            return True, response
        return False, response

    def makeImage(self, user, postID, URL, redditPostURL, defaultPath, count, response):
        fileType = self.getFileType(URL)
        if response.status_code == 200:
            return Image(user, postID, fileType, defaultPath, URL, redditPostURL, response.iter_content(4096),
                         str(count))
        else:
            return None

    def getImages(self, post, defaultPath):
        valid, response = self.validURLImage(post.url)
        if valid:
            params = (post.author.name, post.id, post.url, post.permalink, defaultPath, 1, response)
            return [self.makeImage(*params)]
        return []
