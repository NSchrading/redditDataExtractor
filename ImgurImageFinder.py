from imageFinder import ImageFinder
from image import Image
from bs4 import BeautifulSoup
import ast
import re

class ImgurLinkTypeEnum():
    DIRECT = 1
    SINGLE_PAGE = 2
    ALBUM = 3

class ImgurImageFinder(ImageFinder):
    __slots__ = ('imgurLinkType')

    def __init__(self, URL):
        super().__init__(URL)

        self.imgurLinkType = self.getImgurLinkType()

    def validURLImage(self, url):
        ''' Determine if the file is good to download.
        Status Code must be 200 (valid page)
        /removed. can't be in the URL, as imgur sometimes redirects to imgur.com/removed.jpg if the file is removed
        content-length in the header, if it exists, cannot be 503 bytes (This is the size of the removed image warning if not redirected)
        '''
        isValid, response = super().validURLImage(url)
        if (not "/removed." in response.url) and (not response.headers.get('content-length') == '503'):
            return True, response
        return False, response

    def getImgurLinkType(self):
        if "i.imgur.com" in self.URL:
            return ImgurLinkTypeEnum.DIRECT
        elif "imgur.com/a/" in self.URL:
            return ImgurLinkTypeEnum.ALBUM
        else:
            return ImgurLinkTypeEnum.SINGLE_PAGE

    def getFileType(self, URL):
        fileType = URL[URL.rfind("."):]
        return self.getValidFileType(fileType)

    def getValidFileType(self, fileType):
        fileType = re.sub("\?", "", fileType) # get rid of question marks that may appear
        fileType = re.sub("\d", "", fileType) # get rid of numbers that may appear
        return fileType

    def makeDirectLinkedImage(self, user, postID, URL, defaultPath):
        fileType = self.getFileType(URL)
        isValid, response = self.validURLImage(URL)
        if isValid:
            image = Image(user, postID, fileType, defaultPath, URL, response.iter_content(4096))
            return image
        return None

    def searchSingleImagePageWithRegex(self):
        imageJPG = re.findall("http://i\.imgur\.com/[a-zA-Z0-9]+\.jpg", self.htmlSource)
        imageJPEG = re.findall("http://i\.imgur\.com/[a-zA-Z0-9]+\.jpeg", self.htmlSource)
        imageGIF = re.findall("http://i\.imgur\.com/[a-zA-Z0-9]+\.gif", self.htmlSource)
        imagePNG = re.findall("http://i\.imgur\.com/[a-zA-Z0-9]+\.png", self.htmlSource)
        imageAPNG = re.findall("http://i\.imgur\.com/[a-zA-Z0-9]+\.apng", self.htmlSource)
        if len(imageJPG) > 0:
            return imageJPG[0]
        elif len(imageJPEG) > 0:
            return imageJPG[0]
        elif len(imageGIF) > 0:
            return imageGIF[0]
        elif len(imagePNG) > 0:
            return imagePNG[0]
        elif len(imageAPNG) > 0:
            return imageAPNG[0]
        else:
            return None

    def makeSinglePageLinkedImage(self, user, postID, URL, defaultPath):
        if self.htmlSource is None:
            return None
        soup = BeautifulSoup(self.htmlSource)
        try:
            imageUrl = soup.select('.image a')[0]['href']
            imageUrl = "http:" + imageUrl
        except IndexError:
            imageUrl = self.searchSingleImagePageWithRegex()
            if imageUrl is None:
                return
        standardParams = (user, postID, imageUrl, defaultPath)
        return self.makeDirectLinkedImage(*standardParams)

    def getAlbumImageURLsAndFileTypes(self):
        albumImageURLs = []
        if self.htmlSource is None:
            return []
        match = self.imageURLRegex.search(self.htmlSource)
        if match is not None:
            match = match.group(0)
            match = match[match.find("{"):]     
            match = self.nullToNoneRegex.sub("None", match)
            imageData = ast.literal_eval(match)
            if imageData.get('count') > 0:
                images = imageData.get('items')
                if imageData.get('count') == len(images):
                    for image in images:
                        fileType = image.get('ext')
                        fileType = self.getValidFileType(fileType)
                        albumImageURLs.append(('http://i.imgur.com/' + image.get('hash') + fileType, fileType))
        return albumImageURLs

    def makeAlbumImages(self, user, postID, URL, defaultPath):
        images = []
        dataLst = self.getAlbumImageURLsAndFileTypes()
        count = 1
        for data in dataLst:
            fileType = data[1] # data is a tuple, the second item is the file type
            isValid, response = self.validURLImage(data[0]) # data[0] is the url
            if isValid:
                image = Image(user, postID, fileType, defaultPath, data[0], response.iter_content(4096), str(count))
                images.append(image)
                count += 1
        return images

    def getImages(self, post, defaultPath):
        images = []
        standardParams = (post.author.name, post.id, post.url, defaultPath)
        if self.imgurLinkType == ImgurLinkTypeEnum.DIRECT:
            images.append(self.makeDirectLinkedImage(*standardParams))
        elif self.imgurLinkType == ImgurLinkTypeEnum.SINGLE_PAGE:
            images.append(self.makeSinglePageLinkedImage(*standardParams))
        elif self.imgurLinkType == ImgurLinkTypeEnum.ALBUM:
            images.extend(self.makeAlbumImages(*standardParams))
        return images