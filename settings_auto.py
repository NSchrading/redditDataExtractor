# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'settings.ui'
#
# Created: Mon May 26 16:53:47 2014
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

