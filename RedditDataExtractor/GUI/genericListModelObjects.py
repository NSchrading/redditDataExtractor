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

class GenericListModelObj():
    slots = ('name', '_blacklist', '_mostRecentDownloadTimestamp', 'redditSubmissions', 'externalDownloads')
    subSort = "Hot"

    def __init__(self, name):
        """
        A generic class that holds state for specific users / subreddits in the ListModels
        """
        self.name = name.lower()
        self._blacklist = set()
        self._mostRecentDownloadTimestamp = None
        self.redditSubmissions = {}
        self.externalDownloads = set()

    @property
    def mostRecentDownloadTimestamp(self):
        return self._mostRecentDownloadTimestamp

    @mostRecentDownloadTimestamp.setter
    def mostRecentDownloadTimestamp(self, utc):
        """
        Set the timestamp only if it isn't set or the passed in utc is newer
        :type utc: float
        """
        if utc is not None and (self._mostRecentDownloadTimestamp is None or utc > self._mostRecentDownloadTimestamp):
            self._mostRecentDownloadTimestamp = utc

    def submissionNotInBlacklist(self, submission):
        """
        :param submission: The Submission's permalink
        :type submission: str
        :rtype: bool
        """
        return submission not in self._blacklist

    def submissionBeforeLastDownload(self, submission):
        """
        Return True if we haven't recorded a download timestamp yet or if the created_utc indicates it is a newer submission
        :type submission: praw.objects.Submission
        :rtype: bool
        """
        return self._mostRecentDownloadTimestamp is None or submission.created_utc > self._mostRecentDownloadTimestamp

    def isNewContent(self, submission, downloadedContentType):
        """
        Make sure we haven't downloaded this content yet. Not just based on permalink - it also has to be the same
        downloadedContentType as previously downloaded content to return False

        :type submission: praw.objects.Submission
        :type downloadedContentType: RedditDataExtractor.downloader.DownloadedContentType
        :rtype: bool
        """
        redditURL = submission.permalink
        allRedditSubmissionsOfLstModelObj = self.redditSubmissions
        downloadedContentOfSubmission = allRedditSubmissionsOfLstModelObj.get(redditURL)
        if len(allRedditSubmissionsOfLstModelObj) <= 0 or downloadedContentOfSubmission is None:
            return True
        return not any([downloadedContent.type is downloadedContentType for downloadedContent in downloadedContentOfSubmission])

class User(GenericListModelObj):

    def __init__(self, name):
        """
        A user in a user list
        """
        super().__init__(name)

class Subreddit(GenericListModelObj):

    def __init__(self, name):
        """
        A subreddit in a subreddit list
        """
        super().__init__(name)

    @GenericListModelObj.mostRecentDownloadTimestamp.setter
    def mostRecentDownloadTimestamp(self, utc):
        """
        Override of parent class method - additionally check that the subreddit sorting type is "new". If it isn't, then
        we don't set the timestamp because submissions can be out of order in relation to their created_utc with the other
        sorting methods.
        :type utc: float
        """
        if GenericListModelObj.subSort == "new" and self._mostRecentDownloadTimestamp is None:
            self._mostRecentDownloadTimestamp = utc
        elif GenericListModelObj.subSort == "new" and utc > self._mostRecentDownloadTimestamp:
            self._mostRecentDownloadTimestamp = utc

    def submissionBeforeLastDownload(self, submission):
        """
        Override of parent class method - Additionally check that the subreddit sorting type is "new"
        :rtype: bool
        """
        return GenericListModelObj.subSort != "new" or (self._mostRecentDownloadTimestamp is None or submission.created_utc > self._mostRecentDownloadTimestamp)