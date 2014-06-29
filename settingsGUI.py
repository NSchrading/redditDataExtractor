from PyQt4.Qt import *
from settings_auto import Ui_SettingsDialog


class SettingsGUI(QDialog, Ui_SettingsDialog):
    def __init__(self, userLists, subredditLists, currentUserListName, currentSubredditListName, avoidDuplicates,
                 getExternalDataSub, getCommentData, subSort, subLimit):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.userLists = userLists
        self.subredditLists = subredditLists
        self.currentUserListName = currentUserListName
        self.currentSubredditListName = currentSubredditListName
        self.avoidDuplicates = avoidDuplicates
        self.getExternalDataSub = getExternalDataSub
        self.getCommentData = getCommentData
        self.subSort = subSort
        self.subLimit = subLimit
        self.validator = QIntValidator(1, 100)

        self.defaultUserListComboBox.activated.connect(self.chooseNewUserList)
        self.defaultSubredditListComboBox.activated.connect(self.chooseNewSubredditList)

        self.avoidDuplCheckBox.clicked.connect(self.changeAvoidDuplicates)
        self.getExternalDataSubCheckBox.clicked.connect(self.changeGetExternalDataSub)
        self.getCommentDataCheckBox.clicked.connect(self.changeGetCommentData)

        self.hotBtn.clicked.connect(lambda: self.changeSubSort("hot"))
        self.newBtn.clicked.connect(lambda: self.changeSubSort("new"))
        self.risingBtn.clicked.connect(lambda: self.changeSubSort("rising"))
        self.controversialBtn.clicked.connect(lambda: self.changeSubSort("controversial"))
        self.topBtn.clicked.connect(lambda: self.changeSubSort("top"))

        self.subLimitTextEdit.textChanged.connect(self.setSubLimit)
        self.subLimitTextEdit.setValidator(self.validator)
        self.subLimitTextEdit.setText(str(self.subLimit))

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
        self.getExternalDataSubCheckBox.setChecked(self.getExternalDataSub)
        self.getCommentDataCheckBox.setChecked(self.getCommentData)

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

    def changeGetExternalDataSub(self):
        self.getExternalDataSub = self.getExternalDataSubCheckBox.isChecked()

    def changeGetCommentData(self):
        self.getCommentData = self.getCommentDataCheckBox.isChecked()

    def changeSubSort(self, subSort):
        self.subSort = subSort

    def setSubLimit(self):
        text = self.subLimitTextEdit.text()
        print(text)
        validState = self.validator.validate(text, 0)[0]  # validate() returns a tuple, the state is the 0 index
        if validState == QValidator.Acceptable:
            print("valid: " + text + "\n---------------------------------")
            self.subLimit = int(text)

