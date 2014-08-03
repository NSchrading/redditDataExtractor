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

import unittest
import sys
import pathlib
from queue import Queue

from PyQt4.Qt import *
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt

from RedditDataExtractor.redditDataExtractor import RedditDataExtractor
from RedditDataExtractor.GUI import redditDataExtractorGUI
from RedditDataExtractor.GUI.settingsGUI import SettingsGUI
from RedditDataExtractor.GUI.genericListModelObjects import GenericListModelObj
from main import QueueMessageReceiver


class GUITests(unittest.TestCase):
    def setUp(self):
        self.app = QApplication(sys.argv)
        rddtDataExtractor = RedditDataExtractor()
        rddtDataExtractor.defaultPath = pathlib.Path('Downloads')
        if not rddtDataExtractor.defaultPath.exists():
            rddtDataExtractor.defaultPath.mkdir()
        rddtDataExtractor.defaultPath = rddtDataExtractor.defaultPath.resolve()
        queue = Queue()
        self.thread = QThread()
        self.recv = QueueMessageReceiver(queue)
        w = redditDataExtractorGUI.RddtDataExtractorGUI(rddtDataExtractor, queue, self.recv)
        self.recv.queuePutSignal.connect(w.append_text)
        self.recv.moveToThread(self.thread)
        self.thread.started.connect(self.recv.run)
        self.recv.finished.connect(self.thread.quit)
        self.recv.finished.connect(self.recv.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        self.form = w

    def testStartUpDefault(self):
        self.assertEqual(self.form.userList._lstChooser.currentText(), "Default User List")
        self.assertEqual(self.form.subredditList._lstChooser.currentText(), "Default Subs")
        self.assertEqual(self.form.userList._lstChooser.count(), 1)
        self.assertEqual(self.form.subredditList._lstChooser.count(), 1)

        self.assertEqual(len(self.form.userList.model().stringsInLst), 0)
        self.assertEqual(len(self.form.subredditList.model().stringsInLst), 15)
        self.assertIn("funny", self.form.subredditList.model().stringsInLst)
        self.assertIn("gaming", self.form.subredditList.model().stringsInLst)
        self.assertIn("gifs", self.form.subredditList.model().stringsInLst)
        self.assertIn("movies", self.form.subredditList.model().stringsInLst)
        self.assertIn("music", self.form.subredditList.model().stringsInLst)
        self.assertIn("pics", self.form.subredditList.model().stringsInLst)
        self.assertIn("science", self.form.subredditList.model().stringsInLst)
        self.assertIn("technology", self.form.subredditList.model().stringsInLst)
        self.assertIn("television", self.form.subredditList.model().stringsInLst)
        self.assertIn("videos", self.form.subredditList.model().stringsInLst)
        self.assertIn("wtf", self.form.subredditList.model().stringsInLst)

    def testAddRemoveUser(self):
        QTest.mouseClick(self.form.addUserBtn, Qt.LeftButton)
        self.assertEqual(len(self.form.userList.model().stringsInLst), 1)
        self.assertIn("new list item 1", self.form.userList.model().stringsInLst)
        QTest.mouseClick(self.form.addUserBtn, Qt.LeftButton)
        self.assertEqual(len(self.form.userList.model().stringsInLst), 2)
        self.assertIn("new list item 2", self.form.userList.model().stringsInLst)
        index = self.form.userList.model().createIndex(0, 0)
        self.form.userList.model().setData(index, "rddt_data_extractor")
        self.assertNotIn("new list item 1", self.form.userList.model().stringsInLst)
        self.assertIn("rddt_data_extractor", self.form.userList.model().stringsInLst)
        index = self.form.userList.model().createIndex(1, 0)
        self.form.userList.setCurrentIndex(index)
        QTest.mouseClick(self.form.deleteUserBtn, Qt.LeftButton)
        self.assertNotIn("new list item 2", self.form.userList.model().stringsInLst)

    def testSettings(self):
        settings = SettingsGUI(self.form._rddtDataExtractor, self.form.notifyImgurAPI)

        QTest.mouseClick(settings.showImgurAPINotificationCheckBox, Qt.LeftButton)
        self.assertFalse(settings.showImgurAPINotification)
        QTest.mouseClick(settings.showImgurAPINotificationCheckBox, Qt.LeftButton)
        self.assertTrue(settings.showImgurAPINotification)

        # QTest.mousClick() doesn't work for radio buttons for some reason...
        settings.newBtn.click()
        self.assertEqual(settings.subSort, "new")
        self.assertEqual(GenericListModelObj.subSort, "new")

        settings.topBtn.click()
        self.assertEqual(settings.subSort, "top")
        self.assertEqual(GenericListModelObj.subSort, "top")

        settings.risingBtn.click()
        self.assertEqual(settings.subSort, "rising")
        self.assertEqual(GenericListModelObj.subSort, "rising")

        settings.controversialBtn.click()
        self.assertEqual(settings.subSort, "controversial")
        self.assertEqual(GenericListModelObj.subSort, "controversial")

        settings.hotBtn.click()
        self.assertEqual(settings.subSort, "hot")
        self.assertEqual(GenericListModelObj.subSort, "hot")

        QTest.mouseClick(settings.getExternalContentCheckBox, Qt.LeftButton)
        self.assertTrue(settings.getExternalContent)
        QTest.mouseClick(settings.getExternalContentCheckBox, Qt.LeftButton)
        self.assertFalse(settings.getExternalContent)

        QTest.mouseClick(settings.avoidDuplCheckBox, Qt.LeftButton)
        self.assertFalse(settings.avoidDuplicates)
        QTest.mouseClick(settings.avoidDuplCheckBox, Qt.LeftButton)
        self.assertTrue(settings.avoidDuplicates)

        QTest.mouseClick(settings.getCommentExternalContentCheckBox, Qt.LeftButton)
        self.assertTrue(settings.getCommentExternalContent)
        QTest.mouseClick(settings.getCommentExternalContentCheckBox, Qt.LeftButton)
        self.assertFalse(settings.getCommentExternalContent)

        QTest.mouseClick(settings.getSelftextExternalContentCheckBox, Qt.LeftButton)
        self.assertTrue(settings.getSelftextExternalContent)
        QTest.mouseClick(settings.getSelftextExternalContentCheckBox, Qt.LeftButton)
        self.assertFalse(settings.getSelftextExternalContent)

        QTest.mouseClick(settings.getSubmissionContentCheckBox, Qt.LeftButton)
        self.assertFalse(settings.getSubmissionContent)
        QTest.mouseClick(settings.getSubmissionContentCheckBox, Qt.LeftButton)
        self.assertTrue(settings.getSubmissionContent)

        QTest.mouseClick(settings.restrictDownloadsByCreationDateCheckBox, Qt.LeftButton)
        self.assertFalse(settings.restrictDownloadsByCreationDate)
        QTest.mouseClick(settings.restrictDownloadsByCreationDateCheckBox, Qt.LeftButton)
        self.assertTrue(settings.restrictDownloadsByCreationDate)

        QTest.mouseClick(settings.filterExternalContentCheckBox, Qt.LeftButton)
        self.assertTrue(settings.filterExternalContent)
        QTest.mouseClick(settings.filterExternalContentCheckBox, Qt.LeftButton)
        self.assertFalse(settings.filterExternalContent)

        QTest.mouseClick(settings.filterSubmissionContentCheckBox, Qt.LeftButton)
        self.assertTrue(settings.filterSubmissionContent)
        QTest.mouseClick(settings.filterSubmissionContentCheckBox, Qt.LeftButton)
        self.assertFalse(settings.filterSubmissionContent)



if __name__ == "__main__":
    unittest.main()

