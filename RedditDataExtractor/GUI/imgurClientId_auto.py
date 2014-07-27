# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'imgurClientId.ui'
#
# Created: Sat Jul 26 17:54:04 2014
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

class Ui_ImgurClientIdDialog(object):
    def setupUi(self, ImgurClientIdDialog):
        ImgurClientIdDialog.setObjectName(_fromUtf8("ImgurClientIdDialog"))
        ImgurClientIdDialog.resize(754, 467)
        self.gridLayout_2 = QtGui.QGridLayout(ImgurClientIdDialog)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.enterClientIdBtn = QtGui.QPushButton(ImgurClientIdDialog)
        self.enterClientIdBtn.setObjectName(_fromUtf8("enterClientIdBtn"))
        self.gridLayout_2.addWidget(self.enterClientIdBtn, 3, 0, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label_2 = QtGui.QLabel(ImgurClientIdDialog)
        self.label_2.setTextFormat(QtCore.Qt.RichText)
        self.label_2.setOpenExternalLinks(True)
        self.label_2.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout_2.addWidget(self.label_2)
        self.gridLayout_2.addLayout(self.horizontalLayout_2, 0, 0, 1, 2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(ImgurClientIdDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.clientIdLineEdit = QtGui.QLineEdit(ImgurClientIdDialog)
        self.clientIdLineEdit.setObjectName(_fromUtf8("clientIdLineEdit"))
        self.horizontalLayout.addWidget(self.clientIdLineEdit)
        self.gridLayout_2.addLayout(self.horizontalLayout, 2, 0, 1, 2)
        self.enterLaterBtn = QtGui.QPushButton(ImgurClientIdDialog)
        self.enterLaterBtn.setObjectName(_fromUtf8("enterLaterBtn"))
        self.gridLayout_2.addWidget(self.enterLaterBtn, 3, 1, 1, 1)

        self.retranslateUi(ImgurClientIdDialog)
        QtCore.QMetaObject.connectSlotsByName(ImgurClientIdDialog)

    def retranslateUi(self, ImgurClientIdDialog):
        ImgurClientIdDialog.setWindowTitle(_translate("ImgurClientIdDialog", "Download from Imgur", None))
        self.enterClientIdBtn.setText(_translate("ImgurClientIdDialog", "Enter Client-Id", None))
        self.label_2.setText(_translate("ImgurClientIdDialog", "<html><head/><body><p><span style=\" font-size:14pt;\">In order to download album, page, or gallery images from Imgur, you must register<br/>for a client-id.</span></p><p><span style=\" font-size:10pt;\">You can download directly-linked Imgur images without one.<br/>If you do not already have an Imgur account you will also need to make an account before you are able to register for a client-id</span></p><p><a href=\"https://api.imgur.com/oauth2/addclient\"><span style=\" font-size:10pt; text-decoration: underline; color:#0000ff;\">Click here</span></a><span style=\" font-size:10pt;\"> to log in and register for a client-id.</span></p><p><span style=\" font-size:10pt;\">When you get to the &quot;Register an Application&quot; page enter these details:<br/>Application name: Reddit Data Extractor<br/>Authorization type: Anonymous usage without user authorization<br/>Authorization callback URL: (leave blank)<br/>Application website: (leave blank)<br/>Email: Your email address to send the client-id to.<br/>Description: An application that checks for the existence of Imgur images linked from Reddit and downloads them. </span></p><p><span style=\" font-size:10pt;\">Once you have logged in and registered for a client-id you will receive an email from no-reply@imgur.com.<br/>This email will contain your client-id and a client-secret.<br/>Copy and paste the client-id in the box below and enjoy all the images Imgur has to offer! </span></p><p><span style=\" font-size:10pt;\">Keep your client-secret private and do not share it with anyone.</span></p><p><span style=\" font-size:10pt;\">With your client-id you will be able to make approximately 12,500 requests per day. <br/>You can check your remaining requests for the day by selecting help &gt; View Remaining Imgur Requests. <br/>Do not exceed these limits or you may get rate-limited or blocked from downloading from Imgur.</span></p></body></html>", None))
        self.label.setText(_translate("ImgurClientIdDialog", "Imgur Client-id", None))
        self.enterLaterBtn.setText(_translate("ImgurClientIdDialog", "I don\'t care about album, gallery, or page images right now", None))

