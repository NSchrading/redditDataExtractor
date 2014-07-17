from PyQt4.Qt import *
from settings_auto import Ui_SettingsDialog


class ConnectComboBox(QComboBox):

    # ~ooooohhhh~ static class variables
    changing = False
    index = 0

    def __init__(self, row, filterTable, filtTableConnectCol, connectMap):
        super().__init__()
        self.row = row
        self.filterTable = filterTable
        self.filtTableConnectCol = filtTableConnectCol
        self.connectMap = connectMap
        for connect in self.connectMap:
            self.addItem(connect)
        self.setCurrentIndex(ConnectComboBox.index)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.displayContextMenu)
        self.currentIndexChanged.connect(self.changeAllConnects)

    def displayContextMenu(self, pos):
        menu = QMenu()
        removeAction = menu.addAction("Remove")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == removeAction:
            while(self.filterTable.rowCount() > self.row + 1):
                self.filterTable.removeRow(self.filterTable.rowCount() - 1)
            self.filterTable.removeCellWidget(self.row, self.filtTableConnectCol)

    def changeAllConnects(self, index):
        # check if we are running changeAllConnects from somewhere else. Without this we would get infinite recursion because
        # setCurrentIndex kicks off currentIndexChanged which calls this function. There are probably 2000 different ways
        # to do this that are better.
        if not ConnectComboBox.changing:
            ConnectComboBox.changing = True
            ConnectComboBox.index = index
            for row in range(self.filterTable.rowCount() - 1):
                self.filterTable.removeCellWidget(row, self.filtTableConnectCol)
                print("Row: " + str(row) + " changing to index: " + str(ConnectComboBox.index))
                combobox = ConnectComboBox(row, self.filterTable, self.filtTableConnectCol, self.connectMap)
                combobox.setCurrentIndex(ConnectComboBox.index)
                self.filterTable.setCellWidget(row, self.filtTableConnectCol, combobox)
            ConnectComboBox.changing = False



class SettingsGUI(QDialog, Ui_SettingsDialog):
    def __init__(self, rddtScraper):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.userLists = rddtScraper.userLists
        self.subredditLists = rddtScraper.subredditLists
        self.currentUserListName = rddtScraper.currentUserListName
        self.currentSubredditListName = rddtScraper.currentSubredditListName
        self.avoidDuplicates = rddtScraper.avoidDuplicates
        self.getExternalContent = rddtScraper.getExternalContent
        self.getSubmissionContent = rddtScraper.getSubmissionContent
        self.getCommentData = rddtScraper.getCommentData
        self.subSort = rddtScraper.subSort
        self.subLimit = rddtScraper.subLimit
        self.operMap = rddtScraper.operMap
        self.connectMap = rddtScraper.connectMap
        self.validator = QIntValidator(1, 100)
        self.filtTableTypeCol = 0
        self.filtTablePropCol = 1
        self.filtTableOperCol = 2
        self.filtTableValCol = 3
        self.filtTableConnectCol = 4

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
        self.addFilter(0, self.filtTableTypeCol)

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
        combobox.addItem("Submission")
        combobox.addItem("Comment")
        combobox.currentIndexChanged.connect(lambda: self.changePropComboBox(combobox.currentText(), row))
        return combobox

    def makePostPropComboBox(self):
        combobox = QComboBox()
        combobox.addItem("selftext")
        combobox.addItem("score")
        combobox.addItem("domain")
        combobox.addItem("edited")
        combobox.addItem("stickied")
        combobox.addItem("permalink")
        combobox.addItem("over_18")
        combobox.addItem("subreddit")
        combobox.addItem("url")
        combobox.addItem("author")
        combobox.addItem("is_self")
        return combobox

    def makeCommentPropComboBox(self):
        combobox = QComboBox()
        combobox.addItem("body")
        combobox.addItem("gilded")
        combobox.addItem("score")
        combobox.addItem("author")
        combobox.addItem("edited")
        combobox.addItem("subreddit")
        combobox.addItem("controversiality")
        return combobox

    def makeOperComboBox(self):
        combobox = QComboBox()
        for oper in self.operMap:
            combobox.addItem(oper)
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
        elif col == self.filtTableValCol:
            textEdit = QPlainTextEdit()
            self.filterTable.setCellWidget(row, self.filtTableValCol, textEdit)
        elif col == self.filtTableConnectCol:
            connectCombobox = ConnectComboBox(row, self.filterTable, self.filtTableConnectCol, self.connectMap)
            self.filterTable.setCellWidget(row, self.filtTableConnectCol, connectCombobox)
            self.filterTable.insertRow(row + 1)
            self.addFilter(row + 1, self.filtTableTypeCol)


