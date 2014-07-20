from PyQt4.Qt import *
from redditData import ListType

class DownloadedPostType():
    EXTERNAL_DATA = 1
    JSON_DATA = 2

class DownloadedPost():
    __slots__ = ('redditURL', 'type', 'representativeImage', 'files')

    def __init__(self, redditURL, type):
        self.redditURL = redditURL
        self.type = type
        self.files = []
        self.representativeImage = None

    def deleteFiles(self):
        pass


class Downloader(QObject):

    finished = pyqtSignal()

    def __init__(self, rddtScraper, validData, queue, listModelType):
        super().__init__()
        self.rddtScraper = rddtScraper
        self.validData = validData
        self.queue = queue
        self.listModelType = listModelType
        self.dataPool = QThreadPool()
        self.dataPool.setMaxThreadCount(4)

    @pyqtSlot()
    def run(self):
        if len(self.validData) > 0:
            for listModel, prawData in self.validData:
                worker = Worker(self.rddtScraper, listModel, prawData, self.queue, self.listModelType)
                self.dataPool.start(worker)
            self.dataPool.waitForDone()
        self.finished.emit()

class Worker(QRunnable):
    def __init__(self, rddtScraper, listModel, prawData, queue, listModelType):
        super().__init__()

        self.rddtScraper = rddtScraper
        self.listModel = listModel
        self.prawData = prawData
        self.queue = queue
        self.listModelType = listModelType
        self.imagePool = QThreadPool()
        self.imagePool.setMaxThreadCount(3)
        self.submissionPool = QThreadPool()
        self.submissionPool.setMaxThreadCount(3)

    def run(self):
        name = self.listModel.name
        self.queue.put("Starting download for " + name + "\n")
        self.rddtScraper.makeDirectory(name)
        if self.listModelType == ListType.SUBREDDIT:
            submitted = self.rddtScraper.getSubredditSubmissions(self.prawData, self.listModel)
        else:
            # Temporary
            refresh = None
            submitted = self.prawData.get_submitted(limit=refresh)
        posts = self.rddtScraper.getValidPosts(submitted, self.listModel)
        print("num valid posts: " + str(len(posts)))
        if self.rddtScraper.filterSubmissionContent or self.rddtScraper.filterExternalContent:
            postIdsPassingFilters = self.rddtScraper.getPostIdsPassingFilters(posts)
        for post in posts:
            if self.rddtScraper.getExternalContent and ((not self.rddtScraper.filterExternalContent) or post.id in postIdsPassingFilters) and not post.is_self and not "reddit" in post.domain:
                downloadedPost = DownloadedPost(post.permalink, DownloadedPostType.EXTERNAL_DATA)
                if self.rddtScraper.getCommentData:
                    images = self.rddtScraper.getCommentImages(post, self.listModel)
                    for image in images:
                        if image is not None:
                            imageWorker = ImageWorker(image, self.listModel, self.rddtScraper.avoidDuplicates, self.queue, downloadedPost, post, self.listModel)
                            self.imagePool.start(imageWorker)
                images = self.rddtScraper.getImages(post, self.listModel)
                for image in images:
                    if image is not None:
                        imageWorker = ImageWorker(image, self.listModel, self.rddtScraper.avoidDuplicates, self.queue, downloadedPost, post, self.listModel)
                        self.imagePool.start(imageWorker)
            if self.rddtScraper.getSubmissionContent and ((not self.rddtScraper.filterSubmissionContent) or post.id in postIdsPassingFilters):
                downloadedPost = DownloadedPost(post.permalink, DownloadedPostType.JSON_DATA)
                submissionWorker = SubmissionWorker(self.rddtScraper, post, self.queue, self.listModel, self.listModelType, name, downloadedPost)
                self.submissionPool.start(submissionWorker)
        self.imagePool.waitForDone()
        self.submissionPool.waitForDone()
        self.queue.put("Finished download for " + name + "\n")


class SubmissionWorker(QRunnable):
    def __init__(self, rddtScraper, submission, queue, listModel, listModelType, listModelName, downloadedPost):
        super().__init__()

        self.rddtScraper = rddtScraper
        self.submission = submission
        self.queue = queue
        self.listModel = listModel
        self.listModelType = listModelType
        self.listModelName = listModelName
        self.downloadedPost = downloadedPost
        self.downloadedPost.representativeImage = "images/jsonImage.png"

    def run(self):
        title = self.submission.title
        if self.listModelType == ListType.USER:
            success, savePath = self.rddtScraper.downloadSubmission(self.submission, self.listModelName)
        else:
            success, savePath = self.rddtScraper.downloadSubmission(self.submission)
        if success:
            self.downloadedPost.files.append(savePath)
            posts = self.listModel.redditPosts.get(self.downloadedPost.redditURL)
            if posts is None:
                self.listModel.redditPosts[self.downloadedPost.redditURL] = [self.downloadedPost]
            elif posts is not None and self.downloadedPost not in posts:
                self.listModel.redditPosts[self.downloadedPost.redditURL].append(self.downloadedPost)
            self.listModel.mostRecentDownloadTimestamp = self.submission.created_utc
            self.queue.put("Saved submission: " + title + "\n")
        else:
            self.queue.put("Error saving submission: " + title + "\n")

class ImageWorker(QRunnable):
    def __init__(self, image, user, avoidDuplicates, queue, downloadedPost, post, listModel):
        super().__init__()

        self.image = image
        self.user = user
        self.avoidDuplicates = avoidDuplicates
        self.queue = queue
        self.downloadedPost = downloadedPost
        self.post = post
        self.listModel = listModel


    def run(self):
        allExternalDownloads = set([])
        for redditPostURL in self.user.externalDownloads:
            allExternalDownloads = allExternalDownloads.union(allExternalDownloads, self.user.externalDownloads.get(redditPostURL))
        if (not self.avoidDuplicates) or (self.avoidDuplicates and self.image.URL not in allExternalDownloads):
            if self.image.download():
                self.listModel.mostRecentDownloadTimestamp = self.post.created_utc
                posts = self.user.redditPosts.get(self.downloadedPost.redditURL)
                if posts is None:
                    self.user.redditPosts[self.downloadedPost.redditURL] = [self.downloadedPost]
                elif posts is not None and self.downloadedPost not in posts:
                    self.user.redditPosts[self.downloadedPost.redditURL].append(self.downloadedPost)
                if self.image.commentAuthor is None and self.downloadedPost.representativeImage is None:
                    self.downloadedPost.representativeImage = self.image.savePath
                self.downloadedPost.files.append(self.image.savePath)

                if self.user.externalDownloads.get(self.image.redditPostURL) is None:
                    self.user.externalDownloads[self.image.redditPostURL] = {self.image.URL}
                else:
                    self.user.externalDownloads.get(self.image.redditPostURL).add(self.image.URL)
                self.queue.put('Saved %s' % self.image.savePath + "\n")
            else:
                self.queue.put('Error saving %s' % self.image.savePath + "\n")
