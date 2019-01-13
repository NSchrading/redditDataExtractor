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

import pathlib
import time
from PyQt4.Qt import QObject, QThreadPool, pyqtSlot, pyqtSignal, QRunnable
from enum import Enum

from .redditDataExtractor import ListType


class DownloadedContentType(Enum):
    EXTERNAL_SUBMISSION_DATA = 1
    EXTERNAL_COMMENT_DATA = 2
    EXTERNAL_SELFTEXT_DATA = 3
    JSON_DATA = 4


class DownloadedContent():
    """
    A class to hold information about the content downloaded from a Reddit Submission.
    Can be 1 of 4 types in the DownloadedContentType enum. Reddit submissions can have
    all 4 types of content downloaded from them as long as they have those types
    available.
    """

    # There could be hundreds / thousands of objects - using __slots__ might save a bit of memory
    __slots__ = ('redditURL', 'type', 'representativeImage', 'files', 'externalDownloadURLs')

    def __init__(self, redditURL, type):
        """
        :param redditURL: The permalink of the reddit submission
        :param type: the type of the content of this download (JSON data, comment external, selftext external or submission external)
        :type redditURL: str
        :type type: DownloadedContentType
        """
        self.redditURL = redditURL
        self.type = type
        self.files = set()
        self.externalDownloadURLs = set()
        self.representativeImage = None

    def deleteFiles(self):
        if self.type is DownloadedContentType.EXTERNAL_COMMENT_DATA:
            # Comments appear in a folder for the user making the comment.
            # Always remove the submissions's files (that's the point of the function) but,
            # comments from the same user can come from different submissions so only remove the folder if the folder
            # becomes empty after deleting the files.
            commentFolders = {file.parent for file in self.files if file.exists}
            [file.unlink() for file in self.files if file.exists()]
            [commentFolder.rmdir() for commentFolder in commentFolders if len(list(commentFolder.glob('*'))) <= 0]
        else:
            # Other types just have the files, so remove them
            [file.unlink() for file in self.files if file.exists()]
        self.files.clear()


class Downloader(QObject):
    finished = pyqtSignal()

    def __init__(self, rddtDataExtractor, validUsersOrSubs, queue, listModelType):
        """
        The object that handles coordinating the download of the submission content. Spawns threads to download
        from users / subreddits simultaneously and to download images simultaneously.
        :type rddtDataExtractor: RedditDataExtractor.redditDataExtractor.RedditDataExtractor
        :type validUsersOrSubs: list
        :type queue: Queue.queue
        :type listModelType: RedditDataExtractor.redditDataExtractor.ListType
        """
        QObject.__init__(self)
        self._rddtDataExtractor = rddtDataExtractor
        self._validUsersOrSubs = validUsersOrSubs
        self._queue = queue
        self._listModelType = listModelType
        self._dataPool = QThreadPool()
        self._dataPool.setMaxThreadCount(4)
        self._continueOperation = True
        self.finishSignalForTest = False

    def stop(self):
        self._continueOperation = False

    def isStopped(self):
        return not self._continueOperation

    @pyqtSlot()
    def run(self):
        self.finishSignalForTest = False
        self._rddtDataExtractor.currentlyDownloading = True
        if len(self._validUsersOrSubs) > 0:
            for lstModelObj, validatedPRAWUserOrSub in self._validUsersOrSubs:
                worker = Worker(self._rddtDataExtractor, lstModelObj, validatedPRAWUserOrSub, self._queue,
                                self._listModelType, self.isStopped)
                self._dataPool.start(worker)
            self._dataPool.waitForDone()
        self.finished.emit()
        self.finishSignalForTest = True


class Worker(QRunnable):
    def __init__(self, rddtDataExtractor, lstModelObj, validatedPRAWUserOrSub, queue, lstModelType, isStopped):
        """
        Thread to download for a submission. Spawns more threads for downloading images or submission json data
        :param lstModelObj: The User or Subreddit "ListModel" Object
        :type rddtDataExtractor: RedditDataExtractor.redditDataExtractor.RedditDataExtractor
        :type lstModelObj: RedditDataExtractor.GUI.genericListModelObjects.GenericListModelObj
        :type validatedPRAWUserOrSub: praw.objects.Subreddit or praw.objects.User
        :type queue: Queue.queue
        :type lstModelType: RedditDataExtractor.redditDataExtractor.ListType
        :type isStopped: function
        """
        QRunnable.__init__(self)

        self._rddtDataExtractor = rddtDataExtractor
        self._lstModelObj = lstModelObj
        self._validatedPRAWUserOrSub = validatedPRAWUserOrSub
        self._queue = queue
        self._lstModelType = lstModelType
        self._imagePool = QThreadPool()
        self._imagePool.setMaxThreadCount(3)
        self._submissionPool = QThreadPool()
        self._submissionPool.setMaxThreadCount(3)
        self._videoPool = QThreadPool()
        self._videoPool.setMaxThreadCount(2)
        self._mostRecentDownloadTimestamp = None
        self._downloaderIsStopped = isStopped

    def _startDownloadsForSubmission(self, submission):
        """
        :type submission: praw.objects.Submission
        """
        if self._rddtDataExtractor.getExternalContent and self._lstModelObj.isNewContent(submission,
                                                                                         DownloadedContentType.EXTERNAL_SUBMISSION_DATA) and not submission.is_self and not "reddit" in submission.domain:
            downloadedContent = DownloadedContent(submission.permalink, DownloadedContentType.EXTERNAL_SUBMISSION_DATA)
            images = self._rddtDataExtractor.getImages(submission, self._lstModelObj, self._queue)
            self._startDownloadImages(images, downloadedContent, submission)
            if not self._rddtDataExtractor.avoidVideos:
                videos = self._rddtDataExtractor.getVideos(submission, self._lstModelObj)
                self._startDownloadVideos(videos, downloadedContent, submission)
        if self._rddtDataExtractor.getCommentExternalContent and self._lstModelObj.isNewContent(submission,
                                                                                                DownloadedContentType.EXTERNAL_COMMENT_DATA):
            downloadedContent = DownloadedContent(submission.permalink, DownloadedContentType.EXTERNAL_COMMENT_DATA)
            images = self._rddtDataExtractor.getCommentImages(submission, self._lstModelObj, self._queue)
            self._startDownloadImages(images, downloadedContent, submission)
            if not self._rddtDataExtractor.avoidVideos:
                videos = self._rddtDataExtractor.getCommentVideos(submission, self._lstModelObj)
                self._startDownloadVideos(videos, downloadedContent, submission)
        if self._rddtDataExtractor.getSelftextExternalContent and self._lstModelObj.isNewContent(submission,
                                                                                                 DownloadedContentType.EXTERNAL_SELFTEXT_DATA):
            downloadedContent = DownloadedContent(submission.permalink, DownloadedContentType.EXTERNAL_SELFTEXT_DATA)
            images = self._rddtDataExtractor.getSelftextImages(submission, self._lstModelObj, self._queue)
            self._startDownloadImages(images, downloadedContent, submission)
            if not self._rddtDataExtractor.avoidVideos:
                videos = self._rddtDataExtractor.getSelftextVideos(submission, self._lstModelObj)
                self._startDownloadVideos(videos, downloadedContent, submission)
        if self._rddtDataExtractor.getSubmissionContent and self._lstModelObj.isNewContent(submission,
                                                                                           DownloadedContentType.JSON_DATA):
            if not self._downloaderIsStopped():
                downloadedContent = DownloadedContent(submission.permalink, DownloadedContentType.JSON_DATA)
                submissionWorker = SubmissionWorker(self._rddtDataExtractor, self._lstModelObj, submission, self._queue,
                                                    downloadedContent, self._lstModelType,
                                                    self.setMostRecentDownloadTimestamp, self._downloaderIsStopped)
                self._submissionPool.start(submissionWorker)

    def _startDownloadImages(self, images, downloadedContent, submission):
        """
        :type: images: generator
        :type downloadedContent: DownloadedContent
        :type: submission: praw.objects.Submission
        """
        if images is not None:
            for image in images:
                if self._downloaderIsStopped():
                    break
                elif image is not None:
                    imageWorker = ImageWorker(image, self._lstModelObj, submission, self._queue, downloadedContent,
                                              self._rddtDataExtractor.avoidDuplicates,
                                              self.setMostRecentDownloadTimestamp, self._downloaderIsStopped)
                    self._imagePool.start(imageWorker)

    def _startDownloadVideos(self, videos, downloadedContent, submission):
        """
        :type: videos: generator
        :type downloadedContent: DownloadedContent
        """
        for video in videos:
            if self._downloaderIsStopped():
                break
            elif video is not None:
                videoWorker = VideoWorker(video, self._lstModelObj, submission, self._queue, downloadedContent,
                                          self._rddtDataExtractor.avoidDuplicates, self.setMostRecentDownloadTimestamp,
                                          self._downloaderIsStopped)
                self._videoPool.start(videoWorker)

    def run(self):
        if not self._downloaderIsStopped():
            name = self._lstModelObj.name
            self._queue.put("Starting download for " + name + "\n")
            self._rddtDataExtractor.makeDirectory(name)
            if self._lstModelType is ListType.SUBREDDIT:
                submitted = self._rddtDataExtractor.getSubredditSubmissions(self._validatedPRAWUserOrSub)
            else:
                submitted = self._validatedPRAWUserOrSub.get_submitted(limit=None)
            submissions = self._rddtDataExtractor.getValidSubmissions(submitted, self._lstModelObj)
            for submission, passesFilter in submissions:
                if passesFilter:
                    self._startDownloadsForSubmission(submission)
            self._imagePool.waitForDone()
            self._submissionPool.waitForDone()
            self._videoPool.waitForDone()
            self._lstModelObj.mostRecentDownloadTimestamp = self._mostRecentDownloadTimestamp
            self._queue.put("Finished download for " + name + "\n")

    def setMostRecentDownloadTimestamp(self, utc):
        """
        As the various threads download submissions, this keeps track of the most recent (by creation date) one.
        Then, when ALL downloads are finished, it sets the lstModelObj's mostRecentDownloadTimestamp. This
        allows submissions to be downloaded out of order in a download session, and still be able to prevent
        downloads from older time periods unless the user specifies they don't want that behavior.

        :type utc: float
        """
        if self._mostRecentDownloadTimestamp is None or utc > self._mostRecentDownloadTimestamp:
            self._mostRecentDownloadTimestamp = utc


class SubmissionWorker(QRunnable):
    def __init__(self, rddtDataExtractor, lstModelObj, submission, queue, downloadedContent, lstModelType,
                 setMostRecentDownloadTimestamp, downloaderIsStopped):
        """
        Thread to download JSON content of a submission.
        :param lstModelObj: The User or Subreddit "ListModel" Object
        :type rddtDataExtractor: RedditDataExtractor.redditDataExtractor.RedditDataExtractor
        :type lstModelObj: RedditDataExtractor.GUI.genericListModelObjects.GenericListModelObj
        :type submission: praw.objects.Submission
        :type queue: Queue.queue
        :type downloadedContent: DownloadedContent
        :type lstModelType: RedditDataExtractor.redditDataExtractor.ListType
        :type setMostRecentDownloadTimestamp: Worker.setMostRecentDownloadTimestamp
        :type downloaderIsStopped: function
        """
        QRunnable.__init__(self)

        self._rddtDataExtractor = rddtDataExtractor
        self._lstModelObj = lstModelObj
        self._submission = submission
        self._queue = queue
        self._downloadedContent = downloadedContent
        self._lstModelType = lstModelType
        self._setMostRecentDownloadTimestamp = setMostRecentDownloadTimestamp
        self._downloadedContent.representativeImage = pathlib.Path("RedditDataExtractor/images/jsonImage.png")
        self._downloaderIsStopped = downloaderIsStopped

    def run(self):
        if not self._downloaderIsStopped():
            title = self._submission.title
            if self._lstModelType is ListType.USER:
                success, savePath = self._rddtDataExtractor.downloadSubmission(self._submission, self._lstModelObj.name)
            else:
                success, savePath = self._rddtDataExtractor.downloadSubmission(self._submission)
            if success:
                self._downloadedContent.files.add(savePath)
                downloadedContentOfSubmission = self._lstModelObj.redditSubmissions.get(
                    self._downloadedContent.redditURL)
                if downloadedContentOfSubmission is None:
                    self._lstModelObj.redditSubmissions[self._downloadedContent.redditURL] = [self._downloadedContent]
                elif downloadedContentOfSubmission is not None and self._downloadedContent not in downloadedContentOfSubmission:
                    self._lstModelObj.redditSubmissions[self._downloadedContent.redditURL].append(
                        self._downloadedContent)
                self._setMostRecentDownloadTimestamp(self._submission.created_utc)
                self._queue.put("Saved submission: " + title + "\n")
            else:
                self._queue.put(
                    ">>> Error saving submission: " + title + '.\n>>> To attempt to redownload this file, uncheck "Restrict retrieved submissions to creation dates after the last downloaded submission" in the settings.\n')


class ImageWorker(QRunnable):
    def __init__(self, image, lstModelObj, submission, queue, downloadedContent, avoidDuplicates,
                 setMostRecentDownloadTimestamp, downloaderIsStopped):
        """
        Thread to download images / gifs / webms of a submission.
        :param lstModelObj: The User or Subreddit "ListModel" Object
        :type image: RedditDataExtractor.content.Image
        :type lstModelObj: RedditDataExtractor.GUI.genericListModelObjects.GenericListModelObj
        :type submission: praw.objects.Submission
        :type queue: Queue.queue
        :type downloadedContent: DownloadedContent
        :type avoidDuplicates: bool
        :type setMostRecentDownloadTimestamp: Worker.setMostRecentDownloadTimestamp
        :type downloaderIsStopped: function
        """
        QRunnable.__init__(self)

        self._image = image
        self._lstModelObj = lstModelObj
        self._submission = submission
        self._queue = queue
        self._downloadedContent = downloadedContent
        self._avoidDuplicates = avoidDuplicates
        self._setMostRecentDownloadTimestamp = setMostRecentDownloadTimestamp
        self._downloaderIsStopped = downloaderIsStopped

    def run(self):
        if (not self._downloaderIsStopped()) and ((not self._avoidDuplicates) or (
            self._avoidDuplicates and self._image.URL not in self._lstModelObj.externalDownloads)):
            self._lstModelObj.externalDownloads.add(
                self._image.URL)  # predict that the download will be successful - helps reduce duplicates when threads are running at similar times and download is for the same image
            if self._image.download():
                self._setMostRecentDownloadTimestamp(self._submission.created_utc)
                downloadedContentOfSubmission = self._lstModelObj.redditSubmissions.get(
                    self._downloadedContent.redditURL)
                if downloadedContentOfSubmission is None:
                    self._lstModelObj.redditSubmissions[self._downloadedContent.redditURL] = [self._downloadedContent]
                elif downloadedContentOfSubmission is not None and self._downloadedContent not in downloadedContentOfSubmission:
                    self._lstModelObj.redditSubmissions[self._downloadedContent.redditURL].append(
                        self._downloadedContent)
                if self._downloadedContent.representativeImage is None:
                    self._downloadedContent.representativeImage = self._image.savePath
                self._downloadedContent.files.add(self._image.savePath)
                self._downloadedContent.externalDownloadURLs.add(self._image.URL)
                self._queue.put('Saved %s' % self._image.savePath + "\n")
            else:
                if self._image.URL in self._lstModelObj.externalDownloads:
                    self._lstModelObj.externalDownloads.remove(self._image.URL)
                self._queue.put(
                    '>>> Error saving ' + str(
                        self._image.savePath) + '.\n>>> To attempt to redownload this file, uncheck "Restrict retrieved submissions to creation dates after the last downloaded submission" in the settings.\n')


class VideoWorker(QRunnable):
    def __init__(self, video, lstModelObj, submission, queue, downloadedContent, avoidDuplicates,
                 setMostRecentDownloadTimestamp, downloaderIsStopped):
        """
        Thread to download videos of a submission.
        :param lstModelObj: The User or Subreddit "ListModel" Object
        :type video: RedditDataExtractor.content.Video
        :type lstModelObj: RedditDataExtractor.GUI.genericListModelObjects.GenericListModelObj
        :type submission: praw.objects.Submission
        :type queue: Queue.queue
        :type downloadedContent: DownloadedContent
        :type avoidDuplicates: bool
        :type setMostRecentDownloadTimestamp: Worker.setMostRecentDownloadTimestamp
        :type downloaderIsStopped: function
        """
        QRunnable.__init__(self)
        self._video = video
        self._submission = submission
        self._lstModelObj = lstModelObj
        self._queue = queue
        self._downloadedContent = downloadedContent
        self._avoidDuplicates = avoidDuplicates
        self._setMostRecentDownloadTimestamp = setMostRecentDownloadTimestamp
        self._downloaderIsStopped = downloaderIsStopped

    def run(self):
        if (not self._downloaderIsStopped()) and ((not self._avoidDuplicates) or (
            self._avoidDuplicates and self._video.URL not in self._lstModelObj.externalDownloads)):
            self._lstModelObj.externalDownloads.add(
                self._video.URL)  # predict that the download will be successful - helps reduce duplicates when threads are running at similar times and download is for the same video
            if self._video.download():
                self._setMostRecentDownloadTimestamp(self._submission.created_utc)
                downloadedContentOfSubmission = self._lstModelObj.redditSubmissions.get(
                    self._downloadedContent.redditURL)
                if downloadedContentOfSubmission is None:
                    self._lstModelObj.redditSubmissions[self._downloadedContent.redditURL] = [self._downloadedContent]
                elif downloadedContentOfSubmission is not None and self._downloadedContent not in downloadedContentOfSubmission:
                    self._lstModelObj.redditSubmissions[self._downloadedContent.redditURL].append(
                        self._downloadedContent)
                self._downloadedContent.files.add(self._video.savePath)
                self._downloadedContent.externalDownloadURLs.add(self._video.URL)
                self._downloadedContent.representativeImage = pathlib.Path("RedditDataExtractor/images/videoImage.png")
                self._queue.put('Saved %s' % self._video.savePath + "\n")
            else:
                if self._video.URL in self._lstModelObj.externalDownloads:
                    self._lstModelObj.externalDownloads.remove(self._video.URL)
