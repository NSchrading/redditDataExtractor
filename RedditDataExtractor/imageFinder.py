"""
    This file is part of the reddit Data Extractor.

    The reddit Data Extractor is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    The reddit Data Extractor is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with The reddit Data Extractor.  If not, see <http://www.gnu.org/licenses/>.
"""

import requests
import warnings

from bs4 import BeautifulSoup
from contextlib import closing
from .content import Image
from enum import Enum

# BeautifulSoup issues deprecation warnings. Hide them.
warnings.filterwarnings("ignore", category=DeprecationWarning)


class ImgurLinkTypeEnum(Enum):
    DIRECT = 1
    SINGLE_PAGE = 2
    ALBUM = 3
    GALLERY = 4


class ImageFinder():
    __slots__ = ('_requestsSession', '_queue')

    def __init__(self, queue):
        """
        A class to handle the finding of images / gifs / webms, either by supporting a specific site by subclassing this
        class or by using this class directly and going to direct links.

        :type queue: Queue.queue
        """
        # Set the user-agent to avoid user-agent sniffing
        # Use a session that all requests can use
        self._requestsSession = requests.session()
        self._requestsSession.headers[
            'User-Agent'] = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'
        self._requestsSession.verify = 'RedditDataExtractor/cacert.pem'
        self._queue = queue

    def _validURLImage(self, url):
        """
        Determine if the file is good to download.

        :type url: str
        :rtype: tuple
        """
        response = self.exceptionSafeImageRequest(url, stream=True)
        if response is not None:
            return True, response
        return False, None

    def _makeImage(self, userOrSubName, submissionID, URL, redditSubmissionURL, defaultPath, count, iterContent,
                   specialString=None, specialCount=None, specialPath=None):
        """
        :type userOrSubName: str
        :type submissionID: str
        :type URL: str
        :type redditSubmissionURL: str
        :type defaultPath: pathlib.Path
        :type count: int
        :type iterContent: generator
        :type specialString: str
        :type specialCount int
        :type specialPath str
        :rtype: RedditDataExtractor.content.Image
        """
        fileType = self.getFileType(URL)
        return Image(userOrSubName, submissionID, fileType, defaultPath, URL, redditSubmissionURL, iterContent,
                     str(count), specialString, specialCount, specialPath)

    def exceptionSafeJsonRequest(self, *args, **kwargs):
        try:
            with closing(self._requestsSession.get(*args, **kwargs)) as response:
                if response.status_code == 200 and 'json' in response.headers['Content-Type']:
                    return response.json()
                else:
                    return None
        except:
            self._queue.put(">>> Failed to query json for " + str(*args) + "\n")
        return None

    def exceptionSafeImageRequest(self, *args, **kwargs):
        try:
            response = self._requestsSession.get(*args, **kwargs)
            if response.status_code == 200 and 'image' in response.headers['Content-Type']:
                return response.iter_content(1024)
            else:
                return None
        except:
            self._queue.put(">>> Failed to connect to " + str(
                *args) + ".\n>>> To attempt to redownload this file, uncheck 'Restrict retrieved submissions to creation dates after the last downloaded submission' in the settings.\n")
        return None

    def exceptionSafeWebmRequest(self, *args, **kwargs):
        try:
            response = self._requestsSession.get(*args, **kwargs)
            if response.status_code == 200 and 'webm' in response.headers['Content-Type']:
                return response.iter_content(1024)
            else:
                return None
        except:
            self._queue.put(">>> Failed to connect to " + str(
                *args) + ".\n>>> To attempt to redownload this file, uncheck 'Restrict retrieved submissions to creation dates after the last downloaded submission' in the settings.\n")
        return None

    def exceptionSafeTextRequest(self, *args, **kwargs):
        try:
            with closing(self._requestsSession.get(*args, **kwargs)) as response:
                if response.status_code == 200 and 'text' in response.headers['Content-Type']:
                    return response.text
                else:
                    return None
        except:
            self._queue.put(">>> Failed to query text for " + str(*args) + "\n")
        return None

    @staticmethod
    def getFileType(URL):
        """
        Sometimes things will be added to the end of the file type from urls like www.blah.com/foo.jpg?w=1280&h=1024
        We don't want the ?whatever stuff, so just return plain file types
        :type URL: str
        :rtype: str
        """
        fileType = URL[URL.rfind("."):]
        fileType = fileType.lower()
        if '.jpg' in fileType or '.jpeg' in fileType:
            return '.jpg'
        elif '.png' in fileType:
            return '.png'
        elif '.webm' in fileType:
            return '.webm'
        elif '.gif' in fileType:
            return '.gif'
        else:
            return ".jpg"  # default to jpg and hope for the best

    def getImages(self, submission, defaultPath, userOrSub, specialString=None, specialCount=None, specialPath=None):
        """
        :type submission: praw.objects.Submission
        :type defaultPath: pathlib.Path
        :type userOrSub: RedditDataExtractor.GUI.genericListModelObjects.GenericListModelObj
        :type specialString: str
        :type specialCount int
        :type specialPath str
        :rtype: generator
        """
        valid, response = self._validURLImage(submission.url)
        if valid:
            params = (userOrSub.name, submission.id, submission.url, submission.permalink, defaultPath, 1, response,
                      specialString, specialCount, specialPath)
            yield self._makeImage(*params)


class ImgurImageFinder(ImageFinder):
    __slots__ = ('_CLIENT_ID', '_alreadyQueriedURLs', 'imgurLinkType', 'avoidDuplicates', 'alreadyDownloadedImgurURLs')

    def __init__(self, alreadyDownloadedImgurURLs, avoidDuplicates, queue, clientId):
        """
        A subclass of ImageFinder to guarantee correct images from Imgur links
        :type alreadyDownloadedImgurURLs: set
        :type avoidDuplicates: bool
        :type queue: Queue.queue
        """
        super().__init__(queue)
        self._CLIENT_ID = clientId  # imgur client ID for API access
        self._alreadyQueriedURLs = set([])
        self.imgurLinkType = None
        self.avoidDuplicates = avoidDuplicates
        self.alreadyDownloadedImgurURLs = alreadyDownloadedImgurURLs

    def _validURLImage(self, url):
        headers = {'Authorization': 'Client-ID ' + self._CLIENT_ID}
        apiURL = 'https://api.imgur.com/3/'
        if self.imgurLinkType is ImgurLinkTypeEnum.DIRECT or self.imgurLinkType is ImgurLinkTypeEnum.SINGLE_PAGE:
            imgurHashID = url[url.rfind('/') + 1:]
            dotIndex = imgurHashID.rfind('.')
            if dotIndex != -1:
                imgurHashID = imgurHashID[:imgurHashID.rfind('.')]
            apiURL += 'image/' + imgurHashID
        elif self.imgurLinkType is ImgurLinkTypeEnum.GALLERY:
            imgurHashID = url[url.rfind('/') + 1:]
            apiURL += 'gallery/' + imgurHashID
        else:
            imgurHashID = url[url.rfind('/') + 1:]
            apiURL += 'album/' + imgurHashID
        if apiURL in self._alreadyQueriedURLs:  # Regardless of if we want to avoid duplicates, we always want to reduce API calls
            return False, None
        json = self.exceptionSafeJsonRequest(apiURL, headers=headers, stream=True)
        if json is not None:
            self._alreadyQueriedURLs.add(apiURL)
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

    def _getImageURLsDirect(self, json):
        """
        Appends to the valid imageURLs list if the json data is valid
        :type json: dict
        :rtype: generator
        """
        data = json.get('data')
        if data is not None:
            link = data.get('link')
            if link is not None and (not self.avoidDuplicates or (
                    self.alreadyDownloadedImgurURLs is not None and link not in self.alreadyDownloadedImgurURLs)):
                yield link

    def _getImageURLsPage(self, json):
        """
        Appends to the valid imageURLs list if the json data is valid
        :type json: dict
        :rtype: generator
        """
        image = json.get('image')
        url = None
        if image is not None:
            links = image.get('links')
            if links is not None:
                original = links.get('original')
                if original is not None and (not self.avoidDuplicates or (
                        self.alreadyDownloadedImgurURLs is not None and original not in self.alreadyDownloadedImgurURLs)):
                    url = original
                    yield url
        if url is None:  # if the above method doesn't work, try direct
            for url in self._getImageURLsDirect(json):
                yield url

    def _getImageURLsAlbum(self, json):
        """
        Appends to the valid imageURLs list if the json data is valid
        :type json: dict
        :rtype: generator
        """
        data = json.get('data')
        if data is not None:
            images = data.get('images')
            if images is not None:
                for image in images:
                    link = image.get('link')
                    if link is not None and (not self.avoidDuplicates or (
                            self.alreadyDownloadedImgurURLs is not None and link not in self.alreadyDownloadedImgurURLs)):
                        yield link

    def _getImageURLs(self, url):
        """
        Gets valid image URLs given a submission's external URL (could be an album link, a gallery, a direct link, or a page)
        :type url: str
        :rtype: generator
        """
        valid, json = self._validURLImage(url)
        if valid:
            if self.imgurLinkType is ImgurLinkTypeEnum.DIRECT:
                imageURLs = self._getImageURLsDirect(json)
            elif self.imgurLinkType is ImgurLinkTypeEnum.SINGLE_PAGE:
                imageURLs = self._getImageURLsPage(json)
            else:  # album and gallery json response is the same
                imageURLs = self._getImageURLsAlbum(json)
            for imageURL in imageURLs:
                yield imageURL

    def _getImgurLinkType(self, url):
        """
        Based on the url, determine the type of the imgur link
        :type url: str
        """
        if "i.imgur.com" in url:
            return ImgurLinkTypeEnum.DIRECT
        elif "imgur.com/a/" in url:
            return ImgurLinkTypeEnum.ALBUM
        elif "imgur.com/gallery/" in url:
            return ImgurLinkTypeEnum.GALLERY
        else:
            return ImgurLinkTypeEnum.SINGLE_PAGE

    def getImages(self, submission, defaultPath, userOrSub, specialString=None, specialCount=None, specialPath=None):
        self.imgurLinkType = self._getImgurLinkType(submission.url)
        imageURLs = self._getImageURLs(submission.url)
        count = 1
        for imageURL in imageURLs:
            response = self.exceptionSafeImageRequest(imageURL, stream=True)
            if response is None:
                continue
            params = (
            userOrSub.name, submission.id, imageURL, submission.permalink, defaultPath, count, response, specialString,
            specialCount, specialPath)
            image = self._makeImage(*params)
            if image is not None:
                count += 1
                yield image


class GfycatImageFinder(ImageFinder):
    __slots__ = ('avoidDuplicates', 'alreadyDownloadedURLs')

    def __init__(self, alreadyDownloadedURLs, avoidDuplicates, queue):
        """
        A subclass of ImageFinder to guarantee correct images from Gfycat links
        :type alreadyDownloadedImgurURLs: set
        :type avoidDuplicates: bool
        :type queue: Queue.queue
        """
        super().__init__(queue)
        self.avoidDuplicates = avoidDuplicates
        self.alreadyDownloadedURLs = alreadyDownloadedURLs

    def _validURLImage(self, url):
        if self.avoidDuplicates and self.alreadyDownloadedURLs is not None and url in self.alreadyDownloadedURLs:
            return False, None
        response = self.exceptionSafeWebmRequest(url, stream=True)
        if response is not None:
            return True, response
        else:
            return False, None

    def _getImageURL(self, URL):
        """
        Get possible gfycat image URL from gfycat API call
        :type URL: str
        :rtype: str
        """
        endOfURL = URL[URL.rfind('/') + 1:]
        apiCall = "http://gfycat.com/cajax/get/" + endOfURL
        json = self.exceptionSafeJsonRequest(apiCall)
        validURL = None
        if json is not None:
            gfyItem = json.get("gfyItem")
            if gfyItem is not None and gfyItem.get("webmUrl") is not None:
                validURL = gfyItem.get("webmUrl")
        return validURL

    def getImages(self, submission, defaultPath, userOrSub, specialString=None, specialCount=None, specialPath=None):
        URL = submission.url
        imageURL = self._getImageURL(URL)
        count = 1
        valid, response = self._validURLImage(imageURL)
        if valid:
            params = (
            userOrSub.name, submission.id, imageURL, submission.permalink, defaultPath, count, response, specialString,
            specialCount, specialPath)
            image = self._makeImage(*params)
            if image is not None:
                yield image


class MinusImageFinder(ImageFinder):
    __slots__ = ('avoidDuplicates', 'alreadyDownloadedURLs')

    def __init__(self, alreadyDownloadedURLs, avoidDuplicates, queue):
        """
        A subclass of ImageFinder to guarantee correct images from Minus links
        :type alreadyDownloadedImgurURLs: set
        :type avoidDuplicates: bool
        :type queue: Queue.queue
        """
        super().__init__(queue)
        self.avoidDuplicates = avoidDuplicates
        self.alreadyDownloadedURLs = alreadyDownloadedURLs

    def _validURLImage(self, url):
        if self.avoidDuplicates and self.alreadyDownloadedURLs is not None and url in self.alreadyDownloadedURLs:
            return False, None
        response = self.exceptionSafeImageRequest(url, stream=True)
        if response is not None:
            return True, response
        else:
            return False, None

    def _getImageURLs(self, URL):
        """
        Attempt to get image urls from the Minus URL
        :type URL: str
        :rtype: generator
        """
        endOfURL = URL[URL.rfind('/') + 1:]
        if "." in endOfURL:
            fileType = self.getFileType(endOfURL)
            if len(fileType) > 1:
                yield ("http://i.minus.com/" + endOfURL)
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
                        pass  # galleries not currently supported. If I get minus api credentials I might be able to do it
                    elif 'photo' in content:
                        imageHTML = soup.find("a", "item-main is-image")
                        if imageHTML.get("href") is not None:
                            yield imageHTML.get("href")

    def getImages(self, submission, defaultPath, userOrSub, specialString=None, specialCount=None, specialPath=None):
        imageURLs = self._getImageURLs(submission.url)
        if imageURLs is not None:
            count = 1
            for imageURL in imageURLs:
                valid, response = self._validURLImage(imageURL)
                if valid:
                    params = (
                    userOrSub.name, submission.id, imageURL, submission.permalink, defaultPath, count, response,
                    specialString, specialCount, specialPath)
                    image = self._makeImage(*params)
                    if image is not None:
                        count += 1
                        yield image


class VidbleImageFinder(ImageFinder):
    __slots__ = ('avoidDuplicates', 'alreadyDownloadedURLs')

    def __init__(self, alreadyDownloadedURLs, avoidDuplicates, queue):
        """
        A subclass of ImageFinder to guarantee correct images from Vidble links
        :type alreadyDownloadedImgurURLs: set
        :type avoidDuplicates: bool
        :type queue: Queue.queue
        """
        super().__init__(queue)
        self.avoidDuplicates = avoidDuplicates
        self.alreadyDownloadedURLs = alreadyDownloadedURLs

    def _validURLImage(self, url):
        if self.avoidDuplicates and self.alreadyDownloadedURLs is not None and url in self.alreadyDownloadedURLs:
            return False, None
        response = self.exceptionSafeImageRequest(url, stream=True)
        if response is not None:
            return True, response
        else:
            return False, None

    def _getImageURLs(self, URL):
        """
        Attempt to get image urls from the Vidble URL.
        :type URL: str
        :rtype: generator
        """
        endOfURL = URL[URL.rfind('/') + 1:]
        if "." in endOfURL:
            fileType = self.getFileType(endOfURL)
            if len(fileType) > 1:
                yield ("http://www.vidble.com/" + endOfURL)
        elif '/show/' in URL or '/explore/' in URL:
            URL = URL[URL.rfind('/')]
            text = self.exceptionSafeTextRequest("http://www.vidble.com/" + endOfURL, stream=True)
            if text is not None:
                soup = BeautifulSoup(text)
                imgs = soup.find_all('img')
                if len(imgs) == 1:
                    yield ("http://www.vidble.com/" + imgs[0]['src'])
        elif '/album/' in URL:
            text = self.exceptionSafeTextRequest(URL, stream=True)
            if text is not None:
                soup = BeautifulSoup(text)
                imgs = soup.find_all('img')
                for img in imgs:
                    imgClass = img.get('class')
                    if imgClass is not None and imgClass[0] == 'img2':
                        imgLink = img.get('src')
                        if imgLink is not None:
                            yield ("http://www.vidble.com" + imgLink)


    def getImages(self, submission, defaultPath, userOrSub, specialString=None, specialCount=None, specialPath=None):
        URL = submission.url
        imageURLs = self._getImageURLs(URL)
        if imageURLs is not None:
            count = 1
            for imageURL in imageURLs:
                valid, response = self._validURLImage(imageURL)
                if valid:
                    params = (
                    userOrSub.name, submission.id, imageURL, submission.permalink, defaultPath, count, response,
                    specialString, specialCount, specialPath)
                    image = self._makeImage(*params)
                    if image is not None:
                        count += 1
                        yield image

