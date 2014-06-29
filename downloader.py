from PyQt4.Qt import *
from redditData import DownloadType

class Downloader(QObject):

    finished = pyqtSignal()

    def __init__(self, rddtScraper, validData, queue, downloadType):
        super().__init__()
        self.rddtScraper = rddtScraper
        self.validData = validData
        self.queue = queue
        self.downloadType = downloadType
        self.dataPool = QThreadPool()
        self.dataPool.setMaxThreadCount(4)

    @pyqtSlot()
    def run(self):
        if self.downloadType == DownloadType.SUBREDDIT_CONTENT:
            if len(self.validData) > 0:
                for submissions in self.validData:
                    submissionWorker = SubmissionWorker(self.rddtScraper, submissions, self.queue)
                    self.dataPool.start(submissionWorker)
                self.dataPool.waitForDone()
        else:
            if len(self.validData) > 0:
                for user, redditor in self.validData:
                    userWorker = UserWorker(self.rddtScraper, user, redditor, self.queue)
                    self.dataPool.start(userWorker)
                self.dataPool.waitForDone()

        self.rddtScraper.saveState()
        self.finished.emit()

class UserWorker(QRunnable):
    def __init__(self, rddtScraper, user, redditor, queue):
        super().__init__()

        self.rddtScraper = rddtScraper
        self.user = user
        self.redditor = redditor
        self.queue = queue
        self.imagePool = QThreadPool()
        self.imagePool.setMaxThreadCount(3)

    def run(self):
        userName = self.user.name
        self.queue.put("Starting download for " + userName + "\n")
        self.rddtScraper.makeDirectory(userName)
        # Temporary
        refresh = None
        submitted = self.redditor.get_submitted(limit=refresh)
        posts = self.rddtScraper.getValidPosts(submitted, self.user)
        for post in posts:
            images = []
            if self.rddtScraper.getCommentData:
                images.extend(self.rddtScraper.getCommentImages(post, self.user))
            images.extend(self.rddtScraper.getImages(post, self.user))
            for image in images:
                if image is not None:
                    imageWorker = ImageWorker(image, self.user, self.rddtScraper.avoidDuplicates, self.queue)
                    self.imagePool.start(imageWorker)
            self.imagePool.waitForDone()

class SubmissionWorker(QRunnable):
    def __init__(self, rddtScraper, allSubmissions, queue):
        super().__init__()

        self.rddtScraper = rddtScraper
        self.allSubmissions = allSubmissions
        self.queue = queue

    def run(self):
        subreddit, submissions = self.allSubmissions
        for submission in submissions:
            title = submission.title
            self.rddtScraper.makeDirectory(subreddit)
            self.rddtScraper.downloadSubmission(subreddit, submission)
            self.queue.put("Saved submission: " + title + "\n")

class ImageWorker(QRunnable):
    def __init__(self, image, user, avoidDuplicates, queue):
        super().__init__()

        self.image = image
        self.user = user
        self.avoidDuplicates = avoidDuplicates
        self.queue = queue

    def addRepresentativeImage(self):
        # Add 1 representative picture for this post, even if it is an album with multiple pictures
        # Don't allow comment images to be a representative image
        if self.user.redditPosts.get(self.image.redditPostURL) is None and self.image.commentAuthor is None:
            self.user.redditPosts[self.image.redditPostURL] = self.image.savePath

    def run(self):
        allExternalDownloads = set([])
        for redditPostURL in self.user.externalDownloads:
            allExternalDownloads = allExternalDownloads.union(allExternalDownloads, self.user.externalDownloads.get(redditPostURL))
        if (not self.avoidDuplicates) or (self.avoidDuplicates and self.image.URL not in allExternalDownloads):
            self.addRepresentativeImage()
            if self.user.externalDownloads.get(self.image.redditPostURL) is None:
                self.user.externalDownloads[self.image.redditPostURL] = {self.image.URL}
            else:
                self.user.externalDownloads.get(self.image.redditPostURL).add(self.image.URL)
            self.image.download()
            self.queue.put('Saved %s' % self.image.savePath + "\n")
