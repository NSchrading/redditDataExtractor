import os

from PyQt4.Qt import QDialog, QMessageBox, QListWidgetItem, QListWidget, Qt, QLabel, QSize, QPixmap
from PyQt4 import QtGui

from .downloadedContent_auto import Ui_DownloadedContentWindow
from ..downloader import DownloadedContentType


class DownloadedContentGUI(QDialog, Ui_DownloadedContentWindow):
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

        self.actionDeleteJSON.triggered.connect(lambda: self.deleteContent(DownloadedContentType.JSON_DATA))
        self.actionDeleteJSONAndBlacklist.triggered.connect(lambda: self.deleteContentAndBlacklist(DownloadedContentType.JSON_DATA))
        self.actionDeleteExternal.triggered.connect(lambda: self.deleteContent(DownloadedContentType.EXTERNAL_SUBMISSION_DATA))
        self.actionDeleteExternalAndBlacklist.triggered.connect(lambda: self.deleteContentAndBlacklist(DownloadedContentType.EXTERNAL_SUBMISSION_DATA))
        self.actionDeleteComment.triggered.connect(lambda: self.deleteContent(DownloadedContentType.EXTERNAL_COMMENT_DATA))
        self.actionDeleteCommentandBlacklist.triggered.connect(lambda: self.deleteContentAndBlacklist(DownloadedContentType.EXTERNAL_COMMENT_DATA))
        self.actionDeleteSelftext.triggered.connect(lambda: self.deleteContent(DownloadedContentType.EXTERNAL_SELFTEXT_DATA))
        self.actionDeleteSelftextandBlacklist.triggered.connect(lambda: self.deleteContentAndBlacklist(DownloadedContentType.EXTERNAL_SELFTEXT_DATA))

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
        downloadedContent = self.startingLstModelObj.redditSubmissions
        if downloadedContent is not None and len(downloadedContent) > 0:
            for submissionURL in downloadedContent:
                for submission in downloadedContent.get(submissionURL):
                    if submission.type == DownloadedContentType.JSON_DATA:
                        self.addToTab(submission, submissionURL, self.submissionJSONLst)
                    elif submission.type == DownloadedContentType.EXTERNAL_SUBMISSION_DATA:
                        self.addToTab(submission, submissionURL, self.submissionExternalLst)
                    elif submission.type == DownloadedContentType.EXTERNAL_COMMENT_DATA:
                        self.addToTab(submission, submissionURL, self.commentLst)
                    elif submission.type == DownloadedContentType.EXTERNAL_SELFTEXT_DATA:
                        self.addToTab(submission, submissionURL, self.selftextLst)
        else:
            QMessageBox.information(QMessageBox(), "Reddit Data Extractor",
                                    self.startingLstModelObj.name + " has no downloaded submissions. Download some by hitting the download button.")

    def clearLsts(self):
        self.submissionJSONLst.clear()
        self.submissionExternalLst.clear()
        self.commentLst.clear()
        self.selftextLst.clear()

    def switchModelObj(self, cur):
        self.clearLsts()
        self.startingLstModelObj = self.getCurrentLstModelObj()
        self.initContentLsts()

    def addToTab(self, submission, submissionURL, lst):
        image = submission.representativeImage
        if image is not None and os.path.exists(image):
            item = QListWidgetItem(submissionURL, lst)
            item.setTextColor(Qt.transparent)
            labelWidget = QLabel()
            labelWidget.setOpenExternalLinks(True)
            labelWidget.setTextFormat(Qt.RichText)
            size = QSize(128, 158)
            item.setSizeHint(size)
            size = QSize(128, 128)
            if(image.endswith(".webm")):
                image = "RedditDataExtractor/images/webmImage.png"
            pixmap = QPixmap(image)
            pixmap = pixmap.scaled(size, Qt.KeepAspectRatio)
            height = pixmap.height()
            width = pixmap.width()
            submissionTitle = submissionURL[submissionURL[0:-1].rfind("/") + 1:-1]
            labelWidget.setText(
                '<a href="' + submissionURL + '"><img src="' + str(image) + '" height="' + str(
                    height) + '" width="' + str(width) + '"><p>' + submissionTitle)
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

    def deleteContentAndBlacklist(self, downloadedContentType):
        currentLstModelObj = self.getCurrentLstModelObj()
        currentTabLstItem = self.getCurrentTabLstItem()
        submissionURL = currentTabLstItem.text()

        deleted = self.deleteContent(downloadedContentType)
        if deleted:
            currentLstModelObj.blacklist.add(submissionURL)
            self.saveState()

    def deleteContent(self, downloadedContentType):
        currentLstModelObj = self.getCurrentLstModelObj()
        currentTab = self.tabWidget.currentWidget()
        currentTabLst = currentTab.findChild(QListWidget)
        currentTabLstItem = currentTabLst.currentItem()
        submissionURL = currentTabLstItem.text()

        downloadedContentForSubmission = currentLstModelObj.redditSubmissions.get(submissionURL)
        for content in downloadedContentForSubmission:
            print(content)
            if content.type == downloadedContentType:
                files = content.files
                numFiles = len(files)
                if numFiles <= 20:
                    fileStr = "".join([str(file) + "\n" for file in files])
                else:
                    fileStr = "".join([str(file) + "\n" for file in files[:20]])
                    fileStr += "\n...\nand " + str(numFiles - 20) + " others. "
                msgBox = self.confirmDialog("This will delete these files: \n" + fileStr + "Are you sure you want to delete them?")
                ret = msgBox.exec_()
                if ret == QMessageBox.Yes:
                    downloadedContentForSubmission.remove(content)
                    if(len(downloadedContentForSubmission) <= 0):
                        del currentLstModelObj.redditSubmissions[submissionURL]
                    else:
                        currentLstModelObj.redditSubmissions[submissionURL] = downloadedContentForSubmission
                    if downloadedContentType != DownloadedContentType.JSON_DATA:
                        for externalURL in content.externalDownloadURLs:
                            if externalURL in currentLstModelObj.externalDownloads:
                                currentLstModelObj.externalDownloads.remove(externalURL)
                    item = currentTabLst.takeItem(currentTabLst.currentRow())
                    del item
                    content.deleteFiles()
                    del content
                    QMessageBox.information(QMessageBox(), "Reddit Data Extractor", "Successfully removed requested files.")
                    self.saveState()
                    return True
                return False
        return False
