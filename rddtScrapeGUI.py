import sys
import os
import shelve

from PyQt4.Qt import *
from rddtScrape_auto import Ui_RddtScrapeMainWindow
from settingsGUI import SettingsGUI
from redditData import RedditData, DownloadType
from downloadedUserPostsGUI import DownloadedUserPostsGUI
from listModel import ListModel
from genericListModelObjects import GenericListModelObj, User
from GUIFuncs import confirmDialog
from queue import Queue
from downloader import Downloader

class ListType():
    USER = 1
    SUBREDDIT = 2


# A QObject (to be run in a QThread) which sits waiting for data to come through a Queue.Queue().
# It blocks until data is available, and one it has got something from the queue, it sends
# it to the "MainThread" by emitting a Qt Signal
class MyReceiver(QObject):
    mysignal = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self,queue,*args,**kwargs):
        QObject.__init__(self,*args,**kwargs)
        self.queue = queue

    @pyqtSlot()
    def run(self):
        while True:
            text = self.queue.get()
            self.mysignal.emit(text)


class RddtScrapeGUI(QMainWindow, Ui_RddtScrapeMainWindow):
    def __init__(self, rddtScraper, queue):
        QMainWindow.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.rddtScraper = rddtScraper

        self.currentSelectedUserText = ""
        self.currentSelectedSubredditText = ""

        self.unsavedChanges = False

        self.log = True

        self.queue = queue

        # Custom Set ups
        self.setup()

    def setup(self):

        self.directoryBox.setText(self.rddtScraper.defaultPath)

        self.directorySelectBtn.clicked.connect(self.selectDirectory)
        self.addUserBtn.clicked.connect(self.addUserToList)
        self.addSubredditBtn.clicked.connect(self.addSubredditToList)

        self.deleteUserBtn.clicked.connect(self.deleteUserFromList)
        self.deleteSubredditBtn.clicked.connect(self.deleteSubredditFromList)

        self.actionSettings_2.triggered.connect(self.showSettings)
        self.actionExit.triggered.connect(self.close)
        self.actionSubreddit_List.triggered.connect(self.makeNewSubredditList)
        self.actionUser_List.triggered.connect(self.makeNewUserList)
        self.actionSave.triggered.connect(self.saveState)

        self.actionRemove_Subreddit_List.triggered.connect(lambda: self.removeLst(ListType.SUBREDDIT))
        self.actionRemove_User_List.triggered.connect(lambda: self.removeLst(ListType.USER))

        self.userListChooser.addAction(self.actionUser_List)
        self.subredditListChooser.addAction(self.actionSubreddit_List)
        self.userListChooser.addAction(self.actionRemove_User_List)
        self.subredditListChooser.addAction(self.actionRemove_Subreddit_List)

        self.userListChooser.activated.connect(self.chooseNewUserList)
        self.subredditListChooser.activated.connect(self.chooseNewSubredditList)

        self.userList.addAction(self.actionDownloaded_Reddit_User_Posts)
        self.actionDownloaded_Reddit_User_Posts.triggered.connect(self.viewDownloadedUserPosts)

        self.downloadBtn.clicked.connect(self.download)

        self.userSubBtn.clicked.connect(lambda: self.rddtScraper.changeDownloadType(DownloadType.USER_SUBREDDIT_CONSTRAINED))
        self.allUserBtn.clicked.connect(lambda: self.rddtScraper.changeDownloadType(DownloadType.USER_SUBREDDIT_ALL))
        self.allSubBtn.clicked.connect(lambda: self.rddtScraper.changeDownloadType(DownloadType.SUBREDDIT_FRONTPAGE))

        self.init()

    def initUserList(self):
        for userListKey in self.rddtScraper.userLists:
            self.logPrint("Adding user list: " + str(userListKey))
            self.userListChooser.addItem(userListKey)
        print("default user list: " + str(self.rddtScraper.defaultUserListName))
        model = self.rddtScraper.userLists.get(self.rddtScraper.defaultUserListName)
        self.userList.setModel(model)
        index = self.userListChooser.findText(self.rddtScraper.defaultUserListName)
        self.userListChooser.setCurrentIndex(index)
        self.rddtScraper.currentUserListName = self.rddtScraper.defaultUserListName

    def initSubredditList(self):
        for subredditListKey in self.rddtScraper.subredditLists:
            self.logPrint("Adding subreddit list: " + str(subredditListKey))
            self.subredditListChooser.addItem(subredditListKey)
        print("default subreddit list: " + str(self.rddtScraper.defaultSubredditListName))
        model = self.rddtScraper.subredditLists.get(self.rddtScraper.defaultSubredditListName)
        self.subredditList.setModel(model)
        index = self.subredditListChooser.findText(self.rddtScraper.defaultSubredditListName)
        self.subredditListChooser.setCurrentIndex(index)
        self.rddtScraper.currentSubredditListName = self.rddtScraper.defaultSubredditListName

    def init(self):
        self.initUserList()
        self.initSubredditList()

    @pyqtSlot()
    def download(self):
        self.downloadBtn.setText("Downloading...")
        self.downloadBtn.setEnabled(False)
        self.logTextEdit.clear()
        self.thread = QThread()
        self.downloader = Downloader(self.rddtScraper, self.queue)
        self.downloader.moveToThread(self.thread)
        self.thread.started.connect(self.downloader.run)
        self.downloader.finished.connect(self.thread.quit)
        self.downloader.finished.connect(self.activateDownloadBtn)
        self.downloader.finished.connect(self.downloader.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    @pyqtSlot(str)
    def append_text(self,text):
        self.logTextEdit.moveCursor(QTextCursor.End)
        self.logTextEdit.insertPlainText( text )

    def activateDownloadBtn(self):
        self.downloadBtn.setText("Download!")
        self.downloadBtn.setEnabled(True)

    def selectDirectory(self):
        directory = QFileDialog.getExistingDirectory(QFileDialog())
        if len(directory) > 0 and os.path.exists(directory):
            self.rddtScraper.defaultPath = directory
            self.directoryBox.setText(directory)
            self.setUnsavedChanges(True)

    def addUserToList(self):
        model = self.rddtScraper.userLists.get(self.rddtScraper.currentUserListName)
        if model is not None:
            model.insertRows(model.rowCount(), 1)
            self.setUnsavedChanges(True)

    def addSubredditToList(self):
        model = self.rddtScraper.subredditLists.get(self.rddtScraper.currentSubredditListName)
        if model is not None:
            model.insertRows(model.rowCount(), 1)
            self.setUnsavedChanges(True)

    def deleteUserFromList(self):
        model = self.rddtScraper.userLists.get(self.rddtScraper.currentUserListName)
        indices = self.userList.selectedIndexes()  # indices is a list of QModelIndex
        index = None
        if len(indices) > 0:
            index = indices[0].row()  # only one thing should be selectable at a time
        if model is not None and index is not None:
            model.removeRows(index, 1)
            self.setUnsavedChanges(True)

    def deleteSubredditFromList(self):
        model = self.rddtScraper.subredditLists.get(self.rddtScraper.currentSubredditListName)
        indices = self.subredditList.selectedIndexes()  # indices is a list of QModelIndex
        index = None
        if len(indices) > 0:
            index = indices[0].row()  # only one thing should be selectable at a time
        if model is not None and index is not None:
            model.removeRows(index, 1)
            self.setUnsavedChanges(True)

    def showSettings(self):
        settings = SettingsGUI(self.rddtScraper.userLists, self.rddtScraper.subredditLists,
                               self.rddtScraper.defaultUserListName, self.rddtScraper.defaultSubredditListName, self.rddtScraper.avoidDuplicates)
        ret = settings.exec_()
        if ret == QDialog.Accepted:
            self.logPrint(
                "Saving settings:\n" + str(settings.currentUserListName) + "\n" + str(
                    settings.currentSubredditListName))
            self.rddtScraper.defaultUserListName = settings.currentUserListName
            self.rddtScraper.defaultSubredditListName = settings.currentSubredditListName
            self.rddtScraper.avoidDuplicates = settings.avoidDuplicates
            self.saveState()

    def makeNewSubredditList(self):
        subredditListName, okay = QInputDialog.getText(QInputDialog(), "Subreddit List Name",
                                                       "New Subreddit List Name:",
                                                       QLineEdit.Normal, "New Subreddit List")
        if okay and len(subredditListName) > 0:
            if any([subredditListName in lst for lst in self.rddtScraper.subredditLists]):
                QMessageBox.information(QMessageBox(), "Reddit Scraper", "Duplicate subreddit list names not allowed.")
                return
            self.subredditListChooser.addItem(subredditListName)
            self.subredditListChooser.setCurrentIndex(self.subredditListChooser.count() - 1)
            self.rddtScraper.subredditLists[subredditListName] = ListModel([], GenericListModelObj)
            self.chooseNewSubredditList(self.subredditListChooser.count() - 1)
            if self.rddtScraper.defaultSubredditListName is None:  # becomes None if user deletes all subreddit lists
                self.rddtScraper.defaultSubredditListName = subredditListName
            self.setUnsavedChanges(True)

    def makeNewUserList(self):
        userListName, okay = QInputDialog.getText(QInputDialog(), "User List Name", "New User List Name:",
                                                  QLineEdit.Normal,
                                                  "New User List")
        if okay and len(userListName) > 0:
            if any([userListName in lst for lst in self.rddtScraper.userLists]):
                QMessageBox.information(QMessageBox(), "Reddit Scraper", "Duplicate user list names not allowed.")
                return
            self.userListChooser.addItem(userListName)
            self.userListChooser.setCurrentIndex(self.userListChooser.count() - 1)
            self.rddtScraper.userLists[userListName] = ListModel([], User)
            self.chooseNewUserList(self.userListChooser.count() - 1)
            if self.rddtScraper.defaultUserListName is None:  # becomes None if user deletes all subreddit lists
                self.rddtScraper.defaultUserListName = userListName
            self.setUnsavedChanges(True)

    def removeNonDefaultLst(self, lstType):
        if lstType == ListType.USER:
            self.rddtScraper.currentUserListName = self.rddtScraper.defaultUserListName
            name = self.rddtScraper.currentUserListName
            lstChooser = self.userListChooser
            chooseFunc = self.chooseNewUserList
        elif lstType == ListType.SUBREDDIT:
            self.rddtScraper.currentSubredditListName = self.rddtScraper.defaultSubredditListName
            name = self.rddtScraper.currentSubredditListName
            lstChooser = self.subredditListChooser
            chooseFunc = self.chooseNewSubredditList
        else:
            return
        index = lstChooser.findText(name)
        lstChooser.setCurrentIndex(index)
        chooseFunc(index)

    def removeDefaultLst(self, lstType):
        if lstType == ListType.USER:
            modelName = list(self.rddtScraper.userLists)[0]
            self.rddtScraper.currentUserListName = modelName
            self.rddtScraper.defaultUserListName = modelName
            defaultName = modelName
            lstChooser = self.userListChooser
            chooseFunc = self.chooseNewUserList
        elif lstType == ListType.SUBREDDIT:
            modelName = list(self.rddtScraper.subredditLists)[0]
            self.rddtScraper.currentSubredditListName = modelName
            self.rddtScraper.defaultSubredditListName = modelName
            defaultName = modelName
            lstChooser = self.subredditListChooser
            chooseFunc = self.chooseNewSubredditList
        else:
            return
        index = lstChooser.findText(defaultName)
        lstChooser.setCurrentIndex(index)
        chooseFunc(index)

    def removeLastLst(self, lstType):
        print('deleting last list')
        if lstType == ListType.USER:
            self.rddtScraper.currentUserListName = None
            self.rddtScraper.defaultUserListName = None
            lst = self.userList
        elif lstType == ListType.SUBREDDIT:
            self.rddtScraper.currentSubredditListName = None
            self.rddtScraper.defaultSubredditListName = None
            lst = self.subredditList
        else:
            return
        lst.setModel(ListModel([], GenericListModelObj))

    def removeLst(self, lstType):
        if lstType == ListType.USER:
            lstChooser = self.userListChooser
            index = lstChooser.currentIndex()
            name = lstChooser.currentText()
            defaultName = self.rddtScraper.defaultUserListName
            message = "Are you sure you want to delete user list: " + name + "?"
            lst = self.rddtScraper.userLists
        elif lstType == ListType.SUBREDDIT:
            lstChooser = self.subredditListChooser
            index = lstChooser.currentIndex()
            name = lstChooser.currentText()
            defaultName = self.rddtScraper.defaultSubredditListName
            message = "Are you sure you want to delete subreddit list: " + name + "?"
            lst = self.rddtScraper.subredditLists
        else:
            return
        msgBox = confirmDialog(message)
        ret = msgBox.exec_()
        if ret == QMessageBox.Yes:
            if len(lst) <= 0:
                QMessageBox.information(QMessageBox(), "Reddit Scraper", "There are no more lists left to delete.")
                return
            lstChooser.removeItem(index)
            del lst[name]
            # if default is not being removed, just remove and switch to default
            if name != defaultName:
                self.removeNonDefaultLst(lstType)
            else:
                if len(self.rddtScraper.subredditLists) > 0:
                    # just choose the first model
                    self.removeDefaultLst(lstType)
                else:
                    self.removeLastLst(lstType)
            self.setUnsavedChanges(True)

    def chooseNewUserList(self, userListIndex):
        userListName = self.userListChooser.itemText(userListIndex)
        self.logPrint("Choosing new user list")
        self.rddtScraper.currentUserListName = userListName
        model = self.rddtScraper.userLists.get(self.rddtScraper.currentUserListName)
        self.userList.setModel(model)

    def chooseNewSubredditList(self, subredditListIndex):
        subredditListName = self.subredditListChooser.itemText(subredditListIndex)
        self.logPrint("Choosing new subreddit list")
        self.rddtScraper.currentSubredditListName = subredditListName
        model = self.rddtScraper.subredditLists.get(self.rddtScraper.currentSubredditListName)
        self.subredditList.setModel(model)

    def viewDownloadedUserPosts(self):
        model = self.rddtScraper.userLists.get(self.rddtScraper.currentUserListName)
        indices = self.userList.selectedIndexes()  # indices is a list of QModelIndex
        index = None
        if len(indices) > 0:
            index = indices[0]  # only one thing should be selectable at a time
        if model is not None and index is not None:
            selectedUser = model.getObjectInLst(index)
            downloadedUserPosts = selectedUser.redditPosts
            print(downloadedUserPosts)
            if downloadedUserPosts is not None and len(downloadedUserPosts) > 0:
                downloadedUserPostsGUI = DownloadedUserPostsGUI(selectedUser, confirmDialog, self.saveState)
                for post in downloadedUserPosts:
                    item = QListWidgetItem("", downloadedUserPostsGUI.downloadedUserPostsList)
                    labelWidget = QLabel()
                    labelWidget.setOpenExternalLinks(True)
                    labelWidget.setTextFormat(Qt.RichText)
                    size = QSize(128, 158)
                    item.setSizeHint(size)
                    size = QSize(128, 128)
                    pixmap = QPixmap(downloadedUserPosts.get(post)).scaled(size, Qt.KeepAspectRatio)
                    height = pixmap.height()
                    width = pixmap.width()
                    postTitle = post[post[0:-1].rfind("/") + 1:-1]
                    labelWidget.setText(
                        '<a href="' + post + '"><img src="' + downloadedUserPosts.get(post) + '" height="' + str(
                            height) + '" width="' + str(width) + '"><p>' + postTitle)
                    downloadedUserPostsGUI.downloadedUserPostsList.setItemWidget(item, labelWidget)
                    downloadedUserPostsGUI.posts.append(post)
                downloadedUserPostsGUI.exec_()
            else:
                QMessageBox.information(QMessageBox(), "Reddit Scraper",
                                        "The selected user has no downloaded posts. Download some by hitting the download button.")
        elif index is None:
            QMessageBox.information(QMessageBox(), "Reddit Scraper",
                                    "To view a user's downloaded posts, please select a user in the user list.")

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
            rddtScraper.subredditLists[key] = ListModel(val, GenericListModelObj)
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
    w = RddtScrapeGUI(rddtScraper, queue)
    w.show()

    thread = QThread()
    recv = MyReceiver(queue)
    recv.mysignal.connect(w.append_text)
    recv.moveToThread(thread)
    thread.started.connect(recv.run)
    thread.start()

    sys.exit(a.exec_())


if __name__ == "__main__":
    main()