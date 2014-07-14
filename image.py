import os
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)


class Image():
    __slots__ = (
        'user', 'postID', 'fileType', 'defaultPath', 'savePath', 'URL', 'redditPostURL', 'iterContent', 'numInSeq', 'commentAuthor', 'commentAuthorURLCount')

    def __init__(self, user, postID, fileType, defaultPath, URL, redditPostURL, iterContent, numInSeq="", commentAuthor=None, commentAuthorURLCount=None):
        self.user = user
        self.postID = postID
        self.fileType = fileType
        self.defaultPath = defaultPath
        self.URL = URL
        self.redditPostURL = redditPostURL
        self.iterContent = iterContent
        self.numInSeq = numInSeq
        self.savePath = ""
        self.commentAuthor = commentAuthor
        self.commentAuthorURLCount = commentAuthorURLCount
        self.makeSavePath()

    def makeSavePath(self):
        if self.numInSeq != "":
            imageFile = self.postID + " " + str(self.numInSeq) + self.fileType
        else:
            imageFile = self.postID + self.fileType
        if self.commentAuthor is not None and self.commentAuthorURLCount is not None:
            if self.numInSeq != "":
                imageFile = self.postID + "_comment_" + str(self.commentAuthorURLCount) + " " + str(self.numInSeq) + self.fileType
            else:
                imageFile = self.postID + "_comment_" + str(self.commentAuthorURLCount) + self.fileType
            directory = os.path.abspath(os.path.join(self.defaultPath, self.user, self.commentAuthor))
            if not os.path.exists(directory):
                os.makedirs(directory)
            self.savePath = os.path.abspath(os.path.join(self.defaultPath, self.user, self.commentAuthor, imageFile))
        else:
            self.savePath = os.path.abspath(os.path.join(self.defaultPath, self.user, imageFile))

    def download(self):
        with open(self.savePath, 'wb') as fo:
            for chunk in self.iterContent:
                fo.write(chunk)