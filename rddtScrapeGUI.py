import sys
import os
import shelve

from PyQt4.Qt import *
from rddtScrape_auto import Ui_RddtScrapeMainWindow
from settingsGUI import SettingsGUI
from redditData import RedditData
from downloadedUserPostsGUI import DownloadedUserPostsGUI
from listModel import ListModel
from genericListModelObjects import GenericListModelObj, User


class RddtScrapeGUI(QMainWindow, Ui_RddtScrapeMainWindow):
    def __init__(self, rddtScraper):
        QMainWindow.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.rddtScraper = rddtScraper

        self.currentSelectedUserText = ""
        self.currentSelectedSubredditText = ""

        self.unsavedChanges = False

        self.log = True

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

        self.actionRemove_Subreddit_List.triggered.connect(self.removeSubredditList)
        self.actionRemove_User_List.triggered.connect(self.removeUserList)

        self.userListChooser.addAction(self.actionUser_List)
        self.subredditListChooser.addAction(self.actionSubreddit_List)
        self.userListChooser.addAction(self.actionRemove_User_List)
        self.subredditListChooser.addAction(self.actionRemove_Subreddit_List)

        self.userListChooser.activated.connect(self.chooseNewUserList)
        self.subredditListChooser.activated.connect(self.chooseNewSubredditList)

        self.userList.addAction(self.actionDownloaded_Reddit_User_Posts)
        self.actionDownloaded_Reddit_User_Posts.triggered.connect(self.viewDownloadedUserPosts)

        self.downloadBtn.clicked.connect(self.rddtScraper.download)

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

    def initSubredditList(self):
        for subredditListKey in self.rddtScraper.subredditLists:
            self.logPrint("Adding subreddit list: " + str(subredditListKey))
            self.subredditListChooser.addItem(subredditListKey)
        print("default subreddit list: " + str(self.rddtScraper.defaultSubredditListName))
        model = self.rddtScraper.subredditLists.get(self.rddtScraper.defaultSubredditListName)
        self.subredditList.setModel(model)
        index = self.subredditListChooser.findText(self.rddtScraper.defaultSubredditListName)
        self.subredditListChooser.setCurrentIndex(index)

    def init(self):
        self.initUserList()
        self.initSubredditList()

    def selectDirectory(self):
        directory = QFileDialog.getExistingDirectory(QFileDialog())
        if len(directory) > 0 and os.path.exists(directory):
            self.rddtScraper.defaultPath = directory
            self.directoryBox.setText(directory)
            self.setUnsavedChanges(True)

    def generateUniqueUserName(self, name):
        count = 1
        uniqueName = name + str(count)
        while uniqueName in self.rddtScraper.userSets.get(self.rddtScraper.currentUserSetName):
            count += 1
            uniqueName = name + str(count)
        return uniqueName

    def generateUniqueSubredditName(self, name):
        count = 1
        uniqueName = name + str(count)
        while uniqueName in self.rddtScraper.subredditSets.get(self.rddtScraper.currentSubredditSetName):
            count += 1
            uniqueName = name + str(count)
        return uniqueName

    def addUserToList(self):
        model = self.rddtScraper.userLists.get(self.rddtScraper.currentUserListName)
        if model is not None:
            model.insertRows(model.rowCount(), 1)

    def addSubredditToList(self):
        model = self.rddtScraper.subredditLists.get(self.rddtScraper.currentSubredditListName)
        if model is not None:
            model.insertRows(model.rowCount(), 1)

    def deleteUserFromList(self):
        model = self.rddtScraper.userLists.get(self.rddtScraper.currentUserListName)
        indices = self.userList.selectedIndexes()  # indices is a list of QModelIndex
        index = None
        if len(indices) > 0:
            index = indices[0].row()  # only one thing should be selectable at a time
        if model is not None and index is not None:
            model.removeRows(index, 1)

    def deleteSubredditFromList(self):
        model = self.rddtScraper.subredditLists.get(self.rddtScraper.currentSubredditListName)
        indices = self.subredditList.selectedIndexes()  # indices is a list of QModelIndex
        index = None
        if len(indices) > 0:
            index = indices[0].row()  # only one thing should be selectable at a time
        if model is not None and index is not None:
            model.removeRows(index, 1)

    def showSettings(self):
        settings = SettingsGUI(self.rddtScraper.userLists, self.rddtScraper.subredditLists,
                               self.rddtScraper.defaultUserListName, self.rddtScraper.defaultSubredditListName)
        ret = settings.exec_()
        if ret == QDialog.Accepted:
            self.logPrint(
                "Saving settings:\n" + str(settings.currentUserListName) + "\n" + str(settings.currentSubredditListName))
            self.rddtScraper.defaultUserListName = settings.currentUserListName
            self.rddtScraper.defaultSubredditListName = settings.currentSubredditListName
            self.saveState()

    def makeNewSubredditList(self):
        subredditListName, okay = QInputDialog.getText(QInputDialog(), "Subreddit List Name",
                                                       "New Subreddit List Name:",
                                                       QLineEdit.Normal, "New Subreddit List")
        if okay and len(subredditListName) > 0:
            self.subredditListChooser.addItem(subredditListName)
            self.subredditListChooser.setCurrentIndex(self.subredditListChooser.count() - 1)
            self.rddtScraper.subredditLists[subredditListName] =  ListModel([], GenericListModelObj)
            self.chooseNewSubredditList(self.subredditListChooser.count() - 1)
            self.setUnsavedChanges(True)

    def makeNewUserList(self):
        userListName, okay = QInputDialog.getText(QInputDialog(), "User List Name", "New User List Name:",
                                                  QLineEdit.Normal,
                                                  "New User List")
        if okay and len(userListName) > 0:
            self.userListChooser.addItem(userListName)
            self.userListChooser.setCurrentIndex(self.userListChooser.count() - 1)
            self.rddtScraper.userLists[userListName] = ListModel([], User)
            self.chooseNewUserList(self.userListChooser.count() - 1)
            self.setUnsavedChanges(True)

    def removeSubredditList(self):
        index = self.subredditListChooser.currentIndex()
        name = self.subredditListChooser.currentText()
        msgBox = QMessageBox()
        msgBox.setText("Are you sure you want to delete subreddit list: " + name + "?")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        ret = msgBox.exec_()
        if ret == QMessageBox.Yes:
            if len(self.rddtScraper.subredditLists) <= 0:
                QMessageBox.information(QMessageBox(), "Reddit Scraper", "There are no more lists left to delete.")
                return
            self.subredditListChooser.removeItem(index)
            del self.rddtScraper.subredditLists[name]
            # if default is not being removed, just remove and switch to default
            if name != self.rddtScraper.defaultSubredditListName:
                self.rddtScraper.currentSubredditListName = self.rddtScraper.defaultSubredditListName
                index = self.subredditListChooser.findText(self.rddtScraper.defaultSubredditListName)
                self.subredditListChooser.setCurrentIndex(index)
                self.chooseNewSubredditList(index)
            else:
                if len(self.rddtScraper.subredditLists) > 0:
                    # just choose the first model
                    modelName = list(self.rddtScraper.subredditLists)[0]
                    model = self.rddtScraper.userLists.get(modelName)
                    self.rddtScraper.currentSubredditListName = modelName
                    self.rddtScraper.defaultUserListName = modelName
                    defaultName = modelName
                    index = self.subredditListChooser.findText(defaultName)
                    self.subredditListChooser.setCurrentIndex(index)
                    self.chooseNewSubredditList(index)
                else:
                    print('deleting last list')
                    self.rddtScraper.currentSubredditListName = None
                    self.rddtScraper.defaultSubredditListName = None
                    self.subredditList.setModel(ListModel([], GenericListModelObj))

    def removeUserList(self):
        index = self.userListChooser.currentIndex()
        name = self.userListChooser.currentText()
        msgBox = QMessageBox()
        msgBox.setText("Are you sure you want to delete list: " + name + "?")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        ret = msgBox.exec_()
        if ret == QMessageBox.Yes:
            if len(self.rddtScraper.userLists) <= 0:
                QMessageBox.information(QMessageBox(), "Reddit Scraper", "There are no more lists left to delete.")
                return
            self.userListChooser.removeItem(index)
            del self.rddtScraper.userLists[name]
            # if default is not being removed, just remove and switch to default
            if name != self.rddtScraper.defaultUserListName:
                self.rddtScraper.currentUserListName = self.rddtScraper.defaultUserListName
                index = self.userListChooser.findText(self.rddtScraper.defaultUserListName)
                self.userListChooser.setCurrentIndex(index)
                self.chooseNewUserList(index)
            else:
                print('removing default')
                if len(self.rddtScraper.userLists) > 0:
                    print('not deleting last list')
                    # just choose the first model
                    modelName = list(self.rddtScraper.userLists)[0]
                    model = self.rddtScraper.userLists.get(modelName)
                    self.rddtScraper.currentUserListName = modelName
                    self.rddtScraper.defaultUserListName = modelName
                    defaultName = modelName
                    index = self.userListChooser.findText(defaultName)
                    self.userListChooser.setCurrentIndex(index)
                    self.chooseNewUserList(index)
                else:
                    print('deleting last list')
                    self.rddtScraper.currentUserListName = None
                    self.rddtScraper.defaultUserListName = None
                    self.userList.setModel(ListModel([], User))

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
            downloadedUserPosts = selectedUser.posts
            print(downloadedUserPosts)
            if downloadedUserPosts is not None:
                downloadedUserPostsGUI = DownloadedUserPostsGUI()
                for post in downloadedUserPosts:
                    item = QListWidgetItem("", downloadedUserPostsGUI.downloadedUserPostsList)
                    labelWidget = QLabel()
                    labelWidget.setOpenExternalLinks(True)
                    labelWidget.setTextFormat(Qt.RichText)
                    postTitle = post[post[0:-1].rfind("/") + 1:-1]
                    labelWidget.setText('<a href="' + post + '">' + postTitle + '</a>')
                    downloadedUserPostsGUI.downloadedUserPostsList.setItemWidget(item, labelWidget)
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
    except KeyError:
        print("here")
    finally:
        shelf.close()
        return rddtScraper


def main():
    a = QApplication(sys.argv)
    rddtScraper = loadState()
    if rddtScraper is None:
        print("rddt data client was None, making new one")
        rddtScraper = RedditData()
    w = RddtScrapeGUI(rddtScraper)
    w.show()
    #a.connect(a, SIGNAL('aboutToQuit()'), w.checkSaveState)
    sys.exit(a.exec_())


if __name__ == "__main__":
    main()