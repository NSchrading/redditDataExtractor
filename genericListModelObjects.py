class GenericListModelObj():
    slots = ('name', 'redditPosts', 'externalDownloads' 'blacklist')
    subSort = "Hot"

    def __init__(self, name):
        self.name = name.lower()
        self.redditPosts = {}
        self.externalDownloads = set()
        self.blacklist = set()
        self._mostRecentDownloadTimestamp = None

    @property
    def mostRecentDownloadTimestamp(self):
        return self._mostRecentDownloadTimestamp

    @mostRecentDownloadTimestamp.setter
    def mostRecentDownloadTimestamp(self, utc):
        """

        :param utc:
        """
        if utc is not None and (self._mostRecentDownloadTimestamp is None or utc > self._mostRecentDownloadTimestamp):
            self._mostRecentDownloadTimestamp = utc

    def isNotInBlacklist(self, redditPost):
        return redditPost not in self.blacklist

    def postBeforeLastDownload(self, post):
        return self._mostRecentDownloadTimestamp is None or post.created_utc > self._mostRecentDownloadTimestamp

class User(GenericListModelObj):

    def __init__(self, name):
        super().__init__(name)

class Subreddit(GenericListModelObj):

    def __init__(self, name):
        super().__init__(name)

    @GenericListModelObj.mostRecentDownloadTimestamp.setter
    def mostRecentDownloadTimestamp(self, utc):
        """

        :param utc:
        """
        if GenericListModelObj.subSort == "new" and self._mostRecentDownloadTimestamp is None:
            self._mostRecentDownloadTimestamp = utc
        elif GenericListModelObj.subSort == "new" and utc > self._mostRecentDownloadTimestamp:
            self._mostRecentDownloadTimestamp = utc

    def postBeforeLastDownload(self, post):
        return GenericListModelObj.subSort != "new" or (self._mostRecentDownloadTimestamp is None or post.created_utc > self._mostRecentDownloadTimestamp)