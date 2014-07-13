# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'downloadedPosts.ui'
#
# Created: Sun Jul 13 01:59:36 2014
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

class Ui_DownloadedPostsDialog(object):
    def setupUi(self, DownloadedPostsDialog):
        DownloadedPostsDialog.setObjectName(_fromUtf8("DownloadedPostsDialog"))
        DownloadedPostsDialog.resize(515, 412)
        self.horizontalLayout = QtGui.QHBoxLayout(DownloadedPostsDialog)
        self.horizontalLayout.setSizeConstraint(QtGui.QLayout.SetDefaultConstraint)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.downloadedPostsList = QtGui.QListWidget(DownloadedPostsDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.downloadedPostsList.sizePolicy().hasHeightForWidth())
        self.downloadedPostsList.setSizePolicy(sizePolicy)
        self.downloadedPostsList.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.downloadedPostsList.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.downloadedPostsList.setResizeMode(QtGui.QListView.Fixed)
        self.downloadedPostsList.setWordWrap(False)
        self.downloadedPostsList.setObjectName(_fromUtf8("downloadedPostsList"))
        self.horizontalLayout.addWidget(self.downloadedPostsList)

        self.retranslateUi(DownloadedPostsDialog)
        QtCore.QMetaObject.connectSlotsByName(DownloadedPostsDialog)

    def retranslateUi(self, DownloadedPostsDialog):
        DownloadedPostsDialog.setWindowTitle(_translate("DownloadedPostsDialog", "Downloaded Posts", None))

