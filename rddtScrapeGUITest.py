import unittest
import sys
import time
import os
import shutil
import glob
import itertools
import json
from hashlib import sha256
from redditData import RedditData, DownloadType, ListType
from queue import Queue
from listModel import ListModel
from PyQt4.QtGui import QApplication
from PyQt4.Qt import *
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt
import rddtScrapeGUI


class rddtScrapeGUIText(unittest.TestCase):
    def setUp(self):
        self.app = QApplication(sys.argv)
        rddtScraper = RedditData()
        queue = Queue()
        self.thread = QThread()
        self.recv = rddtScrapeGUI.MyReceiver(queue)
        w = rddtScrapeGUI.RddtScrapeGUI(rddtScraper, queue, self.recv)
        self.recv.mysignal.connect(w.append_text)
        self.recv.moveToThread(self.thread)
        self.thread.started.connect(self.recv.run)
        self.recv.finished.connect(self.thread.quit)
        self.recv.finished.connect(self.recv.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        self.form = w
        self.externalImageHashes = {
            '2b8tbe 1.webm': b'\xc3\xea\x97"?,A\xd9\xda\x7f4\xa8\x92\x80\xc2\xd6\\\x04\x8a\xa9iK\xdb\xf3\xd5\x90\xcf\n\xf5\x94\x15\x06',
            '2b9cfw 5.jpg': b'\xa2\x91Y\xbez\x9d\x8c\x03\x18\xa5\x83\\\xde${\xce\xe5M\x88~4\xfe2\x1a,\xe5\x10:\x07\xb9\xad\xf3',
            '2b8nag 4.jpg': b'\tW\xd6\xc5\t\xa7\xe1\xb2\xa2\xb5\x15\xad<L\x86m\x10\xa0\xab\x11s5\xdf\x7f\x9c\xb9\xd9\xb3\x8d\xc5\x03w',
            '2b9cfw 1.jpg': b'7Hs\xe6\x0b\x03\x81\x19\x80j`\xf1\xc7[\xd5\xc5%5\xb9\x92\xeac\xbd\xf6\xb4\xf0\xe5\x80s\x1f\x1a\xe6',
            '2b9cru 1.gif': b'\x1f\x85\xd9_H\xbe/TEZ\x88=\xfe\x05\xa8\xc2*\xa3\xe9\x07;\x87(o\x9d\x92\xcbFZ\xf1i\xa3',
            '2b8nag 3.jpg': b'F\xae\x95\x18\xe5\x81\xc0\x070F\xbdM\x0f\xdc:\xd4$\x99\x91s\xa4+\x82\xddm\x9f\xdf\xc9\x8c\xa8\xd7\x0f',
            '2b8nag 1.jpg': b'\xe7\xc1\xf3\x9a\xcea\x12\xea\x1b\xdeI\xe9h\nM\xd6YB\xf4\x84\x0f\x95\xbbB=n:;\xac\x9f\x8d}',
            '2b9cfw 3.jpg': b'\n\xb3\xfa\xd3^\xb9@\xcbI\x1bgw\x02V\xa9\xb3<V\xaa\x96\xfbF\xfcAL\xee&\xb4\xd8\xef\xd0b',
            '2b8vjl 1.webm': b'\xe4\xe73\xb5>\xe6\xab\x8f"\xc4.@\x1c\xc7\xee\xaf\x9c12\'\x89yPJ/K\xcf\xcc\xb6\x0b\xff\x85',
            '2b8wdl 1.gif': b'h\xd7;\r\x1a\xf9_\xa0\x04\x85(\x86\x18/!*#\x18\xca\xe9\xcc\x99\x17\xfbI\x80\x80\xd9f\xc5\x85 ',
            '2b8nag 5.jpg': b'\xc60.\x02Ox\xe4R\xcc\x07\xeb@+C\xf6\xb9N\x8e\xde}\xdb2\n8g\xf5\xf5\xa7\xcc\xcd\x8e/',
            '2b8vpe 1.gif': b'vl\xeb\xa6\x1a\xb1Q5d\xf7X\x7fN\xdc\xdbp}\x83\xd1~\xe1\xc4}\x83\x7f-\xfe\x84P\xd7\x05\xa3',
            '2b8nag 2.jpg': b'M\xd6`t^\x9c\xef s%\xdb6\x96t8\x80\x0e4\xca\xb8\xd2\xf1\x03R\x9c\x85W]o\x0f\x1f\x17',
            '2b8w9y 1.gif': b'I\x96\x85n\xfe\xa6\x8a\xe9\xde\xffzp\x82\x17\xd8\x1e\x00\xefD<\x01\xf0[9 F\x85\x83S\xdb;7',
            '2b9cfw 4.jpg': b'\xa3\x8ekJ\xe9\xc7\x0eM\xc5)Kvr\xa9\xb1\xed\xc5i\xcf=\xe8\xf1\x1a3\xb4\x84C4@\xef;\x8a',
            '2b9dm4 1.jpg': b'P\x13\x16\xca\xb1n}\xcc\x902\xd4%uXR\xc2B\xbec\x84~\xe9c\xf6Qh\x84\x82\xee\xca\xb3\xd9',
            '2b8uyr 1.webm': b'\xd6\x07r\xd0\xbbo\x12\xd1\x1b\x07\xa8:\xbf[ r\xabn<t\xa5\x84\xe3\xd4Vy_\x8e\x15\x1b\xf4<',
            '2b8s5r 1.gif': b';\x88\xe6\xf7\x038\xa3\x89\xd1\xe0\xf2\x8e\x01\x9e\xec\x1d8\x8b\x15*\x0e\xda\x0b\xd9\tAl\xa9,\x07\xa5D',
            '2b9cfw 2.jpg': b'8A\xb3\xf0\x889\x7f\xec\xa37\x10ElFD\xa4\xee\xde\xd1\xc4OI\\|\x99U\x9d\xa6\x8ev\x9e\xe9',
            '2b83a2 1.jpg': b'=\xaa\xae:\xc7\xa2K \xceT\xc6\x88\xd1\x84\xa1\x11\xdc^!\x94\x04shu\xfb\x9d7\x89\xbaE\xc4\xf5'}

        self.externalCommentImageHashes = {
            '2bby9l_comment_1 1.webm': b'\x0cN\xe1\x96\x1eo\xc8r3A\xbf{:\xba\xfa\x90\xcd\x95\xd1\xa1\xaa\xe03fP\xcb\xf6~\xfa\x9c\xd0\x07',
            '2bby9l_comment_2 1.gif': b'\xe7\xca\xa6\xe9\x0f\xb7ZPE\x82{\x9b\xd4V\x15M\x815\xa4i\xf3\xb5\xbd\xa5\xbbf@yz\xd7!\xe8',
            '2b8uyr_comment_1 1.webm': b'\xd6\x07r\xd0\xbbo\x12\xd1\x1b\x07\xa8:\xbf[ r\xabn<t\xa5\x84\xe3\xd4Vy_\x8e\x15\x1b\xf4<',
            '2bby9l_comment_3 1.jpg': b'\xa6\xc8p\x86\t\x0c\xef\xf1d\x8c\x93S\x94\xa6\xa3\xf0a\x7fp\xac\xe2\xd3Q\x17\x06\xd3\xbf)P\xfb\xf8\xf7',
            '2bby9l_comment_4 1.gif': b'\x03\xba\xa8\xdeC\xd1\xba\xb4\x84\xad[d]\x16\xff\x11\xa3\xbeb/\xbc\xfd\xa3C\xa32l\xfd\xe8y\x10h',
            '2bcnhu_comment_1 1.jpg': b'\xd5r8\xb0e\x7f\\M\xbe\x14\xe7\x13\xcd\xe4};s\xe0\x1ad\x14\x9b(H\xb1\\[/\x1b\x9b\xe8\xbe',
            '2bby9l_comment_4 2.gif': b'4\x86rl/CAq6Bn\xe8\xbc\x1fb5ie\x1c$\x88!\xb8\x9fw\x8cP\xadYs\x9bF'}

    def changeToTestConfig(self):
        listName = "test subreddit"
        self.form.subredditList.lstChooser.addItem(listName)
        self.form.subredditList.lstChooser.setCurrentIndex(self.form.subredditList.lstChooser.count() - 1)
        self.form.subredditList.chooserDict[listName] = ListModel([], self.form.subredditList.classToUse)
        self.form.subredditList.chooseNewList(self.form.subredditList.lstChooser.count() - 1)

        QTest.mouseClick(self.form.addUserBtn, Qt.LeftButton)
        index = self.form.userList.model().createIndex(0, 0)
        self.form.userList.model().setData(index, "rddt_data_extractor")
        self.assertIn("rddt_data_extractor", self.form.userList.model().stringsInLst)

        QTest.mouseClick(self.form.addSubredditBtn, Qt.LeftButton)
        index = self.form.subredditList.model().createIndex(0, 0)
        self.form.subredditList.model().setData(index, "reddit_data_extractor")
        self.assertIn("reddit_data_extractor", self.form.subredditList.model().stringsInLst)

    def testStartUpDefault(self):
        self.assertEqual(self.form.userList.lstChooser.currentText(), "Default User List")
        self.assertEqual(self.form.subredditList.lstChooser.currentText(), "Default Subs")
        self.assertEqual(self.form.userList.lstChooser.count(), 1)
        self.assertEqual(self.form.subredditList.lstChooser.count(), 1)

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


    def hashfile(self, fileName, blocksize=65536):
        hasher = sha256()
        with open(fileName, 'rb') as file:
            buf = file.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = file.read(blocksize)
        return hasher.digest()

    def compareHashes(self, fileTypes, knownGoodHashes, downloadedFilePaths):
        downloadedFilesSet = set()
        for filePath in downloadedFilePaths:
            downloadedFilesSet = downloadedFilesSet.union(
                set(itertools.chain(*[glob.glob(os.path.join(filePath, fileType)) for fileType in fileTypes])))
        hashesDownloaded = {os.path.basename(fileName): self.hashfile(fileName) for fileName in downloadedFilesSet}
        print(hashesDownloaded)
        return hashesDownloaded == knownGoodHashes

    def compareJSON(self, fileNames):
        for fileName in fileNames:
            goodJSONFilePath = os.path.join("test", "knownGoodTestFiles", fileName)
            testJSONFilePath = os.path.join("Downloads", "rddt_data_extractor", fileName)
            with open(goodJSONFilePath) as goodJSONFile:
                with open(testJSONFilePath) as testJSONFile:
                    goodJSON = json.load(goodJSONFile)
                    testJSON = json.load(testJSONFile)
                    if goodJSON != testJSON:
                        return False
        return True


    def compareJSONFiles(self, fileTypes):
        downloadedFilesSet = set(itertools.chain(
            *[glob.glob(os.path.join("Downloads", "rddt_data_extractor", fileType)) for fileType in fileTypes]))
        knownGoodJSONFilesSet = set(itertools.chain(
            *[glob.glob(os.path.join("test", "knownGoodTestFiles", fileType)) for fileType in fileTypes]))
        knownGoodJSONFiles = {os.path.basename(fileName) for fileName in knownGoodJSONFilesSet}
        filesDownloaded = {os.path.basename(fileName) for fileName in downloadedFilesSet}
        self.assertEqual(filesDownloaded, knownGoodJSONFiles)
        self.assertTrue(self.compareJSON(filesDownloaded))


    def download(self):
        QTest.mouseClick(self.form.downloadBtn, Qt.LeftButton)

        # gross workarounds for signals being missed due to not being in an event loop in the GUI
        redditorValidator = self.form.redditorValidator
        print(redditorValidator)
        maxIter = 2
        i = 0
        while len(redditorValidator.valid) <= 0 and i < maxIter:
            time.sleep(5)
            i += 1
        if len(redditorValidator.valid) > 0:
            self.form.downloadValid(redditorValidator.valid)
            i = 0
            maxIter = 50
            while not self.form.downloader.finishSignalForTest:
                self.assertTrue(i < maxIter)
                i += 1
                time.sleep(5)

            self.form.activateDownloadBtn()
            i = 0
            maxIter = 2
            while self.form.downloadBtn.text() == "Downloading..." and i < maxIter:
                time.sleep(5)
                i += 1
    def testDownloadCommentExternals(self):
        self.changeToTestConfig()
        self.form.rddtScraper.getSubmissionContent = False
        self.form.rddtScraper.getExternalContent = False
        self.form.rddtScraper.getCommentExternalContent = True
        self.download()
        fileTypes = ["*.jpg", "*.jpeg", "*.gif", "*.png", "*.webm"]
        self.assertTrue(self.compareHashes(fileTypes, self.externalCommentImageHashes,
                                           [os.path.join("Downloads", "rddt_data_extractor", "rddt_data_extractor"),
                                            os.path.join("Downloads", "rddt_data_extractor", "GfycatLinkFixerBot")]))

    def testDownloadSubmission(self):
        self.changeToTestConfig()
        self.download()
        fileTypes = ["*.txt"]
        # The order of JSON files is not always the same because it's like a dictionary. So we
        # can't use hashes. Must compare the actual JSON
        self.compareJSONFiles(fileTypes)
        shutil.rmtree(os.path.join("Downloads", "rddt_data_extractor"))

    def testDownloadExternal(self):
        self.changeToTestConfig()
        self.form.rddtScraper.getSubmissionContent = False
        self.form.rddtScraper.getExternalContent = True
        self.download()
        fileTypes = ["*.jpg", "*.jpeg", "*.gif", "*.png", "*.webm"]
        self.assertTrue(self.compareHashes(fileTypes, self.externalImageHashes, [os.path.join("Downloads", "rddt_data_extractor")]))
        shutil.rmtree(os.path.join("Downloads", "rddt_data_extractor"))


if __name__ == "__main__":
    unittest.main()
