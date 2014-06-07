# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'settings.ui'
#
# Created: Fri Jun  6 21:35:47 2014
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_SettingsDialog(object):
    def setupUi(self, SettingsDialog):
        SettingsDialog.setObjectName(_fromUtf8("SettingsDialog"))
        SettingsDialog.resize(485, 356)
        self.verticalLayout = QtGui.QVBoxLayout(SettingsDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setContentsMargins(0, -1, -1, -1)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.defaultUserListLabel = QtGui.QLabel(SettingsDialog)
        self.defaultUserListLabel.setObjectName(_fromUtf8("defaultUserListLabel"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.defaultUserListLabel)
        self.defaultUserListComboBox = QtGui.QComboBox(SettingsDialog)
        self.defaultUserListComboBox.setObjectName(_fromUtf8("defaultUserListComboBox"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.defaultUserListComboBox)
        self.defaultSubredditListLabel = QtGui.QLabel(SettingsDialog)
        self.defaultSubredditListLabel.setObjectName(_fromUtf8("defaultSubredditListLabel"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.defaultSubredditListLabel)
        self.defaultSubredditListComboBox = QtGui.QComboBox(SettingsDialog)
        self.defaultSubredditListComboBox.setObjectName(_fromUtf8("defaultSubredditListComboBox"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.defaultSubredditListComboBox)
        self.avoidDuplCheckBox = QtGui.QCheckBox(SettingsDialog)
        self.avoidDuplCheckBox.setChecked(True)
        self.avoidDuplCheckBox.setObjectName(_fromUtf8("avoidDuplCheckBox"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.avoidDuplCheckBox)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(SettingsDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.hotBtn = QtGui.QRadioButton(SettingsDialog)
        self.hotBtn.setChecked(True)
        self.hotBtn.setObjectName(_fromUtf8("hotBtn"))
        self.horizontalLayout.addWidget(self.hotBtn)
        self.newBtn = QtGui.QRadioButton(SettingsDialog)
        self.newBtn.setObjectName(_fromUtf8("newBtn"))
        self.horizontalLayout.addWidget(self.newBtn)
        self.risingBtn = QtGui.QRadioButton(SettingsDialog)
        self.risingBtn.setObjectName(_fromUtf8("risingBtn"))
        self.horizontalLayout.addWidget(self.risingBtn)
        self.controversialBtn = QtGui.QRadioButton(SettingsDialog)
        self.controversialBtn.setObjectName(_fromUtf8("controversialBtn"))
        self.horizontalLayout.addWidget(self.controversialBtn)
        self.topBtn = QtGui.QRadioButton(SettingsDialog)
        self.topBtn.setObjectName(_fromUtf8("topBtn"))
        self.horizontalLayout.addWidget(self.topBtn)
        self.formLayout.setLayout(3, QtGui.QFormLayout.SpanningRole, self.horizontalLayout)
        self.label_2 = QtGui.QLabel(SettingsDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.label_2)
        self.subLimitTextEdit = QtGui.QLineEdit(SettingsDialog)
        self.subLimitTextEdit.setCursorPosition(2)
        self.subLimitTextEdit.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.subLimitTextEdit.setObjectName(_fromUtf8("subLimitTextEdit"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.subLimitTextEdit)
        self.verticalLayout.addLayout(self.formLayout)
        self.dialogButtonBox = QtGui.QDialogButtonBox(SettingsDialog)
        self.dialogButtonBox.setOrientation(QtCore.Qt.Horizontal)
        self.dialogButtonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Save)
        self.dialogButtonBox.setObjectName(_fromUtf8("dialogButtonBox"))
        self.verticalLayout.addWidget(self.dialogButtonBox)

        self.retranslateUi(SettingsDialog)
        QtCore.QObject.connect(self.dialogButtonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SettingsDialog.accept)
        QtCore.QObject.connect(self.dialogButtonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SettingsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SettingsDialog)

    def retranslateUi(self, SettingsDialog):
        SettingsDialog.setWindowTitle(_translate("SettingsDialog", "Settings", None))
        self.defaultUserListLabel.setText(_translate("SettingsDialog", "Default User List", None))
        self.defaultSubredditListLabel.setText(_translate("SettingsDialog", "Default Subreddit List", None))
        self.avoidDuplCheckBox.setText(_translate("SettingsDialog", "Avoid Downloading Duplicate Images If Possible", None))
        self.label.setText(_translate("SettingsDialog", "Sort Subreddit Content by: ", None))
        self.hotBtn.setText(_translate("SettingsDialog", "Hot", None))
        self.newBtn.setText(_translate("SettingsDialog", "New", None))
        self.risingBtn.setText(_translate("SettingsDialog", "Rising", None))
        self.controversialBtn.setText(_translate("SettingsDialog", "Controversial", None))
        self.topBtn.setText(_translate("SettingsDialog", "Top", None))
        self.label_2.setText(_translate("SettingsDialog", "Max Posts Retrieved in Subreddit Content Download [1-100]", None))
        self.subLimitTextEdit.setText(_translate("SettingsDialog", "10", None))

