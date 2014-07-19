class GenericListModelObj():
    slots = ('name', 'redditPosts', 'externalDownloads' 'blacklist')
    subSort = "Hot"

    def __init__(self, name):
        self.name = name.lower()
        self.redditPosts = {}
        self.externalDownloads = {}
        self.blacklist = set([])
        self._mostRecentDownloadTimestamp = None

    @property
    def mostRecentDownloadTimestamp(self):
        return self._mostRecentDownloadTimestamp

    @mostRecentDownloadTimestamp.setter
    def mostRecentDownloadTimestamp(self, utc):
        """

        :param utc:
        """
        print("timestamp before: " + str(self._mostRecentDownloadTimestamp))
        if self._mostRecentDownloadTimestamp is None:
            self._mostRecentDownloadTimestamp = utc
        elif utc > self._mostRecentDownloadTimestamp:
            self._mostRecentDownloadTimestamp = utc
        print("timestamp after: " + str(self._mostRecentDownloadTimestamp))

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
        print("timestamp before: " + str(self._mostRecentDownloadTimestamp))
        if GenericListModelObj.subSort == "new" and self._mostRecentDownloadTimestamp is None:
            self._mostRecentDownloadTimestamp = utc
        elif GenericListModelObj.subSort == "new" and utc > self._mostRecentDownloadTimestamp:
            self._mostRecentDownloadTimestamp = utc
        print("timestamp after: " + str(self._mostRecentDownloadTimestamp))

    def postBeforeLastDownload(self, post):
        return GenericListModelObj.subSort != "new" or (self._mostRecentDownloadTimestamp is None or post.created_utc > self._mostRecentDownloadTimestamp)