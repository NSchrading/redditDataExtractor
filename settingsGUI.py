from PyQt4.Qt import *
from settings_auto import Ui_SettingsDialog


class SettingsGUI(QDialog, Ui_SettingsDialog):
    def __init__(self, userLists, subredditLists, currentUserListName, currentSubredditListName, avoidDuplicates,
                 getExternalContent, getSubmissionContent, getCommentData, subSort, subLimit):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.userLists = userLists
        self.subredditLists = subredditLists
        self.currentUserListName = currentUserListName
        self.currentSubredditListName = currentSubredditListName
        self.avoidDuplicates = avoidDuplicates
        self.getExternalContent = getExternalContent
        self.getSubmissionContent = getSubmissionContent
        self.getCommentData = getCommentData
        self.subSort = subSort
        self.subLimit = subLimit
        self.validator = QIntValidator(1, 100)
        self.filtTableTypeCol = 0
        self.filtTablePropCol = 1
        self.filtTableOperCol = 2
        self.filtTableValCol = 3

        self.defaultUserListComboBox.activated.connect(self.chooseNewUserList)
        self.defaultSubredditListComboBox.activated.connect(self.chooseNewSubredditList)

        self.avoidDuplCheckBox.clicked.connect(lambda: self.changeCheckBox(self.avoidDuplCheckBox, 'avoidDuplicates'))
        self.getExternalContentCheckBox.clicked.connect(lambda: self.changeCheckBox(self.getExternalContentCheckBox, 'getExternalContent'))
        self.getSubmissionContentCheckBox.clicked.connect(lambda: self.changeCheckBox(self.getSubmissionContentCheckBox, 'getSubmissionContent'))
        self.getCommentDataCheckBox.clicked.connect(lambda: self.changeCheckBox(self.getCommentDataCheckBox, 'getCommentData'))

        self.hotBtn.clicked.connect(lambda: self.changeSubSort("hot"))
        self.newBtn.clicked.connect(lambda: self.changeSubSort("new"))
        self.risingBtn.clicked.connect(lambda: self.changeSubSort("rising"))
        self.controversialBtn.clicked.connect(lambda: self.changeSubSort("controversial"))
        self.topBtn.clicked.connect(lambda: self.changeSubSort("top"))

        self.subLimitTextEdit.textChanged.connect(self.setSubLimit)
        self.subLimitTextEdit.setValidator(self.validator)
        self.subLimitTextEdit.setText(str(self.subLimit))

        self.filterTable.cellPressed.connect(self.addFilter)

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
        self.getExternalContentCheckBox.setChecked(self.getExternalContent)
        self.getSubmissionContentCheckBox.setChecked(self.getSubmissionContent)
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

    def changeCheckBox(self, checkBox, setting):
        settingExists = self.__dict__.get(setting)
        if settingExists is not None:
            self.__dict__[setting] = checkBox.isChecked()

    def changeSubSort(self, subSort):
        self.subSort = subSort

    def setSubLimit(self):
        text = self.subLimitTextEdit.text()
        print(text)
        validState = self.validator.validate(text, 0)[0]  # validate() returns a tuple, the state is the 0 index
        if validState == QValidator.Acceptable:
            print("valid: " + text + "\n---------------------------------")
            self.subLimit = int(text)

    def makeTypeComboBox(self, row):
        combobox = QComboBox()
        combobox.addItem("Post")
        combobox.addItem("Comment")
        combobox.currentIndexChanged.connect(lambda: self.changePropComboBox(combobox.currentText(), row))
        return combobox

    def makePostPropComboBox(self):
        combobox = QComboBox()
        combobox.addItem("Title")
        combobox.addItem("Selftext")
        combobox.addItem("Domain")
        combobox.addItem("Author")
        combobox.addItem("Score")
        return combobox

    def makeCommentPropComboBox(self):
        combobox = QComboBox()
        combobox.addItem("Body")
        combobox.addItem("Author")
        combobox.addItem("Score")
        return combobox

    def makeOperComboBox(self):
        combobox = QComboBox()
        combobox.addItem("Equals")
        combobox.addItem("Does not equal")
        combobox.addItem("Begins with")
        combobox.addItem("Does not begin with")
        combobox.addItem("Ends with")
        combobox.addItem("Does not end with")
        combobox.addItem("Greater than")
        combobox.addItem("Less than")
        combobox.addItem("Contains")
        combobox.addItem("Does not contain")
        return combobox

    def changePropComboBox(self, text, row):
        if text == "Post":
            combobox = self.makePostPropComboBox()
        elif text == "Comment":
            combobox = self.makeCommentPropComboBox()
        self.filterTable.setCellWidget(row, self.filtTablePropCol, combobox)

    def addFilter(self, row, col):
        if col == self.filtTableTypeCol:
            typeCombobox = self.makeTypeComboBox(row)
            propCombobox = self.makePostPropComboBox()
            operCombobox = self.makeOperComboBox()
            self.filterTable.setCellWidget(row, col, typeCombobox)
            self.filterTable.setCellWidget(row, self.filtTablePropCol, propCombobox)
            self.filterTable.setCellWidget(row, self.filtTableOperCol, operCombobox)
            self.filterTable.insertRow(row + 1)
        if col == self.filtTableValCol:
            textEdit = QPlainTextEdit()
            self.filterTable.setCellWidget(row, self.filtTableValCol, textEdit)


