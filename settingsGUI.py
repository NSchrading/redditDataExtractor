from PyQt4.Qt import *
from settings_auto import Ui_SettingsDialog


class SettingsGUI(QDialog, Ui_SettingsDialog):
    def __init__(self, userLists, subredditSets, currentUserListName, currentSubredditSetName):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.userLists = userLists
        self.subredditSets = subredditSets
        self.currentUserListName = currentUserListName
        self.currentSubredditSetName = currentSubredditSetName

        self.defaultUserListComboBox.activated.connect(self.chooseNewUserList)
        self.defaultSubredditListComboBox.activated.connect(self.chooseNewSubredditList)
        self.initSettings()

    def initSettings(self):
        for userListKey in self.userLists:
            self.defaultUserListComboBox.addItem(userListKey)
        index = self.defaultUserListComboBox.findText(self.currentUserListName)
        self.defaultUserListComboBox.setCurrentIndex(index)
        for subredditSetName in self.subredditSets:
            self.defaultSubredditListComboBox.addItem(subredditSetName)
        index = self.defaultSubredditListComboBox.findText(self.currentSubredditSetName)
        self.defaultSubredditListComboBox.setCurrentIndex(index)

    def chooseNewUserList(self):
        self.currentUserListName = self.defaultUserListComboBox.currentText()

    def chooseNewSubredditList(self):
        self.currentSubredditSetName = self.defaultSubredditListComboBox.currentText()