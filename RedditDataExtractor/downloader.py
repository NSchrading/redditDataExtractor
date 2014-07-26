import os
import shutil
from PyQt4.Qt import QObject, QThreadPool, pyqtSlot, pyqtSignal, QRunnable
from .redditDataExtractor import ListType


class DownloadedContentType():
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
        if self.type == DownloadedContentType.EXTERNAL_COMMENT_DATA:
            # Comments appear in a folder for the user making the comment.
            # Always remove the submissions's files (that's the point of the function) but,
            # comments from the same user can come from different submissions so only remove the folder if the folder
            # becomes empty after deleting the files.
            commentFolders = {os.path.dirname(file) for file in self.files if os.path.exists(file)}
            [os.remove(file) for file in self.files if os.path.exists(file)]
            [shutil.rmtree(commentFolder) for commentFolder in commentFolders if len(os.listdir(commentFolder)) <= 0]
        else:
            # Other types just have the files, so remove them
            [os.remove(file) for file in self.files if os.path.exists(file)]
        self.files.clear()


class Downloader(QObject):
    finished = pyqtSignal()

    def __init__(self, rddtDataExtractor, validUsersOrSubs, queue, listModelType):
        """
        The object that handles coordinating the download of the submission content. Spawns threads to download
        from users / subreddits simultaneously and to download images simultaneously.
        :type rddtDataExtractor: RedditDataExtractor.redditDataExtractor.RedditDataExtractor
        :type validUsersOrSubs: set
        :type queue: Queue.queue
        :type listModelType: RedditDataExtractor.redditDataExtractor.ListType
        """
        super().__init__()
        self.rddtDataExtractor = rddtDataExtractor
        self.validUsersOrSubs = validUsersOrSubs
        self.queue = queue
        self.listModelType = listModelType
        self.dataPool = QThreadPool()
        self.dataPool.setMaxThreadCount(4)
        self.finishSignalForTest = False

    @pyqtSlot()
    def run(self):
        self.finishSignalForTest = False
        self.rddtDataExtractor.currentlyDownloading = True
        if len(self.validUsersOrSubs) > 0:
            for lstModelObj, validatedPRAWUserOrSub in self.validUsersOrSubs:
                worker = Worker(self.rddtDataExtractor, lstModelObj, validatedPRAWUserOrSub, self.queue,
                                self.listModelType)
                self.dataPool.start(worker)
            self.dataPool.waitForDone()
        self.finished.emit()
        self.finishSignalForTest = True
        print("FINISHED DOWNLOADING!!!")


class Worker(QRunnable):
    def __init__(self, rddtDataExtractor, lstModelObj, validatedPRAWUserOrSub, queue, lstModelType):
        """
        Thread to download for a submission. Spawns more threads for downloading images or submission json data
        :param lstModelObj: The User or Subreddit "ListModel" Object
        :type rddtDataExtractor: RedditDataExtractor.redditDataExtractor.RedditDataExtractor
        :type lstModelObj: RedditDataExtractor.GUI.genericListModelObjects.GenericListModelObj
        :type validatedPRAWUserOrSub: praw.objects.Subreddit or praw.objects.User
        :type queue: Queue.queue
        :type lstModelType: RedditDataExtractor.redditDataExtractor.ListType
        """
        super().__init__()

        self.rddtDataExtractor = rddtDataExtractor
        self.lstModelObj = lstModelObj
        self.validatedPRAWUserOrSub = validatedPRAWUserOrSub
        self.queue = queue
        self.lstModelType = lstModelType
        self.imagePool = QThreadPool()
        self.imagePool.setMaxThreadCount(3)
        self.submissionPool = QThreadPool()
        self.submissionPool.setMaxThreadCount(3)
        self.mostRecentDownloadTimestamp = None

    def setMostRecentDownloadTimestamp(self, utc):
        """
        As the various threads download submissions, this keeps track of the most recently downloaded one.
        Then, when ALL downloads are finished, it sets the lstModelObj's mostRecentDownloadTimestamp. This
        allows submissions to be downloaded out of order in a download session, and still be able to prevent
        downloads from older time periods unless the user specifies they don't want that behavior.

        :type utc: float
        """
        if self.mostRecentDownloadTimestamp is None or utc > self.mostRecentDownloadTimestamp:
            self.mostRecentDownloadTimestamp = utc

    def startDownloadsForSubmission(self, submission):
        """
        :type submission: praw.objects.Submission
        """
        if self.rddtDataExtractor.getExternalContent and self.lstModelObj.isNewContent(submission,
                                                                                       DownloadedContentType.EXTERNAL_SUBMISSION_DATA) and not submission.is_self and not "reddit" in submission.domain:
            downloadedContent = DownloadedContent(submission.permalink, DownloadedContentType.EXTERNAL_SUBMISSION_DATA)
            images = self.rddtDataExtractor.getImages(submission, self.lstModelObj, self.queue)
            self.startDownloadImages(images, downloadedContent, submission)
        if self.rddtDataExtractor.getCommentExternalContent and self.lstModelObj.isNewContent(submission,
                                                                                              DownloadedContentType.EXTERNAL_COMMENT_DATA):
            downloadedContent = DownloadedContent(submission.permalink, DownloadedContentType.EXTERNAL_COMMENT_DATA)
            images = self.rddtDataExtractor.getCommentImages(submission, self.lstModelObj, self.queue)
            self.startDownloadImages(images, downloadedContent, submission)
        if self.rddtDataExtractor.getSelftextExternalContent and self.lstModelObj.isNewContent(submission,
                                                                                               DownloadedContentType.EXTERNAL_SELFTEXT_DATA):
            downloadedContent = DownloadedContent(submission.permalink, DownloadedContentType.EXTERNAL_SELFTEXT_DATA)
            images = self.rddtDataExtractor.getSelftextImages(submission, self.lstModelObj, self.queue)
            self.startDownloadImages(images, downloadedContent, submission)
        if self.rddtDataExtractor.getSubmissionContent and self.lstModelObj.isNewContent(submission,
                                                                                         DownloadedContentType.JSON_DATA):
            downloadedContent = DownloadedContent(submission.permalink, DownloadedContentType.JSON_DATA)
            submissionWorker = SubmissionWorker(self.rddtDataExtractor, self.lstModelObj, submission, self.queue,
                                                downloadedContent, self.lstModelType,
                                                self.setMostRecentDownloadTimestamp)
            self.submissionPool.start(submissionWorker)

    def startDownloadImages(self, images, downloadedContent, submission):
        """
        :type: images: generator
        :type downloadedContent: DownloadedContent
        :type: submission: praw.objects.Submission
        """
        if images is not None:
            for image in images:
                if image is not None:
                    imageWorker = ImageWorker(image, self.lstModelObj, submission, self.queue, downloadedContent,
                                              self.rddtDataExtractor.avoidDuplicates, self.setMostRecentDownloadTimestamp)
                    self.imagePool.start(imageWorker)

    def run(self):
        name = self.lstModelObj.name
        self.queue.put("Starting download for " + name + "\n")
        self.rddtDataExtractor.makeDirectory(name)
        if self.lstModelType == ListType.SUBREDDIT:
            submitted = self.rddtDataExtractor.getSubredditSubmissions(self.validatedPRAWUserOrSub)
        else:
            submitted = self.validatedPRAWUserOrSub.get_submitted(limit=None)
        submissions = self.rddtDataExtractor.getValidSubmissions(submitted, self.lstModelObj)
        for submission, passesFilter in submissions:
            if passesFilter:
                self.startDownloadsForSubmission(submission)
        self.imagePool.waitForDone()
        self.submissionPool.waitForDone()
        self.lstModelObj.mostRecentDownloadTimestamp = self.mostRecentDownloadTimestamp
        self.queue.put("Finished download for " + name + "\n")


class SubmissionWorker(QRunnable):
    def __init__(self, rddtDataExtractor, lstModelObj, submission, queue, downloadedContent, lstModelType,
                 setMostRecentDownloadTimestamp):
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
        """
        super().__init__()

        self.rddtDataExtractor = rddtDataExtractor
        self.lstModelObj = lstModelObj
        self.submission = submission
        self.queue = queue
        self.downloadedContent = downloadedContent
        self.lstModelType = lstModelType
        self.setMostRecentDownloadTimestamp = setMostRecentDownloadTimestamp
        self.downloadedContent.representativeImage = "RedditDataExtractor/images/jsonImage.png"

    def run(self):
        title = self.submission.title
        if self.lstModelType == ListType.USER:
            success, savePath = self.rddtDataExtractor.downloadSubmission(self.submission, self.lstModelObj.name)
        else:
            success, savePath = self.rddtDataExtractor.downloadSubmission(self.submission)
        if success:
            self.downloadedContent.files.add(savePath)
            downloadedContentOfSubmission = self.lstModelObj.redditSubmissions.get(self.downloadedContent.redditURL)
            if downloadedContentOfSubmission is None:
                self.lstModelObj.redditSubmissions[self.downloadedContent.redditURL] = [self.downloadedContent]
            elif downloadedContentOfSubmission is not None and self.downloadedContent not in downloadedContentOfSubmission:
                self.lstModelObj.redditSubmissions[self.downloadedContent.redditURL].append(self.downloadedContent)
            self.setMostRecentDownloadTimestamp(self.submission.created_utc)
            self.queue.put("Saved submission: " + title + "\n")
        else:
            self.queue.put(
                ">>> Error saving submission: " + title + '.\n>>> To attempt to redownload this file, uncheck "Restrict retrieved submissions to creation dates after the last downloaded submission" in the settings.\n')


class ImageWorker(QRunnable):
    def __init__(self, image, lstModelObj, submission, queue, downloadedContent, avoidDuplicates,
                 setMostRecentDownloadTimestamp):
        """
        Thread to download images / gifs / webms of a submission.
        :param lstModelObj: The User or Subreddit "ListModel" Object
        :type image: RedditDataExtractor.image.Image
        :type lstModelObj: RedditDataExtractor.GUI.genericListModelObjects.GenericListModelObj
        :type submission: praw.objects.Submission
        :type queue: Queue.queue
        :type downloadedContent: DownloadedContent
        :type avoidDuplicates: bool
        :type setMostRecentDownloadTimestamp: Worker.setMostRecentDownloadTimestamp
        """
        super().__init__()

        self.image = image
        self.user = lstModelObj
        self.submission = submission
        self.queue = queue
        self.downloadedContent = downloadedContent
        self.avoidDuplicates = avoidDuplicates
        self.setMostRecentDownloadTimestamp = setMostRecentDownloadTimestamp


    def run(self):
        if (not self.avoidDuplicates) or (self.avoidDuplicates and self.image.URL not in self.user.externalDownloads):
            self.user.externalDownloads.add(
                self.image.URL)  # predict that the download will be successful - helps reduce duplicates when threads are running at similar times and download is for the same image
            if self.image.download():
                self.setMostRecentDownloadTimestamp(self.submission.created_utc)
                downloadedContentOfSubmission = self.user.redditSubmissions.get(self.downloadedContent.redditURL)
                if downloadedContentOfSubmission is None:
                    self.user.redditSubmissions[self.downloadedContent.redditURL] = [self.downloadedContent]
                elif downloadedContentOfSubmission is not None and self.downloadedContent not in downloadedContentOfSubmission:
                    self.user.redditSubmissions[self.downloadedContent.redditURL].append(self.downloadedContent)
                if self.downloadedContent.representativeImage is None:
                    self.downloadedContent.representativeImage = self.image.savePath
                self.downloadedContent.files.add(self.image.savePath)
                self.downloadedContent.externalDownloadURLs.add(self.image.URL)
                self.queue.put('Saved %s' % self.image.savePath + "\n")
            else:
                if self.image.URL in self.user.externalDownloads:
                    self.user.externalDownloads.remove(self.image.URL)
                self.queue.put(
                    '>>> Error saving ' + self.image.savePath + '.\n>>> To attempt to redownload this file, uncheck "Restrict retrieved submissions to creation dates after the last downloaded submission" in the settings.\n')
