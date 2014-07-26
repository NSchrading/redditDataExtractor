class GenericListModelObj():
    slots = ('name', 'redditSubmissions', 'externalDownloads' 'blacklist')
    subSort = "Hot"

    def __init__(self, name):
        self.name = name.lower()
        self.redditSubmissions = {}
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

    def submissionNotInBlacklist(self, submission):
        return submission not in self.blacklist

    def submissionBeforeLastDownload(self, submission):
        return self._mostRecentDownloadTimestamp is None or submission.created_utc > self._mostRecentDownloadTimestamp

    def isNewContent(self, submission, downloadedContentType):
        redditURL = submission.permalink
        allRedditSubmissionsOfLstModelObj = self.redditSubmissions
        downloadedContentOfSubmission = allRedditSubmissionsOfLstModelObj.get(redditURL)
        if len(allRedditSubmissionsOfLstModelObj) <= 0 or downloadedContentOfSubmission is None:
            return True
        return not any([downloadedContent.type == downloadedContentType for downloadedContent in downloadedContentOfSubmission])

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

    def submissionBeforeLastDownload(self, submission):
        return GenericListModelObj.subSort != "new" or (self._mostRecentDownloadTimestamp is None or submission.created_utc > self._mostRecentDownloadTimestamp)