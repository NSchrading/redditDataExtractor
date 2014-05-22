# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'downloadedUserPosts.ui'
#
# Created: Sun Mar 30 23:58:23 2014
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

class Ui_DownloadedUserPostsDialog(object):
    def setupUi(self, DownloadedUserPostsDialog):
        DownloadedUserPostsDialog.setObjectName(_fromUtf8("DownloadedUserPostsDialog"))
        DownloadedUserPostsDialog.resize(510, 397)
        self.horizontalLayout = QtGui.QHBoxLayout(DownloadedUserPostsDialog)
        self.horizontalLayout.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.downloadedUserPostsList = QtGui.QListWidget(DownloadedUserPostsDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.downloadedUserPostsList.sizePolicy().hasHeightForWidth())
        self.downloadedUserPostsList.setSizePolicy(sizePolicy)
        self.downloadedUserPostsList.setResizeMode(QtGui.QListView.Fixed)
        self.downloadedUserPostsList.setWordWrap(False)
        self.downloadedUserPostsList.setObjectName(_fromUtf8("downloadedUserPostsList"))
        self.horizontalLayout.addWidget(self.downloadedUserPostsList)

        self.retranslateUi(DownloadedUserPostsDialog)
        QtCore.QMetaObject.connectSlotsByName(DownloadedUserPostsDialog)

    def retranslateUi(self, DownloadedUserPostsDialog):
        DownloadedUserPostsDialog.setWindowTitle(_translate("DownloadedUserPostsDialog", "Downloaded Reddit Posts of a User", None))

