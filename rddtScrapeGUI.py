import sys
import os
import shelve

from PyQt4.Qt import *
from rddtScrape_auto import Ui_RddtScrapeMainWindow
from settingsGUI import SettingsGUI
from redditData import RedditData
from downloadedUserPostsGUI import DownloadedUserPostsGUI
from userListModel import UserListModel

class rddtScrapeGUI(QMainWindow, Ui_RddtScrapeMainWindow):
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

        self.subredditList.itemChanged.connect(self.subredditTextChanged)
        self.subredditList.currentItemChanged.connect(self.currentSubredditChanged)

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
            self.logPrint("Adding user set: " + str(userListKey))
            self.userListChooser.addItem(userListKey)
        model = self.rddtScraper.userLists.get(self.rddtScraper.currentUserListName)
        self.userList.setModel(model)
        index = self.userListChooser.findText(self.rddtScraper.defaultUserListName)
        self.userListChooser.setCurrentIndex(index)

    def initSubredditList(self):
        for subredditSetName in self.rddtScraper.subredditSets:
            self.logPrint("Adding subreddit set: " + str(subredditSetName))
            self.subredditListChooser.addItem(subredditSetName)
        # Add the subreddits into the list widget only for the default list
        subreddits = self.rddtScraper.subredditSets.get(self.rddtScraper.defaultSubredditSetName)
        if subreddits is not None:
            for subreddit in subreddits:
                self.logPrint("Adding subreddit: " + str(subreddit))
                self.addSubredditToList(None, True, subreddit)
            index = self.subredditListChooser.findText(self.rddtScraper.defaultSubredditSetName)
            self.subredditListChooser.setCurrentIndex(index)

    def init(self):
        self.initUserList()
        self.initSubredditList()

    def selectDirectory(self):
        directory = QFileDialog.getExistingDirectory()
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

    def addSubredditToList(self, _, init=False, subredditName=""):
        """ This if is called if actually adding a new subreddit to the list
        Otherwise, the function is being called to add the subreddits from an already
        made list that is being switched to """
        if not init:
            subredditName = self.generateUniqueSubredditName("Subreddit")
            self.setUnsavedChanges(True)
        item = QListWidgetItem()
        item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsDragEnabled|Qt.ItemIsUserCheckable|Qt.ItemIsEnabled)
        item.setText(subredditName)
        self.subredditList.addItem(item)
        if not init:
            self.rddtScraper.subredditSets[self.subredditListChooser.currentText()].add(item.text())
        self.logPrint(self.rddtScraper.subredditSets[self.subredditListChooser.currentText()])

    def deleteUserFromList(self):
        model = self.rddtScraper.userLists.get(self.rddtScraper.currentUserListName)
        indices = self.userList.selectedIndexes() # indices is a list of QModelIndex
        index = None
        if len(indices) > 0:
            index = indices[0].row() # only one thing should be selectable at a time
        if model is not None and index is not None:
            model.removeRows(index, 1)

    def deleteUserFromListByIndex(self, index):
        removed = self.userList.takeItem(index)
        if removed is not None:
            userText = removed.text()
            self.logPrint("removing: " + str(userText))
            self.rddtScraper.userSets[self.userListChooser.currentText()].remove(userText)
            self.logPrint(self.rddtScraper.userSets[self.userListChooser.currentText()])
            del removed
            self.setUnsavedChanges(True)

    def deleteSubredditFromList(self):
        subreddit = self.subredditList.currentItem()
        index = self.subredditList.indexFromItem(subreddit).row()
        self.deleteSubredditFromListByIndex(index)

    def deleteSubredditFromListByIndex(self, index):
        removed = self.subredditList.takeItem(index)
        if removed is not None:
            subredditText = removed.text()
            self.logPrint("removing: " + str(subredditText))
            self.rddtScraper.subredditSets[self.subredditListChooser.currentText()].remove(subredditText)
            self.logPrint(self.rddtScraper.subredditSets[self.subredditListChooser.currentText()])
            del removed
            self.setUnsavedChanges(True)

    def userTextChanged(self, user):
        if user.text() in self.rddtScraper.userSets[self.userListChooser.currentText()]:
            newName = self.generateUniqueUserName(user.text())
            user.setText(newName)
            self.logPrint("adding: " + str(newName))
            self.rddtScraper.userSets[self.userListChooser.currentText()].add(newName)
            self.currentSelectedUserText = newName
            ret = QMessageBox.warning(self, "Duplicate Users", "Duplicate Users Detected. The Duplicate User has been changed to " + newName)
            self.setUnsavedChanges(True)
        elif self.currentSelectedUserText != user.text():
            self.logPrint("removing: " + str(self.currentSelectedUserText))
            self.rddtScraper.userSets[self.userListChooser.currentText()].remove(self.currentSelectedUserText)
            self.logPrint("adding: " + user.text())
            self.rddtScraper.userSets[self.userListChooser.currentText()].add(user.text())
            self.currentSelectedUserText = user.text()
            self.setUnsavedChanges(True)

    def subredditTextChanged(self, subreddit):
        self.logPrint("GERE")
        if subreddit.text() in self.rddtScraper.subredditSets[self.subredditListChooser.currentText()]:
            newName = self.generateUniqueSubredditName(subreddit.text())
            subreddit.setText(newName)
            self.logPrint("adding: " + str(newName))
            self.rddtScraper.subredditSets[self.subredditListChooser.currentText()].add(newName)
            self.currentSelectedSubredditText = newName
            ret = QMessageBox.warning(self, "Duplicate Subreddits", "Duplicate Subreddits Detected. The Duplicate Subreddit has been changed to " + newName)
            self.setUnsavedChanges(True)
        elif self.currentSelectedSubredditText != subreddit.text():
            self.logPrint("removing: " + str(self.currentSelectedSubredditText))
            self.rddtScraper.subredditSets[self.subredditListChooser.currentText()].remove(self.currentSelectedSubredditText)
            self.logPrint("adding: " + subreddit.text())
            self.rddtScraper.subredditSets[self.subredditListChooser.currentText()].add(subreddit.text())
            self.currentSelectedSubredditText = subreddit.text()
            self.setUnsavedChanges(True)

    def currentUserChanged(self, cur, prev):
        curText = "None" if cur is None else cur.text()
        self.currentSelectedUserText = curText
        prevText = "None" if prev is None else prev.text()
        self.logPrint("curUserText changed to: " + curText + " from " + prevText)

    def currentSubredditChanged(self, cur, prev):
        curText = "None" if cur is None else cur.text()
        self.currentSelectedSubredditText = curText
        prevText = "None" if prev is None else prev.text()
        self.logPrint("curSubrddtText changed to: " + curText + " from " + prevText)

    def showSettings(self):
        settings = SettingsGUI(self.rddtScraper.userLists, self.rddtScraper.subredditSets, self.rddtScraper.defaultUserListName, self.rddtScraper.defaultSubredditSetName)
        ret = settings.exec_()
        if ret == QDialog.Accepted:
            self.logPrint("Saving settings:\n" + str(settings.currentUserListName) + "\n" + str(settings.currentSubredditSetName))
            self.rddtScraper.defaultUserListName = settings.currentUserListName
            self.rddtScraper.defaultSubredditSetName = settings.currentSubredditSetName
            self.saveState()

    def makeNewSubredditList(self):
        subredditListName, okay = QInputDialog.getText(self, "Subreddit List Name", "New Subreddit List Name:", QLineEdit.Normal, "New Subreddit List")
        if(okay and len(subredditListName) > 0):
            self.subredditListChooser.addItem(subredditListName)
            self.subredditListChooser.setCurrentIndex(self.subredditListChooser.count() - 1)
            self.rddtScraper.subredditSets[subredditListName] = set([])
            self.chooseNewSubredditList(self.subredditListChooser.count() - 1)
            self.setUnsavedChanges(True)

    def makeNewUserList(self):
        userListName, okay = QInputDialog.getText(self, "User List Name", "New User List Name:", QLineEdit.Normal, "New User List")
        if(okay and len(userListName) > 0):
            self.userListChooser.addItem(userListName)
            self.userListChooser.setCurrentIndex(self.userListChooser.count() - 1)
            self.rddtScraper.userLists[userListName] = UserListModel([])
            self.chooseNewUserList(self.userListChooser.count() - 1)
            self.setUnsavedChanges(True)

    def removeSubredditList(self):
        index = self.subredditListChooser.currentIndex()
        name = self.subredditListChooser.currentText()
        msgBox = QMessageBox();
        msgBox.setText("Are you sure you want to delete subreddit list: " + name + "?")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        ret = msgBox.exec_();
        if ret == QMessageBox.Yes:
            self.subredditListChooser.removeItem(index)
            self.rddtScraper.subredditSets.pop(name)
            if name != self.rddtScraper.defaultSubredditSetName:
                self.rddtScraper.currentSubredditSetName = self.rddtScraper.defaultSubredditSetName
                index = self.subredditListChooser.findText(self.rddtScraper.defaultSubredditSetName)
                self.subredditListChooser.setCurrentIndex(index)
                self.chooseNewSubredditList(index)
            else:
                if len(self.rddtScraper.subredditSets) > 0:
                    # just choose the first set as the set to show and be default
                    subredditSet = list(self.rddtScraper.subredditSets.keys())[0]
                    self.rddtScraper.currentSubredditSetName = subredditSet
                    self.rddtScraper.defaultSubredditSetName = subredditSet
                    index = self.subredditListChooser.findText(subredditSet)
                    self.subredditListChooser.setCurrentIndex(index)
                    self.chooseNewSubredditList(index)
                else:
                    self.rddtScraper.currentSubredditSetName = None
                    self.rddtScraper.defaultSubredditSetName = None
                    self.subredditList.clear()
            self.logPrint("removed subreddit list.\n" + str(self.rddtScraper.currentSubredditSetName) + "\n" + str(self.rddtScraper.defaultSubredditSetName))
            self.setUnsavedChanges(True)

    def removeUserList(self):
        index = self.userListChooser.currentIndex()
        name = self.userListChooser.currentText()
        msgBox = QMessageBox();
        msgBox.setText("Are you sure you want to delete user list: " + name + "?")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgBox.setDefaultButton(QMessageBox.No)
        ret = msgBox.exec_();
        if ret == QMessageBox.Yes:
            self.userListChooser.removeItem(index)
            self.rddtScraper.userSets.pop(name)
            if name != self.rddtScraper.defaultUserSetName:
                self.rddtScraper.currentUserSetName = self.rddtScraper.defaultUserSetName
                index = self.userListChooser.findText(self.rddtScraper.defaultUserSetName)
                self.userListChooser.setCurrentIndex(index)
                self.chooseNewUserList(index)
            else:
                self.logPrint("Removing a default user list")
                if len(self.rddtScraper.userSets) > 0:
                    self.logPrint("Choosing first available")
                    # just choose the first set as the set to show and be default
                    userSet = list(self.rddtScraper.userSets.keys())[0]
                    self.rddtScraper.currentUserSetName = userSet
                    self.rddtScraper.defaultUserSetName = userSet
                    index = self.userListChooser.findText(userSet)
                    self.userListChooser.setCurrentIndex(index)
                    self.chooseNewUserList(index)
                else:
                    self.logPrint("No lists left")
                    self.rddtScraper.currentUserSetName = None
                    self.rddtScraper.defaultUserSetName = None
                    self.userList.clear()
            self.logPrint("removed user list.\n" + str(self.rddtScraper.currentUserSetName) + "\n" + str(self.rddtScraper.defaultUserSetName))
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
        self.subredditList.clear()
        self.rddtScraper.currentSubredditSetName = subredditListName
        subredditSet = self.rddtScraper.subredditSets.get(subredditListName)
        if subredditSet is not None:
            self.logPrint("Subreddit list " + str(subredditListName) + " was not None. Adding.")
            self.logPrint("Set Returned:\n" + str(subredditSet))
            for subreddit in subredditSet:
                self.addSubredditToList(None, True, subreddit)
        else:
            self.logPrint("Subreddit list " + str(subredditListName) + " was None.")
            self.rddtScraper.subredditSets[subredditListName] = set([])
        self.rddtScraper.currentSubredditSetName = subredditListName

    def viewDownloadedUserPosts(self):
        currentUser = self.userList.currentItem()
        if currentUser is None:
            QMessageBox.information(self, "Reddit Scraper", "To view a user's downloaded posts, please select a user in the user list.")
        else:
            downloadedUserPosts = self.rddtScraper.downloadedUserPosts.get(currentUser.text())
            if downloadedUserPosts is not None:
                downloadedUserPostsGUI = DownloadedUserPostsGUI()
                for post in downloadedUserPosts:
                    item = QListWidgetItem("", downloadedUserPostsGUI.downloadedUserPostsList)
                    labelWidget = QLabel()
                    labelWidget.setOpenExternalLinks(True)
                    labelWidget.setTextFormat(Qt.RichText)
                    labelWidget.setText(post)
                    downloadedUserPostsGUI.downloadedUserPostsList.setItemWidget(item, labelWidget)
                ret = downloadedUserPostsGUI.exec_()
            else:
                QMessageBox.information(self, "Reddit Scraper", "The selected user has no downloaded posts. Download some by hitting the download button.")


    def setUnsavedChanges(self, unsaved):
        self.unsavedChanges = unsaved
        if self.unsavedChanges:
            self.setWindowTitle("Reddit Scraper *")
        else:
            self.setWindowTitle("Reddit Scraper")

    def checkSaveState(self):
        close = False
        if self.unsavedChanges:
            msgBox = QMessageBox();
            msgBox.setText("A list or setting has been changed.");
            msgBox.setInformativeText("Do you want to save your changes?");
            msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel);
            msgBox.setDefaultButton(QMessageBox.Save);
            ret = msgBox.exec_();
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


    def saveState(self):
        userListModels = self.rddtScraper.userLists
        userListSettings = {} # Use this to save normally unpickleable stuff
        for key, val in userListModels.items():
            userListSettings[key] = val.users
        try:
            shelf = shelve.open("settings.db")
            self.rddtScraper.userLists = None # QAbstractListModel is not pickleable so set this to None
            shelf['rddtScraper'] = self.rddtScraper
            shelf['userLists'] = userListSettings # Save QAbstractList data as a simple dict of list
            self.setUnsavedChanges(False)
            self.rddtScraper.userLists = userListModels # Restore the user lists in case the user is not exiting program
            self.logPrint("Saving program.")
        except KeyError:
            pass
        finally:
            shelf.close()

    def logPrint(self, str):
        if self.log:
            print(str)

def loadState():
    print("attempting to load state")
    try:
        shelf = shelve.open("settings.db")
        rddtScraper = shelf['rddtScraper']
        userListSettings = shelf['userLists']
        rddtScraper.userLists = {}
        for key, val in userListSettings.items():
            print("loading from saved " + key)
            rddtScraper.userLists[key] = UserListModel(val)
        return rddtScraper
    except KeyError:
        print("here")
        return None
    finally:
        shelf.close()

def main():
    a = QApplication(sys.argv)
    rddtScraper = loadState()
    if rddtScraper is None:
        rddtScraper = RedditData()
    w = rddtScrapeGUI(rddtScraper)
    w.show()
    #a.connect(a, SIGNAL('aboutToQuit()'), w.checkSaveState)
    sys.exit(a.exec_())

if __name__ == "__main__":
    main()