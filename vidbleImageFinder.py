from imageFinder import ImageFinder
from bs4 import BeautifulSoup
import requests

class VidbleImageFinder(ImageFinder):
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

    def getImageURLs(self, URL):
        validURLs = []
        endOfURL = URL[URL.rfind('/') + 1:]
        if "." in endOfURL:
            fileType = self.getFileType(endOfURL)
            if len(fileType) > 1:
                validURLs.append("http://www.vidble.com/" + endOfURL)
        elif '/show/' in URL:
            URL = URL[URL.rfind('/')]
            response = requests.get("http://www.vidble.com/" + endOfURL)
            if response.status_code == 200:
                text = response.text
                soup = BeautifulSoup(text)
                imgs = soup.find_all('img')
                if len(imgs) == 1:
                    validURLs.append("http://www.vidble.com/" + imgs[0]['src'])
        elif '/album/' in URL:
            response = requests.get(URL)
            if response.status_code == 200:
                text = response.text
                soup = BeautifulSoup(text)
                imgs = soup.find_all('img')
                for img in imgs:
                    imgClass = img.get('class')
                    if imgClass is not None and imgClass[0] == 'img2':
                        validURLs.append("http://www.vidble.com" + img['src'])
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