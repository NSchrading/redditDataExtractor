from PyQt4.Qt import QObject, QThreadPool, pyqtSlot, pyqtSignal, QRunnable
from .redditDataExtractor import ListType


class DownloadedPostType():
    EXTERNAL_SUBMISSION_DATA = 1
    EXTERNAL_COMMENT_DATA = 2
    EXTERNAL_SELFTEXT_DATA = 3
    JSON_DATA = 4

class DownloadedPost():
    __slots__ = ('redditURL', 'type', 'representativeImage', 'files', 'externalDownloadURLs')

    def __init__(self, redditURL, type):
        self.redditURL = redditURL
        self.type = type
        self.files = set()
        self.externalDownloadURLs = set()
        self.representativeImage = None

    def deleteFiles(self):
        pass


class Downloader(QObject):

    finished = pyqtSignal()

    def __init__(self, rddtDataExtractor, validData, queue, listModelType):
        super().__init__()
        self.rddtDataExtractor = rddtDataExtractor
        self.validData = validData
        self.queue = queue
        self.listModelType = listModelType
        self.dataPool = QThreadPool()
        self.dataPool.setMaxThreadCount(4)
        self.finishSignalForTest = False

    @pyqtSlot()
    def run(self):
        self.finishSignalForTest = False
        self.rddtDataExtractor.currentlyDownloading = True
        if len(self.validData) > 0:
            for listModel, prawData in self.validData:
                worker = Worker(self.rddtDataExtractor, listModel, prawData, self.queue, self.listModelType)
                self.dataPool.start(worker)
            self.dataPool.waitForDone()
        self.finished.emit()
        self.finishSignalForTest = True
        print("FINISHED DOWNLOADING!!!")

class Worker(QRunnable):
    def __init__(self, rddtDataExtractor, listModel, prawData, queue, listModelType):
        super().__init__()

        self.rddtDataExtractor = rddtDataExtractor
        self.listModel = listModel
        self.prawData = prawData
        self.queue = queue
        self.listModelType = listModelType
        self.imagePool = QThreadPool()
        self.imagePool.setMaxThreadCount(3)
        self.submissionPool = QThreadPool()
        self.submissionPool.setMaxThreadCount(3)
        self.mostRecentDownloadTimestamp = None

    def setMostRecentDownloadTimestamp(self, utc):
        if self.mostRecentDownloadTimestamp is None or utc > self.mostRecentDownloadTimestamp:
            self.mostRecentDownloadTimestamp = utc

    def startDownloadsForPost(self, post):
        name = self.listModel.name
        if self.rddtDataExtractor.getExternalContent and self.listModel.isNewContent(post, DownloadedPostType.EXTERNAL_SUBMISSION_DATA) and not post.is_self and not "reddit" in post.domain:
            downloadedPost = DownloadedPost(post.permalink, DownloadedPostType.EXTERNAL_SUBMISSION_DATA)
            images = self.rddtDataExtractor.getImages(post, self.listModel, self.queue)
            self.startDownloadImages(images, downloadedPost, post)
        if self.rddtDataExtractor.getCommentExternalContent and self.listModel.isNewContent(post, DownloadedPostType.EXTERNAL_COMMENT_DATA):
            downloadedPost = DownloadedPost(post.permalink, DownloadedPostType.EXTERNAL_COMMENT_DATA)
            images = self.rddtDataExtractor.getCommentImages(post, self.listModel, self.queue)
            self.startDownloadImages(images, downloadedPost, post)
        if self.rddtDataExtractor.getSelftextExternalContent and self.listModel.isNewContent(post, DownloadedPostType.EXTERNAL_SELFTEXT_DATA):
            downloadedPost = DownloadedPost(post.permalink, DownloadedPostType.EXTERNAL_SELFTEXT_DATA)
            images = self.rddtDataExtractor.getSelftextImages(post, self.listModel, self.queue)
            self.startDownloadImages(images, downloadedPost, post)
        if self.rddtDataExtractor.getSubmissionContent and self.listModel.isNewContent(post, DownloadedPostType.JSON_DATA):
            downloadedPost = DownloadedPost(post.permalink, DownloadedPostType.JSON_DATA)
            submissionWorker = SubmissionWorker(self.rddtDataExtractor, post, self.queue, self.listModel, self.listModelType, name, downloadedPost, self.setMostRecentDownloadTimestamp)
            self.submissionPool.start(submissionWorker)

    def startDownloadImages(self, images, downloadedPost, post):
        for image in images:
            if image is not None:
                imageWorker = ImageWorker(image, self.listModel, self.rddtDataExtractor.avoidDuplicates, self.queue, downloadedPost, post, self.listModel, self.setMostRecentDownloadTimestamp)
                self.imagePool.start(imageWorker)

    def run(self):
        name = self.listModel.name
        self.queue.put("Starting download for " + name + "\n")
        self.rddtDataExtractor.makeDirectory(name)
        if self.listModelType == ListType.SUBREDDIT:
            submitted = self.rddtDataExtractor.getSubredditSubmissions(self.prawData, self.listModel)
        else:
            submitted = self.prawData.get_submitted(limit=None)
        posts = self.rddtDataExtractor.getValidPosts(submitted, self.listModel)
        for post, passesFilter in posts:
            if passesFilter:
                self.startDownloadsForPost(post)
        self.imagePool.waitForDone()
        self.submissionPool.waitForDone()
        self.listModel.mostRecentDownloadTimestamp = self.mostRecentDownloadTimestamp
        self.queue.put("Finished download for " + name + "\n")


class SubmissionWorker(QRunnable):
    def __init__(self, rddtDataExtractor, submission, queue, listModel, listModelType, listModelName, downloadedPost, setMostRecentDownloadTimestamp):
        super().__init__()

        self.rddtDataExtractor = rddtDataExtractor
        self.submission = submission
        self.queue = queue
        self.listModel = listModel
        self.listModelType = listModelType
        self.listModelName = listModelName
        self.downloadedPost = downloadedPost
        self.downloadedPost.representativeImage = "images/jsonImage.png"
        self.setMostRecentDownloadTimestamp = setMostRecentDownloadTimestamp

    def run(self):
        title = self.submission.title
        if self.listModelType == ListType.USER:
            success, savePath = self.rddtDataExtractor.downloadSubmission(self.submission, self.listModelName)
        else:
            success, savePath = self.rddtDataExtractor.downloadSubmission(self.submission)
        if success:
            self.downloadedPost.files.add(savePath)
            posts = self.listModel.redditPosts.get(self.downloadedPost.redditURL)
            if posts is None:
                self.listModel.redditPosts[self.downloadedPost.redditURL] = [self.downloadedPost]
            elif posts is not None and self.downloadedPost not in posts:
                self.listModel.redditPosts[self.downloadedPost.redditURL].append(self.downloadedPost)
            self.setMostRecentDownloadTimestamp(self.submission.created_utc)
            self.queue.put("Saved submission: " + title + "\n")
        else:
            self.queue.put(">>> Error saving submission: " + title + '.\n>>> To attempt to redownload this file, uncheck "Restrict retrieved submissions to creation dates after the last downloaded submission" in the settings.\n')

class ImageWorker(QRunnable):
    def __init__(self, image, user, avoidDuplicates, queue, downloadedPost, post, listModel, setMostRecentDownloadTimestamp):
        super().__init__()

        self.image = image
        self.user = user
        self.avoidDuplicates = avoidDuplicates
        self.queue = queue
        self.downloadedPost = downloadedPost
        self.post = post
        self.listModel = listModel
        self.setMostRecentDownloadTimestamp = setMostRecentDownloadTimestamp


    def run(self):
        if (not self.avoidDuplicates) or (self.avoidDuplicates and self.image.URL not in self.user.externalDownloads):
            self.user.externalDownloads.add(self.image.URL) # predict that the download will be successful - helps reduce duplicates when threads are running at similar times and download is for the same image
            if self.image.download():
                self.setMostRecentDownloadTimestamp(self.post.created_utc)
                posts = self.user.redditPosts.get(self.downloadedPost.redditURL)
                if posts is None:
                    self.user.redditPosts[self.downloadedPost.redditURL] = [self.downloadedPost]
                elif posts is not None and self.downloadedPost not in posts:
                    self.user.redditPosts[self.downloadedPost.redditURL].append(self.downloadedPost)
                if self.downloadedPost.representativeImage is None:
                    self.downloadedPost.representativeImage = self.image.savePath
                self.downloadedPost.files.add(self.image.savePath)
                self.downloadedPost.externalDownloadURLs.add(self.image.URL)
                self.queue.put('Saved %s' % self.image.savePath + "\n")
            else:
                if self.image.URL in self.user.externalDownloads:
                    self.user.externalDownloads.remove(self.image.URL)
                self.queue.put('>>> Error saving ' + self.image.savePath + '.\n>>> To attempt to redownload this file, uncheck "Restrict retrieved submissions to creation dates after the last downloaded submission" in the settings.\n')
