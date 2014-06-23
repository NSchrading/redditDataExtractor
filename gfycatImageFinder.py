from imageFinder import ImageFinder
import requests

class GfycatImageFinder(ImageFinder):
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
        if response.status_code == 200 and 'webm' in response.headers['Content-Type']:
            return True, response
        else:
            return False, None

    def getImageURLs(self, URL):
        validURLs = []
        endOfURL = URL[URL.rfind('/') + 1:]
        apiCall = "http://gfycat.com/cajax/get/" + endOfURL
        response = requests.get(apiCall)
        print(apiCall)
        if response.status_code == 200 and 'json' in response.headers['Content-Type']:
            json = response.json()
            gfyItem = json.get("gfyItem")
            if gfyItem is not None and gfyItem.get("webmUrl") is not None:
                validURLs.append(gfyItem.get("webmUrl"))
        return validURLs


    def getImages(self, post, defaultPath):
        images = []
        URL = post.url
        imageURLs = self.getImageURLs(URL)
        count = 1
        for imageURL in imageURLs:
            valid, response = self.validURLImage(imageURL)
            if valid:
                params = (post.author.name, post.id, imageURL, post.permalink, defaultPath, count, response)
                image = self.makeImage(*params)
                if image is not None:
                    images.append(image)
                    count += 1
        return images