from PyQt4.Qt import *
from settings_auto import Ui_SettingsDialog
from genericListModelObjects import GenericListModelObj

def findKey(dict, value):
    return next((k for k, v in dict.items() if v == value), None)

class ConnectComboBox(QComboBox):

    # ~ooooohhhh~ static class variables
    text = "And"

    def __init__(self, row, filterTable, filtTableConnectCol, connectMap):
        super().__init__()
        self.row = row
        self.filterTable = filterTable
        self.filtTableConnectCol = filtTableConnectCol
        self.connectMap = connectMap
        for connect in self.connectMap:
            self.addItem(connect)
        self.setCurrentIndex(self.findText(ConnectComboBox.text))
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.displayContextMenu)
        self.activated.connect(self.changeAllConnects)

    def displayContextMenu(self, pos):
        menu = QMenu()
        removeAction = menu.addAction("Remove")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == removeAction:
            while(self.filterTable.rowCount() > self.row + 1):
                self.filterTable.removeRow(self.filterTable.rowCount() - 1)
            self.filterTable.removeCellWidget(self.row, self.filtTableConnectCol)

    def changeAllConnects(self, index):
        ConnectComboBox.text = self.currentText()
        for row in range(self.filterTable.rowCount() - 1):
            self.filterTable.removeCellWidget(row, self.filtTableConnectCol)
            print("Row: " + str(row) + " changing to text: " + ConnectComboBox.text)
            combobox = ConnectComboBox(row, self.filterTable, self.filtTableConnectCol, self.connectMap)
            combobox.setCurrentIndex(self.findText(ConnectComboBox.text))
            self.filterTable.setCellWidget(row, self.filtTableConnectCol, combobox)



class SettingsGUI(QDialog, Ui_SettingsDialog):
    def __init__(self, rddtScraper):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.userLists = rddtScraper.userLists
        self.subredditLists = rddtScraper.subredditLists
        self.currentUserListName = rddtScraper.defaultUserListName
        self.currentSubredditListName = rddtScraper.defaultSubredditListName
        self.avoidDuplicates = rddtScraper.avoidDuplicates
        self.getExternalContent = rddtScraper.getExternalContent
        self.getCommentExternalContent = rddtScraper.getCommentExternalContent
        self.getSelftextExternalContent = rddtScraper.getSelftextExternalContent
        self.getSubmissionContent = rddtScraper.getSubmissionContent
        self.subSort = rddtScraper.subSort
        self.subLimit = rddtScraper.subLimit
        self.operMap = rddtScraper.operMap
        self.validOperForPropMap = rddtScraper.validOperForPropMap
        self.connectMap = rddtScraper.connectMap
        self.filterExternalContent= rddtScraper.filterExternalContent
        self.filterSubmissionContent = rddtScraper.filterSubmissionContent
        self.restrictDownloadsByCreationDate = rddtScraper.restrictDownloadsByCreationDate
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
        self.getCommentExternalContentCheckBox.clicked.connect(lambda: self.changeCheckBox(self.getCommentExternalContentCheckBox, 'getCommentExternalContent'))
        self.getSelftextExternalContentCheckBox.clicked.connect(lambda: self.changeCheckBox(self.getSelftextExternalContentCheckBox, 'getSelftextExternalContent'))
        self.getSubmissionContentCheckBox.clicked.connect(lambda: self.changeCheckBox(self.getSubmissionContentCheckBox, 'getSubmissionContent'))

        self.hotBtn.clicked.connect(lambda: self.changeSubSort("hot"))
        self.newBtn.clicked.connect(lambda: self.changeSubSort("new"))
        self.risingBtn.clicked.connect(lambda: self.changeSubSort("rising"))
        self.controversialBtn.clicked.connect(lambda: self.changeSubSort("controversial"))
        self.topBtn.clicked.connect(lambda: self.changeSubSort("top"))

        self.subLimitTextEdit.textChanged.connect(self.setSubLimit)
        self.subLimitTextEdit.setValidator(self.validator)
        self.subLimitTextEdit.setText(str(self.subLimit))

        self.filterTable.cellPressed.connect(self.addFilter)
        self.constructFilterTable(rddtScraper.postFilts, rddtScraper.commentFilts, rddtScraper.connector, rddtScraper.operMap, rddtScraper.connectMap)
        self.filterExternalContentCheckBox.clicked.connect(lambda: self.changeCheckBox(self.filterExternalContentCheckBox, 'filterExternalContent'))
        self.filterSubmissionContentCheckBox.clicked.connect(lambda: self.changeCheckBox(self.filterSubmissionContentCheckBox, 'filterSubmissionContent'))

        self.restrictDownloadsByCreationDateCheckBox.clicked.connect(lambda: self.changeCheckBox(self.restrictDownloadsByCreationDateCheckBox, 'restrictDownloadsByCreationDate'))

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
        self.getCommentExternalContentCheckBox.setChecked(self.getCommentExternalContent)
        self.getSelftextExternalContentCheckBox.setChecked(self.getSelftextExternalContent)

        self.getSubmissionContentCheckBox.setChecked(self.getSubmissionContent)

        self.filterExternalContentCheckBox.setChecked(self.filterExternalContent)
        self.filterSubmissionContentCheckBox.setChecked(self.filterSubmissionContent)

        self.restrictDownloadsByCreationDateCheckBox.setChecked(self.restrictDownloadsByCreationDate)

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

    def constructFilterTableWidgets(self, type, prop, oper, val, operMap, row):
        print("adding for row:" + str(row))
        self.addFilter(row, self.filtTableTypeCol, type)
        typeCombobox = self.filterTable.cellWidget(row, self.filtTableTypeCol)
        typeCombobox.setCurrentIndex(typeCombobox.findText(type))
        print(typeCombobox.currentText())
        propCombobox = self.filterTable.cellWidget(row, self.filtTablePropCol)
        propCombobox.setCurrentIndex(propCombobox.findText(prop))
        print(prop)
        propType = self.getPropType(propCombobox.currentText())
        validOpers = self.validOperForPropMap.get(propType)
        if validOpers is not None:
            operCombobox = self.filterTable.cellWidget(row, self.filtTableOperCol)
            operCombobox.setCurrentIndex(operCombobox.findText(findKey(operMap, oper)))
        print(findKey(operMap, oper))
        valTextWidget = self.filterTable.cellWidget(row, self.filtTableValCol)
        valTextWidget.setPlainText(str(val))
        print(val)

    def constructFilterTable(self, postFilts, commentFilts, connector, operMap, connectMap):
        numFilts = len(postFilts) + len(commentFilts)
        if numFilts > 0:
            for row in range(1, numFilts): # first row is already added
                print("Adding row")
                self.filterTable.insertRow(row)
            row = 0
            for prop, oper, val in postFilts:
                self.constructFilterTableWidgets("Submission", prop, oper, val, operMap, row)
                row += 1
            for prop, oper, val in commentFilts:
                self.constructFilterTableWidgets("Comment", prop, oper, val, operMap, row)
                row += 1
            connectorText = findKey(connectMap, connector)
            for row in range(self.filterTable.rowCount() - 1):
                ConnectComboBox.text = connectorText # Set this to whatever the connector is currently so on creation of new ones, it doesn't default to And
                print("adding connector for row: " + str(row))
                connectCombobox = ConnectComboBox(row, self.filterTable, self.filtTableConnectCol, self.connectMap)
                connectCombobox.setCurrentIndex(connectCombobox.findText(connectorText))
                self.filterTable.setCellWidget(row, self.filtTableConnectCol, connectCombobox)
        else:
            self.addFilter(0, self.filtTableTypeCol)

    def chooseNewUserList(self):
        self.currentUserListName = self.defaultUserListComboBox.currentText()

    def chooseNewSubredditList(self):
        self.currentSubredditListName = self.defaultSubredditListComboBox.currentText()

    def changeCheckBox(self, checkBox, setting):
        settingExists = self.__dict__.get(setting)
        if settingExists is not None:
            self.__dict__[setting] = checkBox.isChecked()

    def changeSubSort(self, subSort):
        GenericListModelObj.subSort = subSort
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
        combobox.activated.connect(lambda: self.changePropComboBox(combobox.currentText(), row))
        return combobox

    def makeSubmissionPropComboBox(self, row):
        combobox = QComboBox()
        combobox.addItem("selftext")
        combobox.addItem("title")
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
        combobox.activated.connect(lambda: self.changeOperComboBox(combobox.currentText(), row))
        return combobox

    def makeCommentPropComboBox(self, row):
        combobox = QComboBox()
        combobox.addItem("body")
        combobox.addItem("gilded")
        combobox.addItem("score")
        combobox.addItem("author")
        combobox.addItem("edited")
        combobox.addItem("subreddit")
        combobox.addItem("controversiality")
        combobox.activated.connect(lambda: self.changeOperComboBox(combobox.currentText(), row))
        return combobox

    def makeOperComboBox(self, validOpers):
        combobox = QComboBox()
        for oper in validOpers:
            combobox.addItem(oper)
        return combobox

    def changePropComboBox(self, text, row):
        if text == "Submission":
            combobox = self.makeSubmissionPropComboBox(row)
        elif text == "Comment":
            combobox = self.makeCommentPropComboBox(row)
        if combobox is not None:
            self.filterTable.setCellWidget(row, self.filtTablePropCol, combobox)

    def changeOperComboBox(self, curText, row):
        propType = self.getPropType(curText)
        validOpers = self.validOperForPropMap.get(propType)
        if validOpers is not None:
            combobox = self.makeOperComboBox(validOpers)
            self.filterTable.setCellWidget(row, self.filtTableOperCol, combobox)

    def getPropType(self, curText):
        propType = ""
        if curText in {"selftext", "title", "domain", "subreddit", "url", "author", "body", "permalink"}:
            propType = "string"
        elif curText in {"score", "controversiality"}:
            propType = "number"
        elif curText in {"edited", "stickied", "over_18", "is_self", "gilded"}:
            propType = "boolean"
        return propType

    def addFilter(self, row, col, type="Submission"):
        if col == self.filtTableTypeCol:
            typeCombobox = self.makeTypeComboBox(row)
            if type == "Submission":
                propCombobox = self.makeSubmissionPropComboBox(row)
            elif type == "Comment":
                propCombobox = self.makeCommentPropComboBox(row)
            propType = self.getPropType(propCombobox.currentText())
            validOpers = self.validOperForPropMap.get(propType)
            if validOpers is not None:
                operCombobox = self.makeOperComboBox(validOpers)
                self.filterTable.setCellWidget(row, self.filtTableOperCol, operCombobox)
            textEdit = QPlainTextEdit()
            self.filterTable.setCellWidget(row, self.filtTableTypeCol, typeCombobox)
            self.filterTable.setCellWidget(row, self.filtTablePropCol, propCombobox)
            self.filterTable.setCellWidget(row, self.filtTableValCol, textEdit)
        elif col == self.filtTableConnectCol:
            connectCombobox = ConnectComboBox(row, self.filterTable, self.filtTableConnectCol, self.connectMap)
            self.filterTable.setCellWidget(row, self.filtTableConnectCol, connectCombobox)
            self.filterTable.insertRow(row + 1)
            self.addFilter(row + 1, self.filtTableTypeCol, "Submission")

    def checkFilterTable(self):
        if self.filterExternalContentCheckBox.isChecked() or self.filterSubmissionContentCheckBox.isChecked():
            for row in range(self.filterTable.rowCount()):
                if self.filterTable.cellWidget(row, self.filtTableValCol) is None or len(self.filterTable.cellWidget(row, self.filtTableValCol).toPlainText()) <= 0:
                    QMessageBox.warning(QMessageBox(), "Reddit Scraper", "Please enter text in the value column or uncheck that you would like to filter content.")
                    return False
        return True

    def accept(self):
        if self.checkFilterTable():
            super().accept()

