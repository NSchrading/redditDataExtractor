from PyQt4.Qt import *
from redditData import DownloadType

class Downloader(QObject):

    finished = pyqtSignal()
    def __init__(self, rddtScraper, queue):
        super().__init__()
        self.rddtScraper = rddtScraper
        self.queue = queue
        self.userPool = QThreadPool()
        self.userPool.setMaxThreadCount(4)

    @pyqtSlot()
    def run(self):
        if self.rddtScraper.downloadType == DownloadType.USER_SUBREDDIT_CONSTRAINED or self.rddtScraper.downloadType == DownloadType.USER_SUBREDDIT_ALL:
            validRedditors = self.rddtScraper.getValidRedditors()
        if len(validRedditors) > 0:
            for user, redditor in validRedditors:
                self.queue.put("Starting download for " + user.name + "\n")
                userWorker = UserWorker(self.rddtScraper, user, redditor, self.queue)
                self.userPool.start(userWorker)
            self.userPool.waitForDone()
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
        self.rddtScraper.makeDirectoryForUser(userName)
        # Temporary
        refresh = None
        submitted = self.redditor.get_submitted(limit=refresh)
        posts = self.rddtScraper.getValidPosts(submitted, self.user)
        images = self.rddtScraper.getImages(posts, self.user)
        for image in images:
            if image is not None:
                imageWorker = ImageWorker(image, self.user, self.rddtScraper.avoidDuplicates, self.queue)
                self.imagePool.start(imageWorker)
        self.imagePool.waitForDone()


class ImageWorker(QRunnable):
    def __init__(self, image, user, avoidDuplicates, queue):
        super().__init__()

        self.image = image
        self.user = user
        self.avoidDuplicates = avoidDuplicates
        self.queue = queue

    def run(self):
        if self.image.download(self.user, self.avoidDuplicates):
            self.queue.put('Saving %s...' % self.image.savePath + "\n")
