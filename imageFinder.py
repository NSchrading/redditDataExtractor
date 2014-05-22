import requests
import re

class ImageFinder():
    __slots__ = ('URL', 'htmlSource', 'imageURLRegex', 'nullToNoneRegex')

    def __init__(self, URL):
        self.URL = URL
        self.htmlSource = self.getHTMLSource()
        self.imageURLRegex = re.compile('images.*:.*{"count":.*}')
        self.nullToNoneRegex = re.compile("null")

    def getHTMLSource(self):
        response = requests.get(self.URL, stream=True)
        response.close()
        HTMLSource = None
        if response.status_code == 200:
            HTMLSource =  response.text
        response.close()
        return HTMLSource

    def validURLImage(self, url):
        ''' Determine if the file is good to download.
        Status Code must be 200 (valid page)
        '''
        response = requests.get(url, stream=True)
        response.close()
        if response.status_code == 200:
            return True, response
        return False, response

    def getImages(self, post, defaultPath):
        return []
