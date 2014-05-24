from PyQt4.Qt import *
from settings_auto import Ui_SettingsDialog


class SettingsGUI(QDialog, Ui_SettingsDialog):
    def __init__(self, userLists, subredditLists, currentUserListName, currentSubredditListName):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.userLists = userLists
        self.subredditLists = subredditLists
        self.currentUserListName = currentUserListName
        self.currentSubredditListName = currentSubredditListName

        self.defaultUserListComboBox.activated.connect(self.chooseNewUserList)
        self.defaultSubredditListComboBox.activated.connect(self.chooseNewSubredditList)
        self.initSettings()

    def initSettings(self):
        for userListKey in self.userLists:
            self.defaultUserListComboBox.addItem(userListKey)
        index = self.defaultUserListComboBox.findText(self.currentUserListName)
        self.defaultUserListComboBox.setCurrentIndex(index)
        for subredditListKey in self.subredditLists:
            self.defaultSubredditListComboBox.addItem(subredditListKey)
        index = self.defaultSubredditListComboBox.findText(self.currentSubredditListName)
        self.defaultSubredditListComboBox.setCurrentIndex(index)

    def chooseNewUserList(self):
        self.currentUserListName = self.defaultUserListComboBox.currentText()

    def chooseNewSubredditList(self):
        self.currentSubredditListName = self.defaultSubredditListComboBox.currentText()