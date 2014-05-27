import os
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)


class Image():
    __slots__ = (
        'user', 'postID', 'fileType', 'defaultPath', 'savePath', 'URL', 'redditPostURL', 'iterContent', 'numInSeq')

    def __init__(self, user, postID, fileType, defaultPath, URL, redditPostURL, iterContent, numInSeq=""):
        self.user = user
        self.postID = postID
        self.fileType = fileType
        self.defaultPath = defaultPath
        self.URL = URL
        self.redditPostURL = redditPostURL
        self.iterContent = iterContent
        self.numInSeq = numInSeq
        self.savePath = ""
        self.makeSavePath()

    def makeSavePath(self):
        if self.numInSeq != "":
            imageFile = self.postID + " " + str(self.numInSeq) + self.fileType
        else:
            imageFile = self.postID + self.fileType
        self.savePath = os.path.abspath(os.path.join(self.defaultPath, self.user, imageFile))

    def download(self, user, avoidDuplicates):
        if (not avoidDuplicates) or (avoidDuplicates and self.URL not in user.imgurPosts):
            if user.redditPosts.get(self.redditPostURL) is None:  # Add 1 representative picture for this post, even if it is an album with multiple pictures
                user.redditPosts[self.redditPostURL] = self.savePath
            user.imgurPosts.add(self.URL)
            print('Saving %s...' % self.savePath)
            with open(self.savePath, 'wb') as fo:
                for chunk in self.iterContent:
                    fo.write(chunk)
            return True
        return False

        '''
        DIRECT
        if self.downloadImage(post.url, savePath):
            if check503BytesFile(savePath):
                addToUserSpecificBlacklist(postID, user, defaultPath)
            self.addPostToUserDownloads(post)

        SINGLE
        savePath = os.path.abspath(os.path.join(defaultPath, user, imageFile))
        if downloadImage("http:" + imageUrl, savePath):
            if check503BytesFile(savePath):
                addToUserSpecificBlacklist(postID, user, defaultPath)

        ALBUM
        savePath = os.path.abspath(os.path.join(self.defaultPath, user, postID + " " + str(count) + fileType))
        if self.downloadImage(url[0], savePath):
            check503BytesFile(savePath)
            count += 1
            self.addPostToUserDownloads(post)
        '''