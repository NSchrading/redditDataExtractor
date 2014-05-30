from imageFinder import ImageFinder
import requests

class MinusImageFinder(ImageFinder):
    __slots__ = ('avoidDuplicates', 'alreadyDownloadedURLs')

    def __init__(self, alreadyDownloadedURLs, avoidDuplicates):
        super().__init__()
        self.avoidDuplicates = avoidDuplicates
        self.alreadyDownloadedURLs = alreadyDownloadedURLs

    def validURLImage(self, url):
        #Determine if the file is good to download.
        #Must not be an already-downloaded url
        #Status Code must be 200 (valid page)
        #Must have valid data response
        if self.avoidDuplicates and self.alreadyDownloadedURLs is not None and url in self.alreadyDownloadedURLs:
            return False, None
        response = requests.get(url, stream=True)
        if response.status_code == 200 and 'image' in response.headers['Content-Type']:
            return True, response
        else:
            return False, None

    def getImages(self, post, defaultPath):
        images = []
        imageURL = post.url
        valid, response = self.validURLImage(imageURL)
        if valid:
            count = 1
            params = (post.author.name, post.id, imageURL, post.permalink, defaultPath, count, response)
            image = self.makeImage(*params)
            if image is not None:
                images.append(image)
        return images