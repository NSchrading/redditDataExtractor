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

import requests
import pathlib

from PyQt4.Qt import (QInputDialog, QObject, pyqtSignal, pyqtSlot, QListView, Qt, QLineEdit, QMessageBox, QMainWindow,
                      QThread, QFileDialog, QTextCursor, QDialog, QIcon, QPixmap, QPushButton)

from .redditDataExtractorGUI_auto import Ui_RddtDataExtractorMainWindow
from .settingsGUI import SettingsGUI
from .CommonFuncs import confirmDialog, exceptionSafeJsonRequest
from .downloadedContentGUI import DownloadedContentGUI
from .listModel import ListModel
from .genericListModelObjects import GenericListModelObj, User, Subreddit
from .imgurClientIdGUI import ImgurClientIdGUI
from ..redditDataExtractor import DownloadType, ListType
from ..downloader import Downloader


def isNumber(s):
    """
    Determine if the passed in string is actually a number
    :type s: str
    :rtype: bool
    """
    try:
        float(s)
        return True
    except ValueError:
        return False


class Validator(QObject):
    finished = pyqtSignal()
    invalid = pyqtSignal(str)
    download = pyqtSignal(list)
    stopped = pyqtSignal()

    def __init__(self, rddtDataExtractor, queue, userOrSub, listType):
        """
        A class that, in a separate thread from the GUI, checks if the users / subreddits in the lists still exist
        or ever existed. Emits the invalid signal with the user / subreddit name if it finds an invalid user /
        subreddit.

        :type rddtDataExtractor: RedditDataExtractor.redditDataExtractor.RedditDataExtractor
        :type queue: Queue.queue
        :type userOrSub: set[RedditDataExtractor.GUI.genericListModelObjects.GenericListModelObj]
        :type listType: RedditDataExtractor.redditDataExtractor.ListType
        """
        super().__init__()
        self._rddtDataExtractor = rddtDataExtractor
        self._queue = queue
        self._userOrSub = userOrSub
        self._listType = listType
        self._continueOperation = True
        self.validUsersOrSubs = []

    def stop(self):
        self._continueOperation = False

    @pyqtSlot()
    def run(self):
        if self._listType is ListType.USER:
            s = "user "
            validateFunc = self._rddtDataExtractor.getRedditor
        else:
            s = "subreddit "
            validateFunc = self._rddtDataExtractor.getSubreddit
        for userOrSubLstModelObj in self._userOrSub:
            if self._continueOperation:
                name = userOrSubLstModelObj.name
                self._queue.put("Validating " + s + name + "\n")
                validatedPRAWUserOrSub = validateFunc(name)
                if validatedPRAWUserOrSub is None:
                    self.invalid.emit(name)
                else:
                    self.validUsersOrSubs.append((userOrSubLstModelObj, validatedPRAWUserOrSub))
            else:
                break
        if self._continueOperation:
            self.download.emit(self.validUsersOrSubs)  # emit to begin downloading the validated users
        else:
            self.stopped.emit()  # emit to indicate that the validation process was stopped prematurely
        self.finished.emit()  # emit to delete the ended thread


class ListViewAndChooser(QListView):
    def __init__(self, gui, lstChooser, chooserDict, defaultLstName, classToUse, name):
        """
        A class to hold the state of the combobox (list chooser) and the list view it is connected to
        :param lstChooser: The Combobox that holds the lists of users / subreddits to choose from
        :param chooserDict: The dictionary of key = name of listmodel, value = list of genericLstModelObj
        :type gui: RedditDataExtractor.GUI.redditDataExtractorGUI.RddtDataExtractorGUI
        :type lstChooser: Qt.QComboBox
        :type chooserDict: dict
        :type defaultLstName: str
        :type classToUse: function
        :type name: str
        """
        super().__init__(gui.centralwidget)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.setObjectName(name)
        self._lstChooser = lstChooser
        self._chooserDict = chooserDict
        self._defaultLstName = defaultLstName
        self._classToUse = classToUse
        self._gui = gui
        self._rddtDataExtractor = self._gui._rddtDataExtractor

        for lstKey in self._chooserDict:
            self._lstChooser.addItem(lstKey)
        model = chooserDict.get(defaultLstName)
        self.setModel(model)
        index = self._lstChooser.findText(defaultLstName)
        self._lstChooser.setCurrentIndex(index)

    def getCurrentSelectedIndex(self):
        """
        indices is a list of QModelIndex. Use selectedIndexes() rather than currentIndex() to make sure
        something is actually selected. currentIndex() returns the top item if nothing is selected
        - behavior we don't want.
        :rtype: QModelIndex
        """
        indices = self.selectedIndexes()
        index = None
        if len(indices) > 0:
            index = indices[0]  # only one thing should be selectable at a time
        return index

    def addToList(self):
        if self._rddtDataExtractor.currentlyDownloading:
            QMessageBox.warning(QMessageBox(), "Data Extractor for reddit",
                                "Cannot add while currently downloading. Please wait.")
            return
        model = self.model()
        if model is not None:
            model.insertRows(model.rowCount(), 1)
            self._gui.setUnsavedChanges(True)

    def deleteFromList(self):
        if self._rddtDataExtractor.currentlyDownloading:
            QMessageBox.warning(QMessageBox(), "Data Extractor for reddit",
                                "Cannot remove while currently downloading. Please wait.")
            return
        model = self.model()
        index = self.getCurrentSelectedIndex()
        if model is not None and index is not None:
            row = index.row()
            model.removeRows(row, 1)
            self._gui.setUnsavedChanges(True)

    def makeNewList(self):
        listName, okay = QInputDialog.getText(QInputDialog(), self.objectName().capitalize() + " List Name",
                                              "New " + self.objectName().capitalize() + " List Name:",
                                              QLineEdit.Normal, "New " + self.objectName().capitalize() + " List")
        if okay and len(listName) > 0:
            if any([listName in lst for lst in self._rddtDataExtractor.subredditLists]):
                QMessageBox.information(QMessageBox(), "Data Extractor for reddit",
                                        "Duplicate subreddit list names not allowed.")
                return
            self._lstChooser.addItem(listName)
            self._lstChooser.setCurrentIndex(self._lstChooser.count() - 1)
            self._chooserDict[listName] = ListModel([], self._classToUse)
            self.chooseNewList(self._lstChooser.count() - 1)
            if self._rddtDataExtractor.defaultSubredditListName is None:  # becomes None if user deletes all subreddit lists
                self._rddtDataExtractor.defaultSubredditListName = listName
            self._gui.setUnsavedChanges(True)

    def viewDownloadedContent(self):
        """
        Show the downloaded content dialog GUI for the selected user / subreddit
        """
        if self._rddtDataExtractor.currentlyDownloading:
            QMessageBox.warning(QMessageBox(), "Data Extractor for reddit",
                                "Cannot view downloads while currently downloading. Please wait.")
            return
        model = self.model()
        index = self.getCurrentSelectedIndex()
        if model is not None and index is not None:
            selected = model.getObjectInLst(index)
            downloadedContent = selected.redditSubmissions
            if downloadedContent is not None and len(downloadedContent) > 0:
                downloadedContentGUI = DownloadedContentGUI(selected, self.model(), confirmDialog, self._gui.saveState)
                downloadedContentGUI.exec_()
            else:
                QMessageBox.information(QMessageBox(), "Data Extractor for reddit",
                                        selected.name + " has no downloaded content. Download some by hitting the download button.")
        elif index is None:
            QMessageBox.information(QMessageBox(), "Data Extractor for reddit",
                                    "To view a " + self.objectName() + "'s downloaded content, please select a " + self.objectName() + " in the " + self.objectName() + " list.")


class UserListViewAndChooser(ListViewAndChooser):
    def __init__(self, gui):
        """
        Subclass of ListViewAndChooser specifically for a User View
        :type gui: RedditDataExtractor.GUI.redditDataExtractorGUI.RddtDataExtractorGUI
        """
        super().__init__(gui, gui.userListChooser, gui._rddtDataExtractor.userLists,
                         gui._rddtDataExtractor.defaultUserListName, User, "user")
        self._rddtDataExtractor.currentUserListName = self._defaultLstName

    def chooseNewList(self, listIndex):
        listName = self._lstChooser.itemText(listIndex)
        self._rddtDataExtractor.currentUserListName = listName
        model = self._chooserDict.get(listName)
        self.setModel(model)

    def removeNonDefaultLst(self):
        self._rddtDataExtractor.currentUserListName = self._rddtDataExtractor.defaultUserListName
        name = self._rddtDataExtractor.currentUserListName
        index = self._lstChooser.findText(name)
        self._lstChooser.setCurrentIndex(index)
        self.chooseNewList(index)

    def removeDefaultLst(self):
        modelName = list(self._chooserDict)[0]
        self._rddtDataExtractor.currentUserListName = modelName
        self._rddtDataExtractor.defaultUserListName = modelName
        index = self._lstChooser.findText(modelName)
        self._lstChooser.setCurrentIndex(index)
        self.chooseNewList(index)

    def removeLastLst(self):
        self._rddtDataExtractor.currentUserListName = None
        self._rddtDataExtractor.defaultUserListName = None
        self.setModel(ListModel([], GenericListModelObj))

    def removeLst(self):
        name = self._lstChooser.currentText()
        if len(name) <= 0:
            return
        msgBox = confirmDialog("Are you sure you want to delete the " + self.objectName() + " list: " + name + "?")
        ret = msgBox.exec_()
        if ret == QMessageBox.Yes:
            if len(self._chooserDict) <= 0:
                QMessageBox.information(QMessageBox(), "Data Extractor for reddit",
                                        "There are no more lists left to delete.")
                return
            self._lstChooser.removeItem(self._lstChooser.currentIndex())
            del self._chooserDict[name]
            defaultName = self._rddtDataExtractor.defaultUserListName
            # if default is not being removed, just remove and switch to default
            if name != defaultName:
                self.removeNonDefaultLst()
            else:
                if len(self._chooserDict) > 0:
                    # just choose the first model
                    self.removeDefaultLst()
                else:
                    self.removeLastLst()
            self._gui.setUnsavedChanges(True)


class SubredditListViewAndChooser(ListViewAndChooser):
    def __init__(self, gui):
        """
        Subclass of ListViewAndChooser specifically for a Subreddit View
        :type gui: RedditDataExtractor.GUI.redditDataExtractorGUI.RddtDataExtractorGUI
        """
        super().__init__(gui, gui.subredditListChooser, gui._rddtDataExtractor.subredditLists,
                         gui._rddtDataExtractor.defaultSubredditListName, Subreddit, "subreddit")
        self._rddtDataExtractor.currentSubredditListName = self._defaultLstName

    def chooseNewList(self, listIndex):
        listName = self._lstChooser.itemText(listIndex)
        self._rddtDataExtractor.currentSubredditListName = listName
        model = self._chooserDict.get(listName)
        self.setModel(model)

    def removeNonDefaultLst(self):
        self._rddtDataExtractor.currentSubredditListName = self._rddtDataExtractor.defaultSubredditListName
        name = self._rddtDataExtractor.currentSubredditListName
        index = self._lstChooser.findText(name)
        self._lstChooser.setCurrentIndex(index)
        self.chooseNewList(index)

    def removeDefaultLst(self):
        modelName = list(self._chooserDict)[0]
        self._rddtDataExtractor.currentSubredditListName = modelName
        self._rddtDataExtractor.defaultSubredditListName = modelName
        index = self._lstChooser.findText(modelName)
        self._lstChooser.setCurrentIndex(index)
        self.chooseNewList(index)

    def removeLastLst(self):
        self._rddtDataExtractor.currentSubredditListName = None
        self._rddtDataExtractor.defaultSubredditListName = None
        self.setModel(ListModel([], GenericListModelObj))

    def removeLst(self):
        name = self._lstChooser.currentText()
        if len(name) <= 0:
            return
        msgBox = confirmDialog("Are you sure you want to delete the " + self.objectName() + " list: " + name + "?")
        ret = msgBox.exec_()
        if ret == QMessageBox.Yes:
            if len(self._chooserDict) <= 0:
                QMessageBox.information(QMessageBox(), "Data Extractor for reddit",
                                        "There are no more lists left to delete.")
                return
            self._lstChooser.removeItem(self._lstChooser.currentIndex())
            del self._chooserDict[name]
            defaultName = self._rddtDataExtractor.defaultSubredditListName
            # if default is not being removed, just remove and switch to default
            if name != defaultName:
                self.removeNonDefaultLst()
            else:
                if len(self._chooserDict) > 0:
                    # just choose the first model
                    self.removeDefaultLst()
                else:
                    self.removeLastLst()
            self._gui.setUnsavedChanges(True)


class RddtDataExtractorGUI(QMainWindow, Ui_RddtDataExtractorMainWindow):
    def __init__(self, rddtDataExtractor, queue, recv):
        """
        Main GUI Window that the user interacts with.
        :type rddtDataExtractor: RedditDataExtractor.redditDataExtractor.RedditDataExtractor
        :type queue: Queue.queue
        :type recv: RedditDataExtractor.main.QueueMessageReceiver
        """
        QMainWindow.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        # The model for the view
        self._rddtDataExtractor = rddtDataExtractor

        # Bool to keep track of changes that have occurred that haven't been saved
        self._unsavedChanges = False

        self.queue = queue
        self.recv = recv

        # Custom Set ups
        self.setup()

    def setup(self):
        self.init()

        self.directoryBox.setText(str(self._rddtDataExtractor.defaultPath))

        self.directorySelectBtn.clicked.connect(self.selectDirectory)
        self.addUserBtn.clicked.connect(self.userList.addToList)
        self.addSubredditBtn.clicked.connect(self.subredditList.addToList)

        self.deleteUserBtn.clicked.connect(self.userList.deleteFromList)
        self.deleteSubredditBtn.clicked.connect(self.subredditList.deleteFromList)

        self.actionSettings_2.triggered.connect(self.showSettings)
        self.actionExit.triggered.connect(self.close)
        self.actionSubreddit_List.triggered.connect(self.subredditList.makeNewList)
        self.actionUser_List.triggered.connect(self.userList.makeNewList)
        self.actionSave.triggered.connect(self.saveState)

        self.actionRemove_Subreddit_List.triggered.connect(self.subredditList.removeLst)
        self.actionRemove_User_List.triggered.connect(self.userList.removeLst)

        self.userListChooser.addAction(self.actionUser_List)
        self.subredditListChooser.addAction(self.actionSubreddit_List)
        self.userListChooser.addAction(self.actionRemove_User_List)
        self.subredditListChooser.addAction(self.actionRemove_Subreddit_List)

        self.userListChooser.activated.connect(self.userList.chooseNewList)
        self.subredditListChooser.activated.connect(self.subredditList.chooseNewList)

        self.userList.addAction(self.actionDownloaded_Reddit_User_Posts)
        self.userList.addAction(self.actionNew_User)
        self.userList.addAction(self.actionRemove_Selected_User)
        self.actionDownloaded_Reddit_User_Posts.triggered.connect(self.userList.viewDownloadedContent)
        self.actionNew_User.triggered.connect(self.userList.addToList)
        self.actionRemove_Selected_User.triggered.connect(self.userList.deleteFromList)

        self.subredditList.addAction(self.actionDownloaded_Subreddit_Posts)
        self.subredditList.addAction(self.actionNew_Subreddit)
        self.subredditList.addAction(self.actionRemove_Selected_Subreddit)
        self.actionDownloaded_Subreddit_Posts.triggered.connect(self.subredditList.viewDownloadedContent)
        self.actionNew_Subreddit.triggered.connect(self.subredditList.addToList)
        self.actionRemove_Selected_Subreddit.triggered.connect(self.subredditList.deleteFromList)

        self.actionRemaining_Imgur_Requests.triggered.connect(self.viewRemainingImgurRequests)

        self.downloadBtn.clicked.connect(self.beginDownload)

        self.userSubBtn.clicked.connect(
            lambda: self._rddtDataExtractor.changeDownloadType(DownloadType.USER_SUBREDDIT_CONSTRAINED))
        self.allUserBtn.clicked.connect(
            lambda: self._rddtDataExtractor.changeDownloadType(DownloadType.USER_SUBREDDIT_ALL))
        self.allSubBtn.clicked.connect(
            lambda: self._rddtDataExtractor.changeDownloadType(DownloadType.SUBREDDIT_CONTENT))

        self.actionAbout.triggered.connect(self.displayAbout)

    def initUserList(self):
        self.userList = UserListViewAndChooser(self)
        self.gridLayout.addWidget(self.userList, 1, 0, 1, 1)

    def initSubredditList(self):
        self.subredditList = SubredditListViewAndChooser(self)
        self.gridLayout.addWidget(self.subredditList, 1, 1, 1, 1)

    def init(self):
        self.initUserList()
        self.initSubredditList()
        if (self._rddtDataExtractor.downloadType is DownloadType.USER_SUBREDDIT_CONSTRAINED):
            self.userSubBtn.setChecked(True)
        elif (self._rddtDataExtractor.downloadType is DownloadType.USER_SUBREDDIT_ALL):
            self.allUserBtn.setChecked(True)
        elif (self._rddtDataExtractor.downloadType is DownloadType.SUBREDDIT_CONTENT):
            self.allSubBtn.setChecked(True)
        icon = QIcon()
        icon.addPixmap(QPixmap("RedditDataExtractor/images/logo.png"), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

    def stopDownload(self):
        try:
            self.redditorValidator.stop()
        except AttributeError:  # the redditorValidator object hasn't been made
            pass
        try:
            self.subredditValidator.stop()
        except AttributeError:  # the subredditValidator object hasn't been made
            pass
        try:
            self.downloader.stop()
        except AttributeError:  # the downloader object hasn't been made
            pass
        # Try to save the current downloads, just in case it never stops the download (rare cases of network problems)
        self._rddtDataExtractor.currentlyDownloading = False
        self._rddtDataExtractor.saveState()
        self._rddtDataExtractor.currentlyDownloading = True
        self.stopBtn.setEnabled(False)

    @pyqtSlot()
    def reactivateBtns(self):
        try:
            self.gridLayout.removeWidget(self.stopBtn)
            self.stopBtn.deleteLater()
        except:
            pass
        self.downloadBtn = QPushButton(self.centralwidget)
        self.downloadBtn.setObjectName("downloadBtn")
        self.downloadBtn.setText("Download!")
        self.downloadBtn.clicked.connect(self.beginDownload)
        self.gridLayout.addWidget(self.downloadBtn, 6, 0, 1, 2)
        self.addUserBtn.setEnabled(True)
        self.addSubredditBtn.setEnabled(True)
        self.deleteUserBtn.setEnabled(True)
        self.deleteSubredditBtn.setEnabled(True)
        self._rddtDataExtractor.currentlyDownloading = False

    def enterDownloadMode(self):
        self._rddtDataExtractor.currentlyDownloading = True
        self.logTextEdit.clear()
        self.stopBtn = QPushButton(self.centralwidget)
        self.stopBtn.setObjectName("stopBtn")
        self.stopBtn.setText("Downloading... Press here to stop the download (In progress downloads will continue until done).")
        self.stopBtn.clicked.connect(self.stopDownload)
        try:
            self.gridLayout.removeWidget(self.downloadBtn)
            self.downloadBtn.deleteLater()
        except:
            pass
        self.gridLayout.addWidget(self.stopBtn, 6, 0, 1, 2)
        self.addUserBtn.setEnabled(False)
        self.addSubredditBtn.setEnabled(False)
        self.deleteUserBtn.setEnabled(False)
        self.deleteSubredditBtn.setEnabled(False)

    @pyqtSlot()
    def beginDownload(self):
        self.enterDownloadMode()
        if self._rddtDataExtractor.downloadType is DownloadType.USER_SUBREDDIT_CONSTRAINED:
            # need to validate both subreddits and redditors, start downloading user data once done
            self.getValidSubreddits()
            self.getValidRedditors(startDownload=True)
        elif self._rddtDataExtractor.downloadType is DownloadType.USER_SUBREDDIT_ALL:
            self.getValidRedditors(startDownload=True)
        elif self._rddtDataExtractor.downloadType is DownloadType.SUBREDDIT_CONTENT:
            self.getValidSubreddits(startDownload=True)

    @pyqtSlot(list)
    def downloadValidUserOrSub(self, validUsersOrSubs):
        """
        Begin the download process for the validated users or subreddits
        :type validUsersOrSubs: list
        """
        if self._rddtDataExtractor.downloadType is DownloadType.USER_SUBREDDIT_CONSTRAINED or self._rddtDataExtractor.downloadType is DownloadType.USER_SUBREDDIT_ALL:
            self.downloader = Downloader(self._rddtDataExtractor, validUsersOrSubs, self.queue, ListType.USER)
        elif self._rddtDataExtractor.downloadType is DownloadType.SUBREDDIT_CONTENT:
            self.downloader = Downloader(self._rddtDataExtractor, validUsersOrSubs, self.queue, ListType.SUBREDDIT)
        self.thread = QThread()
        self.downloader.moveToThread(self.thread)
        self.thread.started.connect(self.downloader.run)
        self.downloader.finished.connect(self.thread.quit)
        self.downloader.finished.connect(self.reactivateBtns)
        self.downloader.finished.connect(self.downloader.deleteLater)
        self.downloader.finished.connect(lambda: self.setUnsavedChanges(True))
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    @pyqtSlot(str)
    def append_text(self, text):
        """
        Add text to the text area in the GUI, sent by the Receiver thread that picks up messages from other threads
        :type text: str
        """
        self.logTextEdit.moveCursor(QTextCursor.End)
        self.logTextEdit.insertPlainText(text)

    def getValidRedditors(self, startDownload=False):
        """
        Validate the users in the user list
        :param startDownload: Indicates whether or not the download should start when the validation is done
        :type startDownload: bool
        """
        model = self.userList.model()
        users = set(model.lst)  # create a new set so we don't change set size during iteration if we remove a user
        # These are class variables so that they don't get destroyed when we return from getValidRedditors()
        self.redditorValidatorThread = QThread()
        self.redditorValidator = Validator(self._rddtDataExtractor, self.queue, users, ListType.USER)
        self.redditorValidator.moveToThread(self.redditorValidatorThread)
        self.redditorValidatorThread.started.connect(self.redditorValidator.run)
        self.redditorValidator.invalid.connect(self.notifyInvalidRedditor)
        # When the validation finishes, start the downloading process on the validated users
        if startDownload:
            self.redditorValidator.download.connect(self.downloadValidUserOrSub)
        self.redditorValidator.finished.connect(self.redditorValidatorThread.quit)
        self.redditorValidator.finished.connect(self.redditorValidator.deleteLater)
        self.redditorValidatorThread.finished.connect(self.redditorValidatorThread.deleteLater)
        self.redditorValidator.stopped.connect(self.reactivateBtns)
        self.redditorValidatorThread.start()

    @pyqtSlot(str)
    def notifyInvalidRedditor(self, userName):
        """
        Ask the user if we should delete the redditor
        :type userName: str
        """
        model = self.userList.model()
        msgBox = confirmDialog("The user " + userName + " does not exist. Remove from list?")
        ret = msgBox.exec_()
        if ret == QMessageBox.Yes:
            index = model.getIndexOfName(userName)
            if index != -1:
                model.removeRows(index, 1)

    def getValidSubreddits(self, startDownload=False):
        """
        Validate the subreddits in the subreddit list
        :param startDownload: Indicates whether or not the download should start when the validation is done
        :type startDownload: bool
        """
        model = self.subredditList.model()
        subreddits = set(model.lst)
        self.subredditValidatorThread = QThread()
        self.subredditValidator = Validator(self._rddtDataExtractor, self.queue, subreddits, ListType.SUBREDDIT)
        self.subredditValidator.moveToThread(self.subredditValidatorThread)
        self.subredditValidatorThread.started.connect(self.subredditValidator.run)
        self.subredditValidator.invalid.connect(self.notifyInvalidSubreddit)
        if startDownload:
            self.subredditValidator.download.connect(self.downloadValidUserOrSub)
        self.subredditValidator.finished.connect(self.subredditValidatorThread.quit)
        self.subredditValidator.finished.connect(self.subredditValidator.deleteLater)
        self.subredditValidatorThread.finished.connect(self.subredditValidatorThread.deleteLater)
        self.subredditValidator.stopped.connect(self.reactivateBtns)
        self.subredditValidatorThread.start()

    @pyqtSlot(str)
    def notifyInvalidSubreddit(self, subredditName):
        """
        Ask the user if we should delete the redditor
        :type userName: str
        """
        model = self.subredditList.model()
        msgBox = confirmDialog("The subreddit " + subredditName + " does not exist. Remove from list?")
        ret = msgBox.exec_()
        if ret == QMessageBox.Yes:
            index = model.getIndexOfName(subredditName)
            if index != -1:
                model.removeRows(index, 1)

    def selectDirectory(self):
        directory = QFileDialog.getExistingDirectory(QFileDialog())
        if len(directory) > 0:
            directory = pathlib.Path(directory).resolve()
            if directory.exists():
                self._rddtDataExtractor.defaultPath = directory
                self.directoryBox.setText(str(directory))
                self.setUnsavedChanges(True)

    def convertFilterTableToFilters(self, settings):
        """
        Take the filter table settings from the settings GUI and convert them into
        actionable filter functions and parameters that _submissionPassesFilter() can use
        :type settings: RedditDataExtractor.GUI.settingsGUI.SettingsGUI
        """
        filterTable = settings.filterTable
        submissionFilts = []
        commentFilts = []
        connector = None
        if filterTable.rowCount() > 0:
            connectorWidget = filterTable.cellWidget(0, settings.filtTableConnectCol)
            if connectorWidget is not None:
                connector = self._rddtDataExtractor.mapConnectorTextToOper(connectorWidget.currentText())
            else:
                connector = None  # We are just filtering by a single thing
            for row in range(filterTable.rowCount()):
                type = filterTable.cellWidget(row, settings.filtTableTypeCol).currentText()
                prop = filterTable.cellWidget(row, settings.filtTablePropCol).currentText()
                oper = self._rddtDataExtractor.mapFilterTextToOper(
                    filterTable.cellWidget(row, settings.filtTableOperCol).currentText())
                val = filterTable.cellWidget(row, settings.filtTableValCol).toPlainText()
                if val.lower() == "false":
                    val = False
                elif val.lower() == "true":
                    val = True
                elif isNumber(val):
                    val = float(val)
                filt = (prop, oper, val)
                if type == "Submission":
                    submissionFilts.append(filt)
                elif type == "Comment":
                    commentFilts.append(filt)
        return submissionFilts, commentFilts, connector

    def showSettings(self):
        settings = SettingsGUI(self._rddtDataExtractor, self.notifyImgurAPI)
        ret = settings.exec_()
        if ret == QDialog.Accepted:
            self._rddtDataExtractor.defaultUserListName = settings.currentUserListName
            self._rddtDataExtractor.defaultSubredditListName = settings.currentSubredditListName

            self._rddtDataExtractor.avoidDuplicates = settings.avoidDuplicates
            self._rddtDataExtractor.getExternalContent = settings.getExternalContent
            self._rddtDataExtractor.getCommentExternalContent = settings.getCommentExternalContent
            self._rddtDataExtractor.getSelftextExternalContent = settings.getSelftextExternalContent
            self._rddtDataExtractor.getSubmissionContent = settings.getSubmissionContent

            self._rddtDataExtractor.subSort = settings.subSort
            self._rddtDataExtractor.subLimit = settings.subLimit
            self._rddtDataExtractor.filterExternalContent = settings.filterExternalContent
            self._rddtDataExtractor.filterSubmissionContent = settings.filterSubmissionContent
            if settings.filterExternalContent or settings.filterSubmissionContent:
                self._rddtDataExtractor.submissionFilts, self._rddtDataExtractor.commentFilts, self._rddtDataExtractor.connector = self.convertFilterTableToFilters(
                    settings)
            self._rddtDataExtractor.restrictDownloadsByCreationDate = settings.restrictDownloadsByCreationDate
            self._rddtDataExtractor.showImgurAPINotification = settings.showImgurAPINotification
            self._rddtDataExtractor.avoidVideos = settings.avoidVideos
            self._rddtDataExtractor.getAuthorsCommentsOnly = settings.getAuthorsCommentsOnly
            self.saveState()

    def notifyImgurAPI(self):
        self._rddtDataExtractor.imgurAPIClientID = None
        imgurClientIdGUI = ImgurClientIdGUI()
        ret = imgurClientIdGUI.exec_()
        if ret == QDialog.Accepted:
            self._rddtDataExtractor.imgurAPIClientID = imgurClientIdGUI.imgurAPIClientID
            self._rddtDataExtractor.saveState()

    def displayAbout(self):
        msgBox = QMessageBox()
        msgBox.setTextFormat(Qt.RichText)
        msgBox.setWindowTitle("Data Extractor for reddit")
        msgBox.setText("""
            <p>This program uses the following open source software:<br>
            <a href="http://www.riverbankcomputing.co.uk/software/pyqt/intro">PyQt</a> under the GNU GPL v3 license
            <br>
            <a href="https://praw.readthedocs.org/en/v2.1.16/">PRAW (Python Reddit API Wrapper)</a> under the GNU GPL v3 license
            <br>
            <a href="http://docs.python-requests.org/en/latest/">Requests</a> under the Apache2 license
            <br>
            <a href="http://www.crummy.com/software/BeautifulSoup/">Beautiful Soup</a> under a simplified BSD licence
            <br>
            <a href="https://github.com/rg3/youtube-dl">youtube-dl</a> under an unlicense (public domain)
            </p>

            <p>This program makes use of a modified version of <a href="https://www.videolan.org/vlc/">VLC's</a> logo:<br>
            Copyright (c) 1996-2013 VideoLAN. This logo or a modified version may<br>
            be used or modified by anyone to refer to the VideoLAN project or any<br>
            product developed by the VideoLAN team, but does not indicate<br>
            endorsement by the project.
            </p>

            <p>This program makes use of a modified version of Microsoft Window's<br>
            .txt file icon. This is solely the property of Microsoft Windows<br>
            and I claim no ownership.
            </p>

            <p>This program is released under the GNU GPL v3 license<br>
            <a href="https://www.gnu.org/licenses/quick-guide-gplv3.html">GNU GPL v3 license page</a><br>
            See <a href="https://github.com/NSchrading/redditDataExtractor/blob/master/LICENSE.txt">LICENSE.txt</a> for more information.
            </p>
        """)
        msgBox.exec()

    def viewRemainingImgurRequests(self):
        msgBox = QMessageBox()
        msgBox.setWindowTitle("Data Extractor for reddit")
        if self._rddtDataExtractor.imgurAPIClientID is not None:
            headers = {'Authorization': 'Client-ID ' + self._rddtDataExtractor.imgurAPIClientID}
            apiURL = "https://api.imgur.com/3/credits"
            requestsSession = requests.session()
            requestsSession.headers[
                'User-Agent'] = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'
            json = exceptionSafeJsonRequest(requestsSession, apiURL, headers=headers, stream=True,
                                            verify='RedditDataExtractor/cacert.pem')
            if json is not None and json.get('data') is not None and json.get('data').get('ClientRemaining'):
                msgBox.setText("You have " + str(json.get('data').get('ClientRemaining')) + " requests remaining.")
            else:
                msgBox.setText(
                    "A problem occurred using the Imgur API. Check that you are connected to the internet and make sure your client-id is correct.")
        else:
            msgBox.setText(
                "You do not currently have an Imgur client-id set. To set one, go to settings and check 'Change / Reset Client-id'")
        msgBox.exec()

    def setUnsavedChanges(self, unsaved):
        """
        If there are unsaved changes, indicate to the user by adding an asterisk to the window title
        """
        self._unsavedChanges = unsaved
        if self._unsavedChanges:
            self.setWindowTitle("Data Extractor for reddit *")
        else:
            self.setWindowTitle("Data Extractor for reddit")

    def checkSaveState(self):
        close = False
        if self._unsavedChanges:
            msgBox = QMessageBox()
            msgBox.setText("A list or setting has been changed.")
            msgBox.setInformativeText("Do you want to save your changes?")
            msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            msgBox.setDefaultButton(QMessageBox.Save)
            ret = msgBox.exec_()
            if ret == QMessageBox.Save:
                self.saveState()
                close = True
            elif ret == QMessageBox.Discard:
                close = True
            elif ret == QMessageBox.Cancel:
                close = False
            else:
                close = False
        else:
            close = True
        return close

    def closeEvent(self, event):
        """
        If there are unsaved changes, let the user know before closing the window
        """
        close = self.checkSaveState()
        if close:
            self.recv.stop()
            event.accept()
        else:
            event.ignore()

    def saveState(self):
        successful = self._rddtDataExtractor.saveState()
        self.setUnsavedChanges(not successful)