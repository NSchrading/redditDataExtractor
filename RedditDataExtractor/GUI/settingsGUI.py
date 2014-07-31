"""
    This file is part of the reddit Data Extractor.

    The reddit Data Extractor is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    The reddit Data Extractor is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with The reddit Data Extractor.  If not, see <http://www.gnu.org/licenses/>.
"""

from PyQt4.Qt import QComboBox, Qt, QMenu, QDialog, QIntValidator, QValidator, QPlainTextEdit, QMessageBox

from .settings_auto import Ui_SettingsDialog
from .genericListModelObjects import GenericListModelObj


def findKey(dict, value):
    """
    Find a key in the dictionary given a value (the dictionary should have a 1 to 1 mapping between key and value)
    :type dict: dict
    """
    return next((k for k, v in dict.items() if v == value), None)

class ConnectCombobox(QComboBox):

    # static class variable so it can't be different for other connect comboboxes
    text = "And"

    def __init__(self, row, filterTable, filtTableConnectCol, connectMap):
        """
        A class to represent the connector (And / Or / Xor) comboboxes
        :type row: int
        :type filterTable: QTableWidget
        :type filtTableConnectCol: int
        :type connectMap: dict
        """
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
        """
        type pos: int
        """
        menu = QMenu()
        removeAction = menu.addAction("Remove")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == removeAction:
            while(self.filterTable.rowCount() > self.row + 1):
                self.filterTable.removeRow(self.filterTable.rowCount() - 1)
            self.filterTable.removeCellWidget(self.row, self.filtTableConnectCol)

    def changeAllConnects(self, index):
        """
        Change all combobox text
        """
        ConnectCombobox.text = self.currentText()
        for row in range(self.filterTable.rowCount() - 1):
            self.filterTable.removeCellWidget(row, self.filtTableConnectCol)
            combobox = ConnectCombobox(row, self.filterTable, self.filtTableConnectCol, self.connectMap)
            combobox.setCurrentIndex(self.findText(ConnectCombobox.text))
            self.filterTable.setCellWidget(row, self.filtTableConnectCol, combobox)

class TypeCombobox(QComboBox):

    def __init__(self, row, propCombobox):
        """
        A class to handle the type comboboxes and what happens when the user changes the text
        :param propCombobox: The property combobox connected to the text of the type combobox
        :type row: int
        :type propCombobox: QComboBox
        """
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
        """
        A class to handle the property comboboxes and what happens when the user changes the text
        :param operCombobox: The operator combobox connected to the text of the property combobox
        :type row: int
        :type operCombobox: QComboBox
        :type validOperForPropMap: dict
        """
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
        """
        A class to handle the operator comboboxes and what happens when the user changes the text
        :type row: int
        """
        super().__init__()
        self.row = row

    def changeOpers(self, validOpers):
        self.clear()
        for oper in validOpers:
            self.addItem(oper)


class SettingsGUI(QDialog, Ui_SettingsDialog):
    def __init__(self, rddtDataExtractor, notifyImgurAPI):
        """
        The Dialog that handles changing settings for how the program operates
        :type rddtDataExtractor: RedditDataExtractor.redditDataExtractor.RedditDataExtractor
        :type notifyImgurAPI: function
        """
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
        self.showImgurAPINotification = rddtDataExtractor.showImgurAPINotification
        self.notifyImgurAPI = notifyImgurAPI
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
        self.showImgurAPINotificationCheckBox.clicked.connect(lambda: self.changeCheckBox(self.showImgurAPINotificationCheckBox, 'showImgurAPINotification'))

        self.resetClientIdCheckBox.clicked.connect(self.notifyImgurAPI)

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
        self.showImgurAPINotificationCheckBox.setChecked(self.showImgurAPINotification)

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
        """
        Given the type, property, operation, value, operator map, and row,
        construct a row's filter table comboboxes and text edits
        :type type: str
        :type prop: str
        :type oper: str
        :type val: str
        :type operMap: dict
        :type row: int
        """
        self.addFilter(row, self.filtTableTypeCol, type)
        propCombobox = self.filterTable.cellWidget(row, self.filtTablePropCol)
        propCombobox.setCurrentIndex(propCombobox.findText(prop))
        operCombobox = self.filterTable.cellWidget(row, self.filtTableOperCol)
        operCombobox.setCurrentIndex(operCombobox.findText(findKey(operMap, oper)))
        valTextWidget = self.filterTable.cellWidget(row, self.filtTableValCol)
        valTextWidget.setPlainText(str(val))

    def constructFilterTable(self, submissionFilts, commentFilts, connector, operMap, connectMap):
        """
        Given the filters from a previous save, reconstruct the filter table
        :type submissionFilts: list
        :type commentFilts: list
        :type connector: str
        :type operMap: dict
        :type connectMap: dict
        """
        numFilts = len(submissionFilts) + len(commentFilts)
        if numFilts > 0:
            for row in range(1, numFilts): # first row is already added
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
        """
        Given the name of the setting in the SettingsGUI object, and the corresponding checkbox,
        set it to whether the checkbox is checked or not
        :type checkBox: QCheckBox
        :type setting: str
        """
        settingExists = self.__dict__.get(setting)
        if settingExists is not None:
            self.__dict__[setting] = checkBox.isChecked()

    def changeSubSort(self, subSort):
        """
        Change the sorting method for subreddits
        :type subSort: str
        """
        GenericListModelObj.subSort = subSort
        self.subSort = subSort

    def setSubLimit(self):
        text = self.subLimitTextEdit.text()
        validState = self.validator.validate(text, 0)[0]  # validate() returns a tuple, the state is the 0 index
        if validState == QValidator.Acceptable:
            self.subLimit = int(text)

    def addFilter(self, row, col, type="Submission"):
        """
        Add a whole row of filter comboboxes
        :type row: int
        :type col: int
        :type type: str
        """
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
        """
        Make sure the user entered a value in the textedit field
        """
        if self.filterExternalContentCheckBox.isChecked() or self.filterSubmissionContentCheckBox.isChecked():
            for row in range(self.filterTable.rowCount()):
                if self.filterTable.cellWidget(row, self.filtTableValCol) is None or len(self.filterTable.cellWidget(row, self.filtTableValCol).toPlainText()) <= 0:
                    QMessageBox.warning(QMessageBox(), "Data Extractor for reddit", "Please enter text in the value column or uncheck that you would like to filter content.")
                    return False
        return True

    def accept(self):
        if self.checkFilterTable():
            super().accept()

