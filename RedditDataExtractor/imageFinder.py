import requests

from bs4 import BeautifulSoup
from contextlib import closing
from .image import Image


def debug(target):
    def wrapper(*args, **kwargs):
        print('Calling function "%s" with arguments %s and keyword arguments %s' % (target.__name__, args, kwargs))
        return target(*args, **kwargs)

    return wrapper

class ImgurLinkTypeEnum():
    DIRECT = 1
    SINGLE_PAGE = 2
    ALBUM = 3
    GALLERY = 4

class ImageFinder():
    __slots__ = ('requestsSession', 'queue')

    def __init__(self, queue):
        self.requestsSession = requests.session()
        self.requestsSession.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'
        self.queue = queue

    def exceptionSafeJsonRequest(self, *args, **kwargs):
        try:
            with closing(self.requestsSession.get(*args, **kwargs)) as response:
                if response.status_code == 200 and 'json' in response.headers['Content-Type']:
                    return response.json()
                else:
                    return None
        except:
            # probably should actually do something here like log the error
            pass
        return None

    def exceptionSafeImageRequest(self, *args, **kwargs):
        try:
            response = self.requestsSession.get(*args, **kwargs)
            if response.status_code == 200 and 'image' in response.headers['Content-Type']:
                return response.iter_content(1024)
            else:
                return None
        except:
            self.queue.put(">>> Failed to connect to " + str(*args) + ".\n>>> To attempt to redownload this file, uncheck 'Restrict retrieved submissions to creation dates after the last downloaded submission' in the settings.\n")
        return None

    def exceptionSafeWebmRequest(self, *args, **kwargs):
        try:
            response = self.requestsSession.get(*args, **kwargs)
            if response.status_code == 200 and 'webm' in response.headers['Content-Type']:
                return response.iter_content(1024)
            else:
                return None
        except:
            self.queue.put(">>> Failed to connect to " + str(*args) + ".\n>>> To attempt to redownload this file, uncheck 'Restrict retrieved submissions to creation dates after the last downloaded submission' in the settings.\n")
        return None

    def exceptionSafeTextRequest(self, *args, **kwargs):
        try:
            with closing(self.requestsSession.get(*args, **kwargs)) as response:
                if response.status_code == 200 and 'text' in response.headers['Content-Type']:
                    return response.text
                else:
                    return None
        except:
            # probably should actually do something here like log the error
            pass
        return None

    @staticmethod
    def getFileType(URL):
        fileType = URL[URL.rfind("."):]
        fileType = fileType.lower()
        # Sometimes things will be added to the end of the file type from urls like www.blah.com/foo.jpg?w=1280&h=1024
        # We don't want the ?whatever stuff, so just return plain file types if possible
        if '.jpg' in fileType or '.jpeg' in fileType:
            return '.jpg'
        elif '.png' in fileType:
            return '.png'
        elif '.webm' in fileType:
            return '.webm'
        elif '.gif' in fileType:
            return '.gif'
        else:
            return ".jpg" # default to jpg and hope for the best

    @debug
    def validURLImage(self, url):
        #Determine if the file is good to download.
        #Status Code must be 200 (valid page)
        #Must have 'image' in the response header
        response = self.exceptionSafeImageRequest(url, stream=True)
        if response is not None:
            return True, response
        return False, None

    def makeImage(self, user, postID, URL, redditPostURL, defaultPath, count, response, specialString=None, specialCount=None, specialPath=None):
        fileType = self.getFileType(URL)
        return Image(user, postID, fileType, defaultPath, URL, redditPostURL, response,
                         str(count), specialString, specialCount, specialPath)

    def getImages(self, post, defaultPath, user, specialString=None, specialCount=None, specialPath=None):
        valid, response = self.validURLImage(post.url)
        if valid:
            params = (user.name, post.id, post.url, post.permalink, defaultPath, 1, response, specialString, specialCount, specialPath)
            yield self.makeImage(*params)

class ImgurImageFinder(ImageFinder):
    __slots__ = ('CLIENT_ID', 'imgurLinkType', 'avoidDuplicates', 'alreadyDownloadedImgurURLs', 'alreadyQueriedURLs')

    def __init__(self, alreadyDownloadedImgurURLs, avoidDuplicates, queue):
        super().__init__(queue)
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
        headers = {'Authorization': 'Client-ID ' + self.CLIENT_ID}
        apiURL = 'https://api.imgur.com/3/'
        if self.imgurLinkType == ImgurLinkTypeEnum.DIRECT or self.imgurLinkType == ImgurLinkTypeEnum.SINGLE_PAGE:
            imgurHashID = url[url.rfind('/') + 1:]
            dotIndex = imgurHashID.rfind('.')
            if dotIndex != -1:
                imgurHashID = imgurHashID[:imgurHashID.rfind('.')]
            apiURL += 'image/' + imgurHashID
        elif self.imgurLinkType == ImgurLinkTypeEnum.GALLERY:
            imgurHashID = url[url.rfind('/') + 1:]
            apiURL += 'gallery/' + imgurHashID
        else:
            imgurHashID = url[url.rfind('/') + 1:]
            apiURL += 'album/' + imgurHashID
        if apiURL in self.alreadyQueriedURLs: # Regardless of if we want to avoid duplicates, we always want to reduce API calls
            return False, None
        json = self.exceptionSafeJsonRequest(apiURL, headers=headers, stream=True)
        if json is not None:
            self.alreadyQueriedURLs.add(apiURL)
            print(apiURL)
            status = json.get('status')
            success = json.get('success')
            if (status is None and json.get('error') is not None) or (not success):
                return False, None
            elif (status is not None and status == 200) and (
                    json.get('image') is not None or json.get('data') is not None) and success:
                return True, json
            else:
                return False, None
        return False, None

    def getImageURLsDirect(self, json, imageURLs):
        data = json.get('data')
        if data is not None:
            link = data.get('link')
            if link is not None and (not self.avoidDuplicates or (self.alreadyDownloadedImgurURLs is not None and link not in self.alreadyDownloadedImgurURLs)):
                imageURLs.append(link)

    def getImageURLsPage(self, json, imageURLs):
        image = json.get('image')
        if image is not None:
            links = image.get('links')
            if links is not None:
                original = links.get('original')
                if original is not None and (not self.avoidDuplicates or (self.alreadyDownloadedImgurURLs is not None and original not in self.alreadyDownloadedImgurURLs)):
                    imageURLs.append(original)
        if len(imageURLs) <= 0: # if the above method doesn't work, try direct
            self.getImageURLsDirect(json, imageURLs)

    def getImageURLsAlbum(self, json, imageURLs):
        data = json.get('data')
        if data is not None:
            images = data.get('images')
            if images is not None:
                for image in images:
                    link = image.get('link')
                    if link is not None and (not self.avoidDuplicates or (self.alreadyDownloadedImgurURLs is not None and link not in self.alreadyDownloadedImgurURLs)):
                        imageURLs.append(link)

    def getImageURLs(self, url):
        valid, json = self.validURLImage(url)
        imageURLs = []
        if valid:
            if self.imgurLinkType == ImgurLinkTypeEnum.DIRECT:
                self.getImageURLsDirect(json, imageURLs)
            elif self.imgurLinkType == ImgurLinkTypeEnum.SINGLE_PAGE:
                self.getImageURLsPage(json, imageURLs)
            else: # album and gallery json response is the same
                self.getImageURLsAlbum(json, imageURLs)
        return imageURLs

    def getImgurLinkType(self, url):
        if "i.imgur.com" in url:
            return ImgurLinkTypeEnum.DIRECT
        elif "imgur.com/a/" in url:
            return ImgurLinkTypeEnum.ALBUM
        elif "imgur.com/gallery/" in url:
            return ImgurLinkTypeEnum.GALLERY
        else:
            return ImgurLinkTypeEnum.SINGLE_PAGE

    def getImages(self, post, defaultPath, user, specialString=None, specialCount=None, specialPath=None):
        self.imgurLinkType = self.getImgurLinkType(post.url)
        imageURLs = self.getImageURLs(post.url)
        count = 1
        for imageURL in imageURLs:
            response = self.exceptionSafeImageRequest(imageURL, stream=True)
            if response is None:
                continue
            params = (user.name, post.id, imageURL, post.permalink, defaultPath, count, response, specialString, specialCount, specialPath)
            image = self.makeImage(*params)
            if image is not None:
                count += 1
                yield image

class GfycatImageFinder(ImageFinder):
    __slots__ = ('avoidDuplicates', 'alreadyDownloadedURLs')

    def __init__(self, alreadyDownloadedURLs, avoidDuplicates, queue):
        super().__init__(queue)
        self.avoidDuplicates = avoidDuplicates
        self.alreadyDownloadedURLs = alreadyDownloadedURLs

    def validURLImage(self, url):
        #Determine if the file is good to download.
        #Must not be an already-downloaded url
        #Status Code must be 200 (valid page)
        #Must have valid data response
        if self.avoidDuplicates and self.alreadyDownloadedURLs is not None and url in self.alreadyDownloadedURLs:
            return False, None
        response = self.exceptionSafeWebmRequest(url, stream=True)
        if response is not None:
            return True, response
        else:
            return False, None

    def getImageURLs(self, URL):
        validURLs = []
        endOfURL = URL[URL.rfind('/') + 1:]
        apiCall = "http://gfycat.com/cajax/get/" + endOfURL
        json = self.exceptionSafeJsonRequest(apiCall)
        print(apiCall)
        if json is not None:
            gfyItem = json.get("gfyItem")
            if gfyItem is not None and gfyItem.get("webmUrl") is not None:
                validURLs.append(gfyItem.get("webmUrl"))
        return validURLs


    def getImages(self, post, defaultPath, user, specialString=None, specialCount=None, specialPath=None):
        URL = post.url
        imageURLs = self.getImageURLs(URL)
        count = 1
        for imageURL in imageURLs:
            valid, response = self.validURLImage(imageURL)
            if valid:
                params = (user.name, post.id, imageURL, post.permalink, defaultPath, count, response, specialString, specialCount, specialPath)
                image = self.makeImage(*params)
                if image is not None:
                    count += 1
                    yield image

class MinusImageFinder(ImageFinder):
    __slots__ = ('avoidDuplicates', 'alreadyDownloadedURLs')

    def __init__(self, alreadyDownloadedURLs, avoidDuplicates, queue):
        super().__init__(queue)
        self.avoidDuplicates = avoidDuplicates
        self.alreadyDownloadedURLs = alreadyDownloadedURLs

    def validURLImage(self, url):
        #Determine if the file is good to download.
        #Must not be an already-downloaded url
        #Status Code must be 200 (valid page)
        #Must have valid data response
        if self.avoidDuplicates and self.alreadyDownloadedURLs is not None and url in self.alreadyDownloadedURLs:
            return False, None
        response = self.exceptionSafeImageRequest(url, stream=True)
        if response is not None:
            return True, response
        else:
            return False, None

    def getImageURLs(self, URL):
        validURLs = []
        endOfURL = URL[URL.rfind('/') + 1:]
        if "." in endOfURL:
            fileType = self.getFileType(endOfURL)
            if len(fileType) > 1:
                validURLs.append("http://i.minus.com/" + endOfURL)
        else:
            text = self.exceptionSafeTextRequest("http://minus.com/i/" + endOfURL, stream=True)
            if text is None:
                text = self.exceptionSafeTextRequest("http://minus.com/" + endOfURL, stream=True)
            if text is not None:
                soup = BeautifulSoup(text)
                type = soup.find(property="og:type")
                if type is not None and type.get('content') is not None:
                    content = type.get('content')
                    if 'gallery' in content:
                        pass # galleries not currently supported. If I get minus api credentials I might be able to do it
                    elif 'photo' in content:
                        imageHTML = soup.find("a", "item-main is-image")
                        if imageHTML.get("href") is not None:
                            validURLs.append(imageHTML.get("href"))
        return validURLs

    def getImages(self, post, defaultPath, user, specialString=None, specialCount=None, specialPath=None):
        imageURLs = self.getImageURLs(post.url)
        count = 1
        for imageURL in imageURLs:
            valid, response = self.validURLImage(imageURL)
            if valid:
                params = (user.name, post.id, imageURL, post.permalink, defaultPath, count, response, specialString, specialCount, specialPath)
                image = self.makeImage(*params)
                if image is not None:
                    count += 1
                    yield image


class VidbleImageFinder(ImageFinder):
    __slots__ = ('avoidDuplicates', 'alreadyDownloadedURLs')

    def __init__(self, alreadyDownloadedURLs, avoidDuplicates, queue):
        super().__init__(queue)
        self.avoidDuplicates = avoidDuplicates
        self.alreadyDownloadedURLs = alreadyDownloadedURLs

    def validURLImage(self, url):
        #Determine if the file is good to download.
        #Must not be an already-downloaded url
        #Status Code must be 200 (valid page)
        #Must have valid data response
        if self.avoidDuplicates and self.alreadyDownloadedURLs is not None and url in self.alreadyDownloadedURLs:
            return False, None
        response = self.exceptionSafeImageRequest(url, stream=True)
        if response is not None:
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
        elif '/show/' in URL or '/explore/' in URL:
            URL = URL[URL.rfind('/')]
            text = self.exceptionSafeTextRequest("http://www.vidble.com/" + endOfURL, stream=True)
            if text is not None:
                soup = BeautifulSoup(text)
                imgs = soup.find_all('img')
                if len(imgs) == 1:
                    validURLs.append("http://www.vidble.com/" + imgs[0]['src'])
        elif '/album/' in URL:
            text = self.exceptionSafeTextRequest(URL, stream=True)
            if text is not None:
                soup = BeautifulSoup(text)
                imgs = soup.find_all('img')
                for img in imgs:
                    imgClass = img.get('class')
                    if imgClass is not None and imgClass[0] == 'img2':
                        validURLs.append("http://www.vidble.com" + img['src'])
        return validURLs


    def getImages(self, post, defaultPath, user, specialString=None, specialCount=None, specialPath=None):
        URL = post.url
        imageURLs = self.getImageURLs(URL)
        count = 1
        for imageURL in imageURLs:
            valid, response = self.validURLImage(imageURL)
            if valid:
                params = (user.name, post.id, imageURL, post.permalink, defaultPath, count, response, specialString, specialCount, specialPath)
                image = self.makeImage(*params)
                if image is not None:
                    count += 1
                    yield image

