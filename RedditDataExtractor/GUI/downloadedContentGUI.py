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

from PyQt4.Qt import QDialog, QMessageBox, QListWidgetItem, QListWidget, Qt, QLabel, QSize, QPixmap
from PyQt4 import QtGui

from .downloadedContent_auto import Ui_DownloadedContentWindow
from ..downloader import DownloadedContentType


class DownloadedContentGUI(QDialog, Ui_DownloadedContentWindow):
    def __init__(self, startingLstModelObj, model, confirmDialog, saveState):
        """
        A nice looking dialog to display the downloads of different users / subreddits, broken up by downloadType
        :param startingLstModelObj: The user / subreddit lstModelObj that was selected to view downloads for
        :param model: The list that the user / subreddit is in

        :type startingLstModelObj: RedditDataExtractor.GUI.genericListModelObjects.GenericListModelObj
        :type model: RedditDataExtractor.GUI.listModel.ListModel
        :type confirmDialog: function
        :type saveState: function
        """
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

        self.actionDeleteJSON.triggered.connect(lambda: self._deleteContent(DownloadedContentType.JSON_DATA))
        self.actionDeleteJSONAndBlacklist.triggered.connect(lambda: self._deleteContentAndBlacklist(DownloadedContentType.JSON_DATA))
        self.actionDeleteExternal.triggered.connect(lambda: self._deleteContent(DownloadedContentType.EXTERNAL_SUBMISSION_DATA))
        self.actionDeleteExternalAndBlacklist.triggered.connect(lambda: self._deleteContentAndBlacklist(DownloadedContentType.EXTERNAL_SUBMISSION_DATA))
        self.actionDeleteComment.triggered.connect(lambda: self._deleteContent(DownloadedContentType.EXTERNAL_COMMENT_DATA))
        self.actionDeleteCommentandBlacklist.triggered.connect(lambda: self._deleteContentAndBlacklist(DownloadedContentType.EXTERNAL_COMMENT_DATA))
        self.actionDeleteSelftext.triggered.connect(lambda: self._deleteContent(DownloadedContentType.EXTERNAL_SELFTEXT_DATA))
        self.actionDeleteSelftextandBlacklist.triggered.connect(lambda: self._deleteContentAndBlacklist(DownloadedContentType.EXTERNAL_SELFTEXT_DATA))

        self.submissionJSONLst.addAction(self.actionDeleteJSON)
        self.submissionJSONLst.addAction(self.actionDeleteJSONAndBlacklist)
        self.submissionExternalLst.addAction(self.actionDeleteExternal)
        self.submissionExternalLst.addAction(self.actionDeleteExternalAndBlacklist)
        self.commentLst.addAction(self.actionDeleteComment)
        self.commentLst.addAction(self.actionDeleteCommentandBlacklist)
        self.selftextLst.addAction(self.actionDeleteSelftext)
        self.selftextLst.addAction(self.actionDeleteSelftextandBlacklist)

        self.userSubredditLst.itemClicked.connect(self._switchModelObj)

        self._startingLstModelObj = startingLstModelObj
        self._model = model
        self._confirmDialog = confirmDialog
        self._saveState = saveState

        self._initUserSubredditLst()
        self._initContentLsts()

    def _initUserSubredditLst(self):
        for modelObj in self._model.stringsInLst:
            self.userSubredditLst.addItem(modelObj)
        self.userSubredditLst.setCurrentItem(self.userSubredditLst.findItems(self._startingLstModelObj.name, Qt.MatchExactly)[0])

    def _initContentLsts(self):
        downloadedContent = self._startingLstModelObj.redditSubmissions
        if downloadedContent is not None and len(downloadedContent) > 0:
            for submissionURL in downloadedContent:
                for submission in downloadedContent.get(submissionURL):
                    if submission.type is DownloadedContentType.JSON_DATA:
                        self._addToTab(submission, submissionURL, self.submissionJSONLst)
                    elif submission.type is DownloadedContentType.EXTERNAL_SUBMISSION_DATA:
                        self._addToTab(submission, submissionURL, self.submissionExternalLst)
                    elif submission.type is DownloadedContentType.EXTERNAL_COMMENT_DATA:
                        self._addToTab(submission, submissionURL, self.commentLst)
                    elif submission.type is DownloadedContentType.EXTERNAL_SELFTEXT_DATA:
                        self._addToTab(submission, submissionURL, self.selftextLst)
        else:
            QMessageBox.information(QMessageBox(), "Data Extractor for reddit",
                                    self._startingLstModelObj.name + " has no downloaded submissions. Download some by hitting the download button.")

    def _clearLsts(self):
        self.submissionJSONLst.clear()
        self.submissionExternalLst.clear()
        self.commentLst.clear()
        self.selftextLst.clear()

    def _switchModelObj(self, cur):
        self._clearLsts()
        self._startingLstModelObj = self._getCurrentLstModelObj()
        self._initContentLsts()

    def _addToTab(self, submission, submissionURL, lst):
        """
        Add a submission and its representative image to the lst under its tab.

        :type submission: praw.objects.Submission
        :type submissionURL: str
        :type lst: QListWidget
        """
        imagePath = submission.representativeImage
        if imagePath is not None and imagePath.exists():
            item = QListWidgetItem(submissionURL, lst)
            item.setTextColor(Qt.transparent)
            labelWidget = QLabel()
            labelWidget.setOpenExternalLinks(True)
            labelWidget.setTextFormat(Qt.RichText)
            size = QSize(128, 158)
            item.setSizeHint(size)
            size = QSize(128, 128)
            if imagePath.suffix == ".webm":
                imagePath = pathlib.Path("RedditDataExtractor", "images", "webmImage.png").resolve()
            pixmap = QPixmap(str(imagePath))
            pixmap = pixmap.scaled(size, Qt.KeepAspectRatio)
            height = pixmap.height()
            width = pixmap.width()
            submissionTitle = submissionURL[submissionURL[0:-1].rfind("/") + 1:-1]
            labelWidget.setText(
                '<a href="' + submissionURL + '"><img src="' + str(imagePath) + '" height="' + str(
                    height) + '" width="' + str(width) + '"><p>' + submissionTitle)
            lst.setItemWidget(item, labelWidget)

    def _getCurrentLstModelObj(self):
        currentLstModelObjName = self.userSubredditLst.currentItem().text()
        index = self._model.getIndexOfName(currentLstModelObjName)
        index = self._model.index(index, 0)
        currentLstModelObj = self._model.getObjectInLst(index)
        return currentLstModelObj

    def _getCurrentTabLstItem(self):
        currentTab = self.tabWidget.currentWidget()
        currentTabLst = currentTab.findChild(QListWidget)
        currentTabLstItem = currentTabLst.currentItem()
        return currentTabLstItem

    def _deleteContentAndBlacklist(self, downloadedContentType):
        """
        Delete the selected content and blacklist it so it is never downloaded again.

        :type downloadedContentType: RedditDataExtractor.downloader.DownloadedContentType
        """
        currentLstModelObj = self._getCurrentLstModelObj()
        currentTabLstItem = self._getCurrentTabLstItem()
        submissionURL = currentTabLstItem.text()

        deleted = self._deleteContent(downloadedContentType)
        if deleted:
            currentLstModelObj._blacklist.add(submissionURL)
            self._saveState()

    def _deleteContent(self, downloadedContentType):
        """
        Delete the selected content

        :type downloadedContentType: RedditDataExtractor.downloader.DownloadedContentType
        """
        currentLstModelObj = self._getCurrentLstModelObj()
        currentTab = self.tabWidget.currentWidget()
        currentTabLst = currentTab.findChild(QListWidget)
        currentTabLstItem = currentTabLst.currentItem()
        submissionURL = currentTabLstItem.text()

        downloadedContentForSubmission = currentLstModelObj.redditSubmissions.get(submissionURL)
        for content in downloadedContentForSubmission:
            if content.type == downloadedContentType:
                files = content.files
                numFiles = len(files)
                if numFiles <= 20: # avoid making a super long list that is hard to read
                    fileStr = "".join([str(file) + "\n" for file in files])
                else:
                    fileStr = "".join([str(file) + "\n" for file in files[:20]])
                    fileStr += "\n...\nand " + str(numFiles - 20) + " others. "
                msgBox = self._confirmDialog("This will delete these files: \n" + fileStr + "Are you sure you want to delete them?")
                ret = msgBox.exec_()
                if ret == QMessageBox.Yes:
                    downloadedContentForSubmission.remove(content)
                    if(len(downloadedContentForSubmission) <= 0):
                        del currentLstModelObj.redditSubmissions[submissionURL]
                    else:
                        currentLstModelObj.redditSubmissions[submissionURL] = downloadedContentForSubmission
                    if downloadedContentType is not DownloadedContentType.JSON_DATA:
                        for externalURL in content.externalDownloadURLs:
                            if externalURL in currentLstModelObj.externalDownloads:
                                currentLstModelObj.externalDownloads.remove(externalURL)
                    item = currentTabLst.takeItem(currentTabLst.currentRow())
                    del item # PyQt documentation says the item won't be garbage collected automatically after using takeItem()
                    content.deleteFiles()
                    del content
                    QMessageBox.information(QMessageBox(), "Data Extractor for reddit", "Successfully removed requested files.")
                    self._saveState()
                    return True
                return False
        return False
