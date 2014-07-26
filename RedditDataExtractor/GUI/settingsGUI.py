from PyQt4.Qt import QComboBox, Qt, QMenu, QDialog, QIntValidator, QValidator, QPlainTextEdit, QMessageBox

from .settings_auto import Ui_SettingsDialog
from .genericListModelObjects import GenericListModelObj


def findKey(dict, value):
    return next((k for k, v in dict.items() if v == value), None)

class ConnectCombobox(QComboBox):

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
        self.setCurrentIndex(self.findText(ConnectCombobox.text))
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
        ConnectCombobox.text = self.currentText()
        for row in range(self.filterTable.rowCount() - 1):
            self.filterTable.removeCellWidget(row, self.filtTableConnectCol)
            print("Row: " + str(row) + " changing to text: " + ConnectCombobox.text)
            combobox = ConnectCombobox(row, self.filterTable, self.filtTableConnectCol, self.connectMap)
            combobox.setCurrentIndex(self.findText(ConnectCombobox.text))
            self.filterTable.setCellWidget(row, self.filtTableConnectCol, combobox)

class TypeCombobox(QComboBox):

    def __init__(self, row, propCombobox):
        super().__init__()
        self.row = row
        self.addItem("Submission")
        self.addItem("Comment")
        self.propCombobox = propCombobox
        self.currentIndexChanged.connect(self.changePropComboBox)
        self.setCurrentIndex(1) # just change it to kick off the flow of comboboxes changing to their proper values

    def changePropComboBox(self, index):
        if self.currentText() == "Submission":
            self.propCombobox.initSubmission()
        elif self.currentText() == "Comment":
            self.propCombobox.initComment()


class PropCombobox(QComboBox):

    def __init__(self, row, operCombobox, validOperForPropMap):
        super().__init__()
        self.row = row
        self.operCombobox = operCombobox
        self.validOperForPropMap = validOperForPropMap
        self.initSubmission()
        self.currentIndexChanged.connect(self.changeOperCombobox)

    def initSubmission(self):
        self.clear()
        self.addItem("selftext")
        self.addItem("title")
        self.addItem("score")
        self.addItem("domain")
        self.addItem("edited")
        self.addItem("stickied")
        self.addItem("permalink")
        self.addItem("over_18")
        self.addItem("subreddit")
        self.addItem("url")
        self.addItem("author")
        self.addItem("is_self")

    def initComment(self):
        self.clear()
        self.addItem("body")
        self.addItem("gilded")
        self.addItem("score")
        self.addItem("author")
        self.addItem("edited")
        self.addItem("subreddit")
        self.addItem("controversiality")

    def getPropType(self):
        propType = ""
        if self.currentText() in {"selftext", "title", "domain", "subreddit", "url", "author", "body", "permalink"}:
            propType = "string"
        elif self.currentText() in {"score", "controversiality"}:
            propType = "number"
        elif self.currentText() in {"edited", "stickied", "over_18", "is_self", "gilded"}:
            propType = "boolean"
        return propType

    def changeOperCombobox(self, index):
        propType = self.getPropType()
        validOpers = self.validOperForPropMap.get(propType)
        if validOpers is not None:
            self.operCombobox.changeOpers(validOpers)


class OperCombobox(QComboBox):

    def __init__(self, row):
        super().__init__()
        self.row = row

    def changeOpers(self, validOpers):
        self.clear()
        for oper in validOpers:
            self.addItem(oper)


class SettingsGUI(QDialog, Ui_SettingsDialog):
    def __init__(self, rddtDataExtractor):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.userLists = rddtDataExtractor.userLists
        self.subredditLists = rddtDataExtractor.subredditLists
        self.currentUserListName = rddtDataExtractor.defaultUserListName
        self.currentSubredditListName = rddtDataExtractor.defaultSubredditListName
        self.avoidDuplicates = rddtDataExtractor.avoidDuplicates
        self.getExternalContent = rddtDataExtractor.getExternalContent
        self.getCommentExternalContent = rddtDataExtractor.getCommentExternalContent
        self.getSelftextExternalContent = rddtDataExtractor.getSelftextExternalContent
        self.getSubmissionContent = rddtDataExtractor.getSubmissionContent
        self.subSort = rddtDataExtractor.subSort
        self.subLimit = rddtDataExtractor.subLimit
        self.operMap = rddtDataExtractor.operMap
        self.validOperForPropMap = rddtDataExtractor.validOperForPropMap
        self.connectMap = rddtDataExtractor.connectMap
        self.filterExternalContent= rddtDataExtractor.filterExternalContent
        self.filterSubmissionContent = rddtDataExtractor.filterSubmissionContent
        self.restrictDownloadsByCreationDate = rddtDataExtractor.restrictDownloadsByCreationDate
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
        self.constructFilterTable(rddtDataExtractor.submissionFilts, rddtDataExtractor.commentFilts, rddtDataExtractor.connector, rddtDataExtractor.operMap, rddtDataExtractor.connectMap)
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
        print(typeCombobox.currentText())
        propCombobox = self.filterTable.cellWidget(row, self.filtTablePropCol)
        propCombobox.setCurrentIndex(propCombobox.findText(prop))
        print(prop)
        operCombobox = self.filterTable.cellWidget(row, self.filtTableOperCol)
        operCombobox.setCurrentIndex(operCombobox.findText(findKey(operMap, oper)))
        print(findKey(operMap, oper))
        valTextWidget = self.filterTable.cellWidget(row, self.filtTableValCol)
        valTextWidget.setPlainText(str(val))
        print(val)

    def constructFilterTable(self, submissionFilts, commentFilts, connector, operMap, connectMap):
        numFilts = len(submissionFilts) + len(commentFilts)
        if numFilts > 0:
            for row in range(1, numFilts): # first row is already added
                print("Adding row")
                self.filterTable.insertRow(row)
            row = 0
            for prop, oper, val in submissionFilts:
                self.constructFilterTableWidgets("Submission", prop, oper, val, operMap, row)
                row += 1
            for prop, oper, val in commentFilts:
                self.constructFilterTableWidgets("Comment", prop, oper, val, operMap, row)
                row += 1
            connectorText = findKey(connectMap, connector)
            for row in range(self.filterTable.rowCount() - 1):
                ConnectCombobox.text = connectorText # Set this to whatever the connector is currently so on creation of new ones, it doesn't default to And
                print("adding connector for row: " + str(row))
                connectCombobox = ConnectCombobox(row, self.filterTable, self.filtTableConnectCol, self.connectMap)
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


    def addFilter(self, row, col, type="Submission"):
        if col == self.filtTableTypeCol:
            operCombobox = OperCombobox(row)
            propCombobox = PropCombobox(row, operCombobox, self.validOperForPropMap)
            typeCombobox = TypeCombobox(row, propCombobox)
            typeCombobox.setCurrentIndex(typeCombobox.findText(type))
            textEdit = QPlainTextEdit()
            self.filterTable.setCellWidget(row, self.filtTableTypeCol, typeCombobox)
            self.filterTable.setCellWidget(row, self.filtTablePropCol, propCombobox)
            self.filterTable.setCellWidget(row, self.filtTableOperCol, operCombobox)
            self.filterTable.setCellWidget(row, self.filtTableValCol, textEdit)
        elif col == self.filtTableConnectCol:
            connectCombobox = ConnectCombobox(row, self.filterTable, self.filtTableConnectCol, self.connectMap)
            self.filterTable.setCellWidget(row, self.filtTableConnectCol, connectCombobox)
            self.filterTable.insertRow(row + 1)
            self.addFilter(row + 1, self.filtTableTypeCol, "Submission")

    def checkFilterTable(self):
        if self.filterExternalContentCheckBox.isChecked() or self.filterSubmissionContentCheckBox.isChecked():
            for row in range(self.filterTable.rowCount()):
                if self.filterTable.cellWidget(row, self.filtTableValCol) is None or len(self.filterTable.cellWidget(row, self.filtTableValCol).toPlainText()) <= 0:
                    QMessageBox.warning(QMessageBox(), "Reddit Data Extractor", "Please enter text in the value column or uncheck that you would like to filter content.")
                    return False
        return True

    def accept(self):
        if self.checkFilterTable():
            super().accept()

