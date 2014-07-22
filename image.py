import os
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)


class Image():

    gifHeader = [hex(ord("G")), hex(ord("I")), hex(ord("F"))]

    __slots__ = (
        'user', 'postID', 'fileType', 'defaultPath', 'savePath', 'URL', 'redditPostURL', 'iterContent', 'numInSeq', 'specialString', 'specialCount', 'specialPath')

    def __init__(self, user, postID, fileType, defaultPath, URL, redditPostURL, iterContent, numInSeq="", specialString=None, specialCount=None, specialPath=None):
        self.user = user
        self.postID = postID
        self.fileType = fileType
        self.defaultPath = defaultPath
        self.URL = URL
        self.redditPostURL = redditPostURL
        self.iterContent = iterContent
        self.numInSeq = numInSeq
        self.savePath = ""
        self.specialString = specialString
        self.specialCount = specialCount
        self.specialPath = specialPath
        self.makeSavePath()

    def makeSavePath(self):
        if self.numInSeq != "":
            imageFile = self.postID + " " + str(self.numInSeq) + self.fileType
        else:
            imageFile = self.postID + self.fileType
        if self.specialString is not None and self.specialCount is not None:
            if self.numInSeq != "":
                imageFile = self.postID + self.specialString + str(self.specialCount) + " " + str(self.numInSeq) + self.fileType
            else:
                imageFile = self.postID + self.specialString + str(self.specialCount) + self.fileType
        if self.specialPath is not None:
            directory = os.path.abspath(os.path.join(self.defaultPath, self.user, self.specialPath))
            if not os.path.exists(directory):
                os.makedirs(directory)
            self.savePath = os.path.abspath(os.path.join(directory, imageFile))
        else:
            self.savePath = os.path.abspath(os.path.join(self.defaultPath, self.user, imageFile))

    def isActuallyGif(self):
        print("checking if gif")
        with open(self.savePath, 'rb') as f:
            for i in range(3):
                if hex(ord(f.read(1))) != Image.gifHeader[i]:
                    return False
            return True

    def download(self):
        try:
            with open(self.savePath, 'wb') as fo:
                for chunk in self.iterContent:
                    fo.write(chunk)
            filePath, fileExtension = os.path.splitext(self.savePath)
            if fileExtension in [".jpg", ".jpeg", ".png"]:
                if self.isActuallyGif():
                    print("its actually a gif")
                    newPath = filePath + ".gif"
                    os.rename(self.savePath, newPath)
                    self.savePath = newPath
                    self.fileType = ".gif"
            return True
        except Exception as e:
            print(type(e))
            print(e.args)
            print(e)
            return False
