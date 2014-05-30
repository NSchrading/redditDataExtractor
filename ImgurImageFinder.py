from imageFinder import ImageFinder
import requests


class ImgurLinkTypeEnum():
    DIRECT = 1
    SINGLE_PAGE = 2
    ALBUM = 3


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

    def getImages(self, post, defaultPath):
        images = []
        self.imgurLinkType = self.getImgurLinkType(post.url)
        imageURLs = self.getImageURLs(post.url)
        count = 1
        for imageURL in imageURLs:
            response = requests.get(imageURL)
            params = (post.author.name, post.id, imageURL, post.permalink, defaultPath, count, response)
            image = self.makeImage(*params)
            if image is not None:
                images.append(image)
                count += 1
        return images