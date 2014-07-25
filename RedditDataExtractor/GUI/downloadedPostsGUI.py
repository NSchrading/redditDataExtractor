import os

from PyQt4.Qt import QDialog, QMessageBox, QListWidgetItem, QListWidget, Qt, QLabel, QSize, QPixmap
from PyQt4 import QtGui

from .downloadedPosts_auto import Ui_DownloadedPosts
from ..downloader import DownloadedPostType


class DownloadedPostsGUI(QDialog, Ui_DownloadedPosts):
    def __init__(self, startingLstModelObj, model, confirmDialog, saveState):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.actionDeleteJSON = QtGui.QAction("Delete content", self)
        self.actionDeleteJSONAndBlacklist = QtGui.QAction("Delete content and never download again", self)
        self.actionDeleteExternal = QtGui.QAction("Delete content", self)
        self.actionDeleteExternalAndBlacklist = QtGui.QAction("Delete content and never download again", self)
        self.actionDeleteComment = QtGui.QAction("Delete content", self)
        self.actionDeleteCommentandBlacklist = QtGui.QAction("Delete content and never download again", self)
        self.actionDeleteSelftext = QtGui.QAction("Delete content", self)
        self.actionDeleteSelftextandBlacklist = QtGui.QAction("Delete content and never download again", self)

        self.actionDeleteJSON.triggered.connect(lambda: self.deleteContent(DownloadedPostType.JSON_DATA))
        self.actionDeleteJSONAndBlacklist.triggered.connect(lambda: self.deleteContentAndBlacklist(DownloadedPostType.JSON_DATA))
        self.actionDeleteExternal.triggered.connect(lambda: self.deleteContent(DownloadedPostType.EXTERNAL_SUBMISSION_DATA))
        self.actionDeleteExternalAndBlacklist.triggered.connect(lambda: self.deleteContentAndBlacklist(DownloadedPostType.EXTERNAL_SUBMISSION_DATA))
        self.actionDeleteComment.triggered.connect(lambda: self.deleteContent(DownloadedPostType.EXTERNAL_COMMENT_DATA))
        self.actionDeleteCommentandBlacklist.triggered.connect(lambda: self.deleteContentAndBlacklist(DownloadedPostType.EXTERNAL_COMMENT_DATA))
        self.actionDeleteSelftext.triggered.connect(lambda: self.deleteContent(DownloadedPostType.EXTERNAL_SELFTEXT_DATA))
        self.actionDeleteSelftextandBlacklist.triggered.connect(lambda: self.deleteContentAndBlacklist(DownloadedPostType.EXTERNAL_SELFTEXT_DATA))

        self.submissionJSONLst.addAction(self.actionDeleteJSON)
        self.submissionJSONLst.addAction(self.actionDeleteJSONAndBlacklist)
        self.submissionExternalLst.addAction(self.actionDeleteExternal)
        self.submissionExternalLst.addAction(self.actionDeleteExternalAndBlacklist)
        self.commentLst.addAction(self.actionDeleteComment)
        self.commentLst.addAction(self.actionDeleteCommentandBlacklist)
        self.selftextLst.addAction(self.actionDeleteSelftext)
        self.selftextLst.addAction(self.actionDeleteSelftextandBlacklist)

        self.userSubredditLst.itemClicked.connect(self.switchModelObj)

        self.startingLstModelObj = startingLstModelObj
        self.model = model
        self.confirmDialog = confirmDialog
        self.saveState = saveState

        self.initUserSubredditLst()
        self.initContentLsts()

    def initUserSubredditLst(self):
        for modelObj in self.model.stringsInLst:
            self.userSubredditLst.addItem(modelObj)
        self.userSubredditLst.setCurrentItem(self.userSubredditLst.findItems(self.startingLstModelObj.name, Qt.MatchExactly)[0])

    def initContentLsts(self):
        downloadedPosts = self.startingLstModelObj.redditPosts
        if downloadedPosts is not None and len(downloadedPosts) > 0:
            for postURL in downloadedPosts:
                for post in downloadedPosts.get(postURL):
                    if post.type == DownloadedPostType.JSON_DATA:
                        self.addToTab(post, postURL, self.submissionJSONLst)
                    elif post.type == DownloadedPostType.EXTERNAL_SUBMISSION_DATA:
                        self.addToTab(post, postURL, self.submissionExternalLst)
                    elif post.type == DownloadedPostType.EXTERNAL_COMMENT_DATA:
                        self.addToTab(post, postURL, self.commentLst)
                    elif post.type == DownloadedPostType.EXTERNAL_SELFTEXT_DATA:
                        self.addToTab(post, postURL, self.selftextLst)
        else:
            QMessageBox.information(QMessageBox(), "Reddit Data Extractor",
                                    self.startingLstModelObj.name + " has no downloaded posts. Download some by hitting the download button.")

    def clearLsts(self):
        self.submissionJSONLst.clear()
        self.submissionExternalLst.clear()
        self.commentLst.clear()
        self.selftextLst.clear()

    def switchModelObj(self, cur):
        self.clearLsts()
        self.startingLstModelObj = self.getCurrentLstModelObj()
        self.initContentLsts()

    def addToTab(self, post, postURL, lst):
        image = post.representativeImage
        if image is not None and os.path.exists(image):
            item = QListWidgetItem(postURL, lst)
            item.setTextColor(Qt.transparent)
            labelWidget = QLabel()
            labelWidget.setOpenExternalLinks(True)
            labelWidget.setTextFormat(Qt.RichText)
            size = QSize(128, 158)
            item.setSizeHint(size)
            size = QSize(128, 128)
            if(image.endswith(".webm")):
                image = "images/webmImage.png"
            pixmap = QPixmap(image)
            pixmap = pixmap.scaled(size, Qt.KeepAspectRatio)
            height = pixmap.height()
            width = pixmap.width()
            postTitle = postURL[postURL[0:-1].rfind("/") + 1:-1]
            labelWidget.setText(
                '<a href="' + postURL + '"><img src="' + str(image) + '" height="' + str(
                    height) + '" width="' + str(width) + '"><p>' + postTitle)
            lst.setItemWidget(item, labelWidget)

    def getCurrentLstModelObj(self):
        currentLstModelObjName = self.userSubredditLst.currentItem().text()
        index = self.model.getIndexOfName(currentLstModelObjName)
        index = self.model.index(index, 0)
        currentLstModelObj = self.model.getObjectInLst(index)
        return currentLstModelObj

    def getCurrentTabLstItem(self):
        currentTab = self.tabWidget.currentWidget()
        currentTabLst = currentTab.findChild(QListWidget)
        currentTabLstItem = currentTabLst.currentItem()
        return currentTabLstItem

    def deleteContentAndBlacklist(self, downloadedPostType):
        currentLstModelObj = self.getCurrentLstModelObj()
        currentTabLstItem = self.getCurrentTabLstItem()
        postURL = currentTabLstItem.text()

        deleted = self.deleteContent(downloadedPostType)
        if deleted:
            currentLstModelObj.blacklist.add(postURL)
            self.saveState()

    def deleteContent(self, downloadedPostType):
        currentLstModelObj = self.getCurrentLstModelObj()
        currentTab = self.tabWidget.currentWidget()
        currentTabLst = currentTab.findChild(QListWidget)
        currentTabLstItem = currentTabLst.currentItem()
        postURL = currentTabLstItem.text()

        posts = currentLstModelObj.redditPosts.get(postURL)
        for post in posts:
            print(post)
            if post.type == downloadedPostType:
                files = post.files
                numFiles = len(files)
                if numFiles <= 20:
                    fileStr = "".join([str(file) + "\n" for file in files])
                else:
                    fileStr = "".join([str(file) + "\n" for file in files[:20]])
                    fileStr += "\n...\nand " + str(numFiles - 20) + " others. "
                msgBox = self.confirmDialog("This will delete these files: \n" + fileStr + "Are you sure you want to delete them?")
                ret = msgBox.exec_()
                if ret == QMessageBox.Yes:
                    posts.remove(post)
                    if(len(posts) <= 0):
                        del currentLstModelObj.redditPosts[postURL]
                    else:
                        currentLstModelObj.redditPosts[postURL] = posts
                    if downloadedPostType != DownloadedPostType.JSON_DATA:
                        for externalURL in post.externalDownloadURLs:
                            if externalURL in currentLstModelObj.externalDownloads:
                                currentLstModelObj.externalDownloads.remove(externalURL)
                    item = currentTabLst.takeItem(currentTabLst.currentRow())
                    del item
                    [os.remove(file) for file in files if os.path.exists(file)]
                    QMessageBox.information(QMessageBox(), "Reddit Data Extractor", "Successfully removed requested files.")
                    self.saveState()
                    return True
                return False
        return False
