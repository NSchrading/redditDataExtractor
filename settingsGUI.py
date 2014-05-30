from PyQt4.Qt import *
from settings_auto import Ui_SettingsDialog


class SettingsGUI(QDialog, Ui_SettingsDialog):
    def __init__(self, userLists, subredditLists, currentUserListName, currentSubredditListName, avoidDuplicates, subSort):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.userLists = userLists
        self.subredditLists = subredditLists
        self.currentUserListName = currentUserListName
        self.currentSubredditListName = currentSubredditListName

        self.defaultUserListComboBox.activated.connect(self.chooseNewUserList)
        self.defaultSubredditListComboBox.activated.connect(self.chooseNewSubredditList)
        self.avoidDuplCheckBox.clicked.connect(self.changeAvoidDuplicates)
        self.hotBtn.clicked.connect(lambda: self.changeSubSort("hot"))
        self.newBtn.clicked.connect(lambda: self.changeSubSort("new"))
        self.risingBtn.clicked.connect(lambda: self.changeSubSort("rising"))
        self.controversialBtn.clicked.connect(lambda: self.changeSubSort("controversial"))
        self.topBtn.clicked.connect(lambda: self.changeSubSort("top"))

        self.avoidDuplicates = avoidDuplicates
        self.subSort = subSort
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
        self.avoidDuplCheckBox.setChecked(self.avoidDuplicates)
        self.initSubSort()

    def initSubSort(self):
        if self.subSort == "hot":
            self.hotBtn.setChecked(True)
        elif self.subSort == "new":
            self.newBtn.setChecked(True)
        elif self.subSort == "rising":
            self.risingBtn.setChecked(True)
        elif self.subSort == "controversial":
            self.controversialBtn.setChecked(True)
        else:
            self.topBtn.setChecked(True)

    def chooseNewUserList(self):
        self.currentUserListName = self.defaultUserListComboBox.currentText()

    def chooseNewSubredditList(self):
        self.currentSubredditListName = self.defaultSubredditListComboBox.currentText()

    def changeAvoidDuplicates(self):
        self.avoidDuplicates = self.avoidDuplCheckBox.isChecked()

    def changeSubSort(self, subSort):
        self.subSort = subSort