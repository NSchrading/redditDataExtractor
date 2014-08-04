# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'downloadedContent.ui'
#
# Created: Fri Jul 25 17:22:48 2014
# by: PyQt4 UI code generator 4.10.4
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


class Ui_DownloadedContentWindow(object):
    def setupUi(self, DownloadedContentWindow):
        DownloadedContentWindow.setObjectName(_fromUtf8("DownloadedContentWindow"))
        DownloadedContentWindow.resize(732, 536)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DownloadedContentWindow.sizePolicy().hasHeightForWidth())
        DownloadedContentWindow.setSizePolicy(sizePolicy)
        self.horizontalLayout = QtGui.QHBoxLayout(DownloadedContentWindow)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.userSubredditLst = QtGui.QListWidget(DownloadedContentWindow)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.userSubredditLst.sizePolicy().hasHeightForWidth())
        self.userSubredditLst.setSizePolicy(sizePolicy)
        self.userSubredditLst.setObjectName(_fromUtf8("userSubredditLst"))
        self.horizontalLayout.addWidget(self.userSubredditLst)
        self.tabWidget = QtGui.QTabWidget(DownloadedContentWindow)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.submissionJSONTab = QtGui.QWidget()
        self.submissionJSONTab.setObjectName(_fromUtf8("submissionJSONTab"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.submissionJSONTab)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.submissionJSONLst = QtGui.QListWidget(self.submissionJSONTab)
        self.submissionJSONLst.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.submissionJSONLst.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.submissionJSONLst.setObjectName(_fromUtf8("submissionJSONLst"))
        self.horizontalLayout_2.addWidget(self.submissionJSONLst)
        self.tabWidget.addTab(self.submissionJSONTab, _fromUtf8(""))
        self.submissionExternalTab = QtGui.QWidget()
        self.submissionExternalTab.setObjectName(_fromUtf8("submissionExternalTab"))
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.submissionExternalTab)
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.submissionExternalLst = QtGui.QListWidget(self.submissionExternalTab)
        self.submissionExternalLst.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.submissionExternalLst.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.submissionExternalLst.setObjectName(_fromUtf8("submissionExternalLst"))
        self.horizontalLayout_4.addWidget(self.submissionExternalLst)
        self.tabWidget.addTab(self.submissionExternalTab, _fromUtf8(""))
        self.commentTab = QtGui.QWidget()
        self.commentTab.setObjectName(_fromUtf8("commentTab"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout(self.commentTab)
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.commentLst = QtGui.QListWidget(self.commentTab)
        self.commentLst.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.commentLst.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.commentLst.setObjectName(_fromUtf8("commentLst"))
        self.horizontalLayout_5.addWidget(self.commentLst)
        self.tabWidget.addTab(self.commentTab, _fromUtf8(""))
        self.selftextTab = QtGui.QWidget()
        self.selftextTab.setObjectName(_fromUtf8("selftextTab"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.selftextTab)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.selftextLst = QtGui.QListWidget(self.selftextTab)
        self.selftextLst.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.selftextLst.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.selftextLst.setObjectName(_fromUtf8("selftextLst"))
        self.horizontalLayout_3.addWidget(self.selftextLst)
        self.tabWidget.addTab(self.selftextTab, _fromUtf8(""))
        self.horizontalLayout.addWidget(self.tabWidget)

        self.retranslateUi(DownloadedContentWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(DownloadedContentWindow)

    def retranslateUi(self, DownloadedContentWindow):
        DownloadedContentWindow.setWindowTitle(_translate("DownloadedContentWindow", "Downloaded Content", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.submissionJSONTab),
                                  _translate("DownloadedContentWindow", "Submission JSON", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.submissionExternalTab),
                                  _translate("DownloadedContentWindow", "Submission External", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.commentTab),
                                  _translate("DownloadedContentWindow", "Comment External", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.selftextTab),
                                  _translate("DownloadedContentWindow", "Selftext External", None))

