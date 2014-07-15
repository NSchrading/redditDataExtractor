import sys
import os
import shelve

from PyQt4.Qt import *
from rddtScrape_auto import Ui_RddtScrapeMainWindow
from settingsGUI import SettingsGUI
from redditData import RedditData, DownloadType, ListType
from downloadedPostsGUI import DownloadedPostsGUI
from listModel import ListModel
from genericListModelObjects import GenericListModelObj, User, Subreddit
from GUIFuncs import confirmDialog
from queue import Queue
from downloader import Downloader

# A QObject (to be run in a QThread) which sits waiting for data to come through a Queue.Queue().
# It blocks until data is available, and one it has got something from the queue, it sends
# it to the "MainThread" by emitting a Qt Signal
class MyReceiver(QObject):
    mysignal = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, queue, *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.queue = queue
        self.continueOperation = True

    @pyqtSlot()
    def run(self):
        while(self.continueOperation):
            text = self.queue.get()
            self.mysignal.emit(text)
        self.finished.emit()

    def stop(self):
        self.continueOperation = False
        self.queue.put("") # wake up the queue (it blocks until it gets something)

class Validator(QObject):

    finished = pyqtSignal(list)
    invalid = pyqtSignal(str)

    def __init__(self, rddtScraper, queue, data, listType):
        super().__init__()
        self.rddtScraper = rddtScraper
        self.queue = queue
        self.data = data
        self.listType = listType

    @pyqtSlot()
    def run(self):
        valid = []
        if self.listType == ListType.USER:
            s = "user "
            validateFunc = self.rddtScraper.getRedditor
        else:
            s = "subreddit "
            validateFunc = self.rddtScraper.getSubreddit
        for d in self.data:
            name = d.name
            self.queue.put("Validating " + s + name + "\n")
            validatedData = validateFunc(name)
            if validatedData is None:
                self.invalid.emit(name)
                self.queue.put("Invalid " + s + "found: " + name + "\n")
            else:
                valid.append((d, validatedData))
        self.finished.emit(valid)

class listViewAndChooser(QListView):
    def __init__(self, parent, name, lstChooser, chooserDict, defaultLstName, rddtScraper, lstType, gui):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.setObjectName(name)
        self.lstChooser = lstChooser
        self.chooserDict = chooserDict
        self.rddtScraper = rddtScraper
        self.lstType = lstType
        if self.lstType == ListType.USER:
            self.classToUse = User
            self.rddtScraper.currentUserListName = defaultLstName
        elif self.lstType == ListType.SUBREDDIT:
            self.classToUse = Subreddit
            rddtScraper.currentSubredditListName = defaultLstName
        self.gui = gui

        for lstKey in self.chooserDict:
            print("Adding to chooser: " + str(lstKey))
            self.lstChooser.addItem(lstKey)
        print("default list: " + str(defaultLstName))
        model = chooserDict.get(defaultLstName)
        self.setModel(model)
        index = self.lstChooser.findText(defaultLstName)
        self.lstChooser.setCurrentIndex(index)

    def getCurrentSelectedIndex(self):
        # indices is a list of QModelIndex. Use selectedIndexes() rather than currentIndex() to make sure
        # something is actually selected. currentIndex() returns the top item if nothing is selected
        # - behavior we don't want.
        indices = self.selectedIndexes()
        index = None
        if len(indices) > 0:
            index = indices[0] # only one thing should be selectable at a time
        return index

    def addToList(self):
        model = self.model()
        if model is not None:
            model.insertRows(model.rowCount(), 1)
            self.gui.setUnsavedChanges(True)

    def deleteFromList(self):
        model = self.model()
        index = self.getCurrentSelectedIndex()
        if model is not None and index is not None:
            row = index.row()
            model.removeRows(row, 1)
            self.gui.setUnsavedChanges(True)

    def chooseNewList(self, listIndex):
        listName = self.lstChooser.itemText(listIndex)
        print("Choosing new list: " + listName)
        # I could pass in a function that changes these appropriately based off of type, but this works too I guess...
        # Kinda gross code. Oh well
        if self.lstType == ListType.USER:
            self.rddtScraper.currentUserListName = listName
        elif self.lstType == ListType.SUBREDDIT:
            self.rddtScraper.currentSubredditListName = listName
        else:
            return
        model = self.chooserDict.get(listName)
        self.setModel(model)

    def makeNewList(self):
        listName, okay = QInputDialog.getText(QInputDialog(), self.objectName().capitalize() + " List Name",
                                                       "New " + self.objectName().capitalize() + " List Name:",
                                                       QLineEdit.Normal, "New " + self.objectName().capitalize() + " List")
        if okay and len(listName) > 0:
            if any([listName in lst for lst in self.rddtScraper.subredditLists]):
                QMessageBox.information(QMessageBox(), "Reddit Scraper", "Duplicate subreddit list names not allowed.")
                return
            self.lstChooser.addItem(listName)
            self.lstChooser.setCurrentIndex(self.lstChooser.count() - 1)
            self.chooserDict[listName] = ListModel([], self.classToUse)
            self.chooseNewList(self.lstChooser.count() - 1)
            if self.rddtScraper.defaultSubredditListName is None:  # becomes None if user deletes all subreddit lists
                self.rddtScraper.defaultSubredditListName = listName
            self.gui.setUnsavedChanges(True)

    def removeNonDefaultLst(self):
        if self.lstType == ListType.USER:
            self.rddtScraper.currentUserListName = self.rddtScraper.defaultUserListName
            name = self.rddtScraper.currentUserListName
        elif self.lstType == ListType.SUBREDDIT:
            self.rddtScraper.currentSubredditListName = self.rddtScraper.defaultSubredditListName
            name = self.rddtScraper.currentSubredditListName
        else:
            return
        index = self.lstChooser.findText(name)
        self.lstChooser.setCurrentIndex(index)
        self.chooseNewList(index)

    def removeDefaultLst(self):
        modelName = list(self.chooserDict)[0]
        if self.lstType == ListType.USER:
            self.rddtScraper.currentUserListName = modelName
            self.rddtScraper.defaultUserListName = modelName
        elif self.lstType == ListType.SUBREDDIT:
            self.rddtScraper.currentSubredditListName = modelName
            self.rddtScraper.defaultSubredditListName = modelName
        else:
            return
        index = self.lstChooser.findText(modelName)
        self.lstChooser.setCurrentIndex(index)
        self.chooseNewList(index)

    def removeLastLst(self):
        print('deleting last list')
        if self.lstType == ListType.USER:
            self.rddtScraper.currentUserListName = None
            self.rddtScraper.defaultUserListName = None
        elif self.lstType == ListType.SUBREDDIT:
            self.rddtScraper.currentSubredditListName = None
            self.rddtScraper.defaultSubredditListName = None
        else:
            return
        self.setModel(ListModel([], GenericListModelObj))

    def removeLst(self):
        name = self.lstChooser.currentText()
        if len(name) <= 0:
            return
        msgBox = confirmDialog("Are you sure you want to delete the " + self.objectName() + " list: " + name + "?")
        ret = msgBox.exec_()
        if ret == QMessageBox.Yes:
            if len(self.chooserDict) <= 0:
                QMessageBox.information(QMessageBox(), "Reddit Scraper", "There are no more lists left to delete.")
                return
            self.lstChooser.removeItem(self.lstChooser.currentIndex())
            del self.chooserDict[name]
            # I could pass in a function that changes these appropriately based off of type, but this works too I guess...
            # Kinda gross code. Oh well
            if self.lstType == ListType.USER:
                defaultName = self.rddtScraper.defaultUserListName
            elif self.lstType == ListType.SUBREDDIT:
                defaultName = self.rddtScraper.defaultSubredditListName
            # if default is not being removed, just remove and switch to default
            if name != defaultName:
                self.removeNonDefaultLst()
            else:
                if len(self.chooserDict) > 0:
                    # just choose the first model
                    self.removeDefaultLst()
                else:
                    self.removeLastLst()
            self.gui.setUnsavedChanges(True)

    def viewDownloadedPosts(self):
        model = self.model()
        index = self.currentIndex()
        if model is not None and index is not None:
            selected = model.getObjectInLst(index)
            downloadedPosts = selected.redditPosts
            if downloadedPosts is not None and len(downloadedPosts) > 0:
                downloadedPostsGUI = DownloadedPostsGUI(selected, confirmDialog, self.gui.saveState)
                for postURL in downloadedPosts:
                    for post in downloadedPosts.get(postURL):
                        image = post.representativeImage
                        if image is None or not os.path.exists(image):
                            continue
                        item = QListWidgetItem("", downloadedPostsGUI.downloadedPostsList)
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
                        downloadedPostsGUI.downloadedPostsList.setItemWidget(item, labelWidget)
                        downloadedPostsGUI.posts.append((postURL, post.type))
                downloadedPostsGUI.exec_()
            else:
                QMessageBox.information(QMessageBox(), "Reddit Scraper",
                                        "The selected " + self.objectName() + " has no downloaded posts. Download some by hitting the download button.")
        elif index is None:
            QMessageBox.information(QMessageBox(), "Reddit Scraper",
                                    "To view a " + self.objectName() + "'s downloaded posts, please select a " + s  + " in the " + s + " list.")

class RddtScrapeGUI(QMainWindow, Ui_RddtScrapeMainWindow):
    def __init__(self, rddtScraper, queue, recv):
        QMainWindow.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.rddtScraper = rddtScraper

        self.currentSelectedUserText = ""
        self.currentSelectedSubredditText = ""

        self.unsavedChanges = False

        self.log = True

        self.queue = queue
        self.recv = recv

        # Custom Set ups
        self.setup()

    def setup(self):
        self.init()

        self.directoryBox.setText(self.rddtScraper.defaultPath)

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

        self.userListChooser.currentIndexChanged.connect(self.userList.chooseNewList)
        self.subredditListChooser.currentIndexChanged.connect(self.subredditList.chooseNewList)

        self.userList.addAction(self.actionDownloaded_Reddit_User_Posts)
        self.userList.addAction(self.actionNew_User)
        self.userList.addAction(self.actionRemove_Selected_User)
        self.actionDownloaded_Reddit_User_Posts.triggered.connect(self.userList.viewDownloadedPosts)
        self.actionNew_User.triggered.connect(self.userList.addToList)
        self.actionRemove_Selected_User.triggered.connect(self.userList.deleteFromList)

        self.subredditList.addAction(self.actionDownloaded_Subreddit_Posts)
        self.subredditList.addAction(self.actionNew_Subreddit)
        self.subredditList.addAction(self.actionRemove_Selected_Subreddit)
        self.actionDownloaded_Subreddit_Posts.triggered.connect(self.subredditList.viewDownloadedPosts)
        self.actionNew_Subreddit.triggered.connect(self.subredditList.addToList)
        self.actionRemove_Selected_Subreddit.triggered.connect(self.subredditList.deleteFromList)

        self.downloadBtn.clicked.connect(self.beginDownload)

        self.userSubBtn.clicked.connect(
            lambda: self.rddtScraper.changeDownloadType(DownloadType.USER_SUBREDDIT_CONSTRAINED))
        self.allUserBtn.clicked.connect(lambda: self.rddtScraper.changeDownloadType(DownloadType.USER_SUBREDDIT_ALL))
        self.allSubBtn.clicked.connect(lambda: self.rddtScraper.changeDownloadType(DownloadType.SUBREDDIT_CONTENT))

        self.actionAbout.triggered.connect(self.displayAbout)

    def initUserList(self):
        self.userList = listViewAndChooser(self.centralwidget, "user", self.userListChooser, self.rddtScraper.userLists, self.rddtScraper.defaultUserListName, self.rddtScraper, ListType.USER, self)
        self.gridLayout.addWidget(self.userList, 1, 0, 1, 1)

    def initSubredditList(self):
        self.subredditList = listViewAndChooser(self.centralwidget, "subreddit", self.subredditListChooser, self.rddtScraper.subredditLists, self.rddtScraper.defaultSubredditListName, self.rddtScraper, ListType.SUBREDDIT, self)
        self.gridLayout.addWidget(self.subredditList, 1, 1, 1, 1)

    def init(self):
        self.initUserList()
        self.initSubredditList()
        if(self.rddtScraper.downloadType == DownloadType.USER_SUBREDDIT_CONSTRAINED):
            self.userSubBtn.setChecked(True)
        elif(self.rddtScraper.downloadType == DownloadType.USER_SUBREDDIT_ALL):
            self.allUserBtn.setChecked(True)
        elif(self.rddtScraper.downloadType == DownloadType.SUBREDDIT_CONTENT):
            self.allSubBtn.setChecked(True)

    @pyqtSlot()
    def beginDownload(self):
        self.downloadBtn.setText("Downloading...")
        self.downloadBtn.setEnabled(False)
        self.logTextEdit.clear()
        if self.rddtScraper.downloadType == DownloadType.USER_SUBREDDIT_CONSTRAINED:
            # need to validate both subreddits and redditors, start downloading user data once done
            self.getValidSubreddits()
            self.getValidRedditors(startDownload=True)
        elif self.rddtScraper.downloadType == DownloadType.USER_SUBREDDIT_ALL:
            self.getValidRedditors(startDownload=True)
        elif self.rddtScraper.downloadType == DownloadType.SUBREDDIT_CONTENT:
            self.getValidSubreddits(startDownload=True)

    @pyqtSlot(list)
    def downloadValid(self, validData):
        if self.rddtScraper.downloadType == DownloadType.USER_SUBREDDIT_CONSTRAINED or self.rddtScraper.downloadType == DownloadType.USER_SUBREDDIT_ALL:
            self.downloader = Downloader(self.rddtScraper, validData, self.queue, ListType.USER)
        elif self.rddtScraper.downloadType == DownloadType.SUBREDDIT_CONTENT:
            self.downloader = Downloader(self.rddtScraper, validData, self.queue, ListType.SUBREDDIT)
        self.thread = QThread()
        self.downloader.moveToThread(self.thread)
        self.thread.started.connect(self.downloader.run)
        self.downloader.finished.connect(self.thread.quit)
        self.downloader.finished.connect(self.activateDownloadBtn)
        self.downloader.finished.connect(self.downloader.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    @pyqtSlot(str)
    def append_text(self, text):
        self.logTextEdit.moveCursor(QTextCursor.End)
        self.logTextEdit.insertPlainText(text)

    def activateDownloadBtn(self):
        self.downloadBtn.setText("Download!")
        self.downloadBtn.setEnabled(True)

    def getValidRedditors(self, startDownload=False):
        model = self.rddtScraper.userLists.get(self.rddtScraper.currentUserListName)
        print(self.rddtScraper.currentUserListName)
        users = set(model.lst)  # create a new set so we don't change set size during iteration if we remove a user
        # These are class variables so that they don't get destroyed when we return from getValidRedditors()
        self.redditorValidatorThread = QThread()
        self.redditorValidator = Validator(self.rddtScraper, self.queue, users, ListType.USER)
        self.redditorValidator.moveToThread(self.redditorValidatorThread)
        self.redditorValidatorThread.started.connect(self.redditorValidator.run)
        self.redditorValidator.invalid.connect(self.notifyInvalidRedditor)
        # When the validation finishes, start the downloading process on the validated users
        if startDownload:
            self.redditorValidator.finished.connect(self.downloadValid)
        self.redditorValidator.finished.connect(self.redditorValidatorThread.quit)
        self.redditorValidator.finished.connect(self.redditorValidator.deleteLater)
        self.redditorValidatorThread.finished.connect(self.redditorValidatorThread.deleteLater)
        self.redditorValidatorThread.start()

    @pyqtSlot(str)
    def notifyInvalidRedditor(self, userName):
        model = self.rddtScraper.userLists.get(self.rddtScraper.currentUserListName)
        msgBox = confirmDialog("The user " + userName + " does not exist. Remove from list?")
        ret = msgBox.exec_()
        if ret == QMessageBox.Yes:
            index = model.getIndexOfName(userName)
            if index != -1:
                model.removeRows(index, 1)

    def getValidSubreddits(self, startDownload=False):
        model = self.rddtScraper.subredditLists.get(self.rddtScraper.currentSubredditListName)
        subreddits = set(model.lst)
        self.subredditValidatorThread = QThread()
        self.subredditValidator = Validator(self.rddtScraper, self.queue, subreddits, ListType.SUBREDDIT)
        self.subredditValidator.moveToThread(self.subredditValidatorThread)
        self.subredditValidatorThread.started.connect(self.subredditValidator.run)
        self.subredditValidator.invalid.connect(self.notifyInvalidSubreddit)
        if startDownload:
            self.subredditValidator.finished.connect(self.downloadValid)
        self.subredditValidator.finished.connect(self.subredditValidatorThread.quit)
        self.subredditValidator.finished.connect(self.subredditValidator.deleteLater)
        self.subredditValidatorThread.finished.connect(self.subredditValidatorThread.deleteLater)
        self.subredditValidatorThread.start()

    @pyqtSlot(str)
    def notifyInvalidSubreddit(self, subredditName):
        model = self.rddtScraper.subredditLists.get(self.rddtScraper.currentSubredditListName)
        msgBox = confirmDialog("The subreddit " + subredditName + " does not exist. Remove from list?")
        ret = msgBox.exec_()
        if ret == QMessageBox.Yes:
            index = model.getIndexOfName(subredditName)
            if index != -1:
                model.removeRows(index, 1)

    def selectDirectory(self):
        directory = QFileDialog.getExistingDirectory(QFileDialog())
        if len(directory) > 0 and os.path.exists(directory):
            self.rddtScraper.defaultPath = directory
            self.directoryBox.setText(directory)
            self.setUnsavedChanges(True)

    def showSettings(self):
        settings = SettingsGUI(self.rddtScraper.userLists, self.rddtScraper.subredditLists,
                               self.rddtScraper.defaultUserListName, self.rddtScraper.defaultSubredditListName,
                               self.rddtScraper.avoidDuplicates, self.rddtScraper.getExternalContent, self.rddtScraper.getSubmissionContent,
                               self.rddtScraper.getCommentData, self.rddtScraper.subSort, self.rddtScraper.subLimit)
        ret = settings.exec_()
        if ret == QDialog.Accepted:
            self.logPrint(
                "Saving settings:\n" + str(settings.currentUserListName) + "\n" + str(
                    settings.currentSubredditListName))
            self.rddtScraper.defaultUserListName = settings.currentUserListName
            self.rddtScraper.defaultSubredditListName = settings.currentSubredditListName

            self.rddtScraper.avoidDuplicates = settings.avoidDuplicates
            self.rddtScraper.getExternalContent = settings.getExternalContent
            self.rddtScraper.getSubmissionContent = settings.getSubmissionContent
            self.rddtScraper.getCommentData = settings.getCommentData

            self.rddtScraper.subSort = settings.subSort
            self.rddtScraper.subLimit = settings.subLimit
            self.saveState()

    def displayAbout(self):
        msgBox = QMessageBox()
        msgBox.setTextFormat(Qt.RichText)
        msgBox.setWindowTitle("Reddit Scraper")
        msgBox.setText("""
            <p>This program uses the following open source software:<br>
            <a href="http://www.riverbankcomputing.co.uk/software/pyqt/intro">PyQt</a> under the GNU GPL v3 license
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
            <a href="https://www.gnu.org/licenses/quick-guide-gplv3.html">GNU GPL v3 license page</a>
            </p>
        """)
        msgBox.exec()


    def setUnsavedChanges(self, unsaved):
        self.unsavedChanges = unsaved
        if self.unsavedChanges:
            self.setWindowTitle("Reddit Scraper *")
        else:
            self.setWindowTitle("Reddit Scraper")

    def checkSaveState(self):
        close = False
        if self.unsavedChanges:
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
        self.logPrint("Attempting to close program.")
        close = self.checkSaveState()
        if close:
            self.recv.stop()
            self.logPrint("Closing program.")
            event.accept()
        else:
            self.logPrint("Ignoring close attempt.")
            event.ignore()

    def logPrint(self, s):
        if self.log:
            print(s)

    def saveState(self):
        successful = self.rddtScraper.saveState()
        self.setUnsavedChanges(not successful)


def loadState():
    print("attempting to load state")
    shelf = shelve.open("settings.db")
    rddtScraper = None
    try:
        rddtScraper = shelf['rddtScraper']
        userListSettings = shelf['userLists']
        subredditListSettings = shelf['subredditLists']
        rddtScraper.userLists = {}
        rddtScraper.subredditLists = {}
        for key, val in userListSettings.items():
            print("loading from saved " + key)
            rddtScraper.userLists[key] = ListModel(val, User)
        for key, val in subredditListSettings.items():
            print("loading from saved " + key)
            rddtScraper.subredditLists[key] = ListModel(val, Subreddit)
    except KeyError as e:
        print(e)
    finally:
        shelf.close()
        return rddtScraper

def main():
    a = QApplication(sys.argv)
    rddtScraper = loadState()
    if rddtScraper is None:
        print("rddt data client was None, making new one")
        rddtScraper = RedditData()
    queue = Queue()
    thread = QThread()
    recv = MyReceiver(queue)
    w = RddtScrapeGUI(rddtScraper, queue, recv)
    recv.mysignal.connect(w.append_text)
    recv.moveToThread(thread)
    thread.started.connect(recv.run)
    recv.finished.connect(thread.quit)
    recv.finished.connect(recv.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.start()

    w.show()

    sys.exit(a.exec_())


if __name__ == "__main__":
    main()