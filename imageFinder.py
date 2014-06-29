import requests
from image import Image


class ImgurLinkTypeEnum():
    DIRECT = 1
    SINGLE_PAGE = 2
    ALBUM = 3

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
        #Must have 'image' in the response header
        response = requests.get(url, stream=True)
        if response.status_code == 200 and 'image' in response.headers['Content-Type']:
            return True, response
        return False, response

    def makeImage(self, user, postID, URL, redditPostURL, defaultPath, count, response, commentAuthor=None, commentAuthorURLCount=None):
        fileType = self.getFileType(URL)
        if response.status_code == 200:
            return Image(user, postID, fileType, defaultPath, URL, redditPostURL, response.iter_content(4096),
                         str(count), commentAuthor, commentAuthorURLCount)
        else:
            return None

    def getImages(self, post, defaultPath, commentAuthor=None, commentAuthorURLCount=None):
        valid, response = self.validURLImage(post.url)
        if valid:
            params = (post.author.name, post.id, post.url, post.permalink, defaultPath, 1, response, commentAuthor, commentAuthorURLCount)
            return [self.makeImage(*params)]
        return []

class ImgurImageFinder(ImageFinder):
    __slots__ = ('CLIENT_ID', 'imgurLinkType', 'avoidDuplicates', 'alreadyDownloadedImgurURLs', 'alreadyQueriedURLs')

    def __init__(self, alreadyDownloadedImgurURLs, avoidDuplicates):
        super().__init__()
        self.CLIENT_ID = 'e0ea61b57d4c3c9'  # imgur client ID for API access
        self.imgurLinkType = None
        self.avoidDuplicates = avoidDuplicates
        self.alreadyDownloadedImgurURLs = alreadyDownloadedImgurURLs
        self.alreadyQueriedURLs = set([])

    def validURLImage(self, url):
        #Determine if the file is good to download.
        #Must not be an already-downloaded imgur url
        #Status Code must be 200 (valid page)
        #Must have valid data response
        if self.avoidDuplicates and self.alreadyDownloadedImgurURLs is not None and url in self.alreadyDownloadedImgurURLs:
            return False, None
        headers = {'Authorization': 'Client-ID ' + self.CLIENT_ID}
        apiURL = 'https://api.imgur.com/3/'
        if self.imgurLinkType == ImgurLinkTypeEnum.DIRECT or self.imgurLinkType == ImgurLinkTypeEnum.SINGLE_PAGE:
            imgurHashID = url[url.rfind('/') + 1:]
            dotIndex = imgurHashID.rfind('.')
            if dotIndex != -1:
                imgurHashID = imgurHashID[:imgurHashID.rfind('.')]
            apiURL += 'image/' + imgurHashID + '.json'
        else:
            imgurHashID = url[url.rfind('/') + 1:]
            apiURL += 'album/' + imgurHashID + '.json'
        if apiURL in self.alreadyQueriedURLs: # Regardless of if we want to avoid duplicates, we always want to reduce API calls
            return False, None
        response = requests.get(apiURL, headers=headers, stream=True)
        self.alreadyQueriedURLs.add(apiURL)
        print(apiURL)
        json = response.json()
        status = json.get('status')
        success = json.get('success')
        if (status is None and json.get('error') is not None) or (not success):
            return False, None
        elif (status is not None and status == 200) and (
                json.get('image') is not None or json.get('data') is not None) and success:
            return True, response
        else:
            return False, None

    def getImageURLsDirect(self, response, imageURLs):
        data = response.json().get('data')
        if data is not None:
            link = data.get('link')
            if link is not None:
                imageURLs.append(link)

    def getImageURLsPage(self, response, imageURLs):
        image = response.json().get('image')
        if image is not None:
            links = image.get('links')
            if links is not None:
                original = links.get('original')
                imageURLs.append(original)
        if len(imageURLs) <= 0: # if the above method doesn't work, try direct
            self.getImageURLsDirect(response, imageURLs)

    def getImageURLsAlbum(self, response, imageURLs):
        data = response.json().get('data')
        if data is not None:
            images = data.get('images')
            if images is not None:
                for image in images:
                    link = image.get('link')
                    if link is not None:
                        imageURLs.append(link)

    def getImageURLs(self, url):
        valid, response = self.validURLImage(url)
        imageURLs = []
        if valid:
            if self.imgurLinkType == ImgurLinkTypeEnum.DIRECT:
                self.getImageURLsDirect(response, imageURLs)
            elif self.imgurLinkType == ImgurLinkTypeEnum.SINGLE_PAGE:
                self.getImageURLsPage(response, imageURLs)
            else:
                self.getImageURLsAlbum(response, imageURLs)
        return imageURLs

    def getImgurLinkType(self, url):
        if "i.imgur.com" in url:
            return ImgurLinkTypeEnum.DIRECT
        elif "imgur.com/a/" in url:
            return ImgurLinkTypeEnum.ALBUM
        else:
            return ImgurLinkTypeEnum.SINGLE_PAGE

    def getImages(self, post, defaultPath, commentAuthor=None, commentAuthorURLCount=None):
        images = []
        self.imgurLinkType = self.getImgurLinkType(post.url)
        imageURLs = self.getImageURLs(post.url)
        count = 1
        for imageURL in imageURLs:
            response = requests.get(imageURL)
            params = (post.author.name, post.id, imageURL, post.permalink, defaultPath, count, response, commentAuthor, commentAuthorURLCount)
            image = self.makeImage(*params)
            if image is not None:
                images.append(image)
                count += 1
        return images

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


    def getImages(self, post, defaultPath, commentAuthor=None, commentAuthorURLCount=None):
        images = []
        URL = post.url
        imageURLs = self.getImageURLs(URL)
        count = 1
        for imageURL in imageURLs:
            valid, response = self.validURLImage(imageURL)
            if valid:
                params = (post.author.name, post.id, imageURL, post.permalink, defaultPath, count, response, commentAuthor, commentAuthorURLCount)
                image = self.makeImage(*params)
                if image is not None:
                    images.append(image)
                    count += 1
        return images

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

    def getImages(self, post, defaultPath, commentAuthor=None, commentAuthorURLCount=None):
        images = []
        imageURL = post.url
        valid, response = self.validURLImage(imageURL)
        if valid:
            count = 1
            params = (post.author.name, post.id, imageURL, post.permalink, defaultPath, count, response, commentAuthor, commentAuthorURLCount)
            image = self.makeImage(*params)
            if image is not None:
                images.append(image)
        return images


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


    def getImages(self, post, defaultPath, commentAuthor=None, commentAuthorURLCount=None):
        images = []
        URL = post.url
        imageURLs = self.getImageURLs(URL)
        count = 1
        for imageURL in imageURLs:
            valid, response = self.validURLImage(imageURL)
            if valid:
                params = (post.author.name, post.id, imageURL, post.permalink, defaultPath, count, response, commentAuthor, commentAuthorURLCount)
                image = self.makeImage(*params)
                if image is not None:
                    images.append(image)
                    count += 1
        return images

