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
import time
import os
import shutil
import itertools
import json
import pathlib
from hashlib import sha256
from queue import Queue

from PyQt4.Qt import *
from PyQt4.QtTest import QTest
from PyQt4.QtCore import Qt

from RedditDataExtractor.redditDataExtractor import RedditDataExtractor
from RedditDataExtractor.GUI.listModel import ListModel
from RedditDataExtractor.GUI import redditDataExtractorGUI
from RedditDataExtractor.downloader import DownloadedContentType
from main import QueueMessageReceiver


class DownloadTests(unittest.TestCase):
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
            '2b8nag 5.jpg': b'\xc60.\x02Ox\xe4R\xcc\x07\xeb@+C\xf6\xb9N\x8e\xde}\xdb2\n8g\xf5\xf5\xa7\xcc\xcd\x8e/',
            '2b8vpe 1.gif': b'vl\xeb\xa6\x1a\xb1Q5d\xf7X\x7fN\xdc\xdbp}\x83\xd1~\xe1\xc4}\x83\x7f-\xfe\x84P\xd7\x05\xa3',
            '2b8nag 2.jpg': b'M\xd6`t^\x9c\xef s%\xdb6\x96t8\x80\x0e4\xca\xb8\xd2\xf1\x03R\x9c\x85W]o\x0f\x1f\x17',
            '2b9cfw 4.jpg': b'\xa3\x8ekJ\xe9\xc7\x0eM\xc5)Kvr\xa9\xb1\xed\xc5i\xcf=\xe8\xf1\x1a3\xb4\x84C4@\xef;\x8a',
            '2b9dm4 1.jpg': b'P\x13\x16\xca\xb1n}\xcc\x902\xd4%uXR\xc2B\xbec\x84~\xe9c\xf6Qh\x84\x82\xee\xca\xb3\xd9',
            '2b8uyr 1.webm': b'\xd6\x07r\xd0\xbbo\x12\xd1\x1b\x07\xa8:\xbf[ r\xabn<t\xa5\x84\xe3\xd4Vy_\x8e\x15\x1b\xf4<',
            '2b8s5r 1.gif': b';\x88\xe6\xf7\x038\xa3\x89\xd1\xe0\xf2\x8e\x01\x9e\xec\x1d8\x8b\x15*\x0e\xda\x0b\xd9\tAl\xa9,\x07\xa5D',
            '2b9cfw 2.jpg': b'8A\xb3\xf0\x889\x7f\xec\xa37\x10ElFD\xa4\xee\xde\xd1\xc4OI\\|\x99U\x9d\xa6\x8ev\x9e\xe9',
            '2b83a2 1.jpg': b'=\xaa\xae:\xc7\xa2K \xceT\xc6\x88\xd1\x84\xa1\x11\xdc^!\x94\x04shu\xfb\x9d7\x89\xbaE\xc4\xf5',
            '2b8w9y 1.gif': b'I\x96\x85n\xfe\xa6\x8a\xe9\xde\xffzp\x82\x17\xd8\x1e\x00\xefD<\x01\xf0[9 F\x85\x83S\xdb;7',
            '2b8wdl 1.gif': b'h\xd7;\r\x1a\xf9_\xa0\x04\x85(\x86\x18/!*#\x18\xca\xe9\xcc\x99\x17\xfbI\x80\x80\xd9f\xc5\x85 ',
            '3c51k9 1.gif': b'P\x99\xb7`)\xc1\x15\xb1?\rR\x0e\xe4\xe0:H\xbdB\xf3<\x9f\x08\xd4\xa5\xeb\xc2\xa8l\r}h\x1c',
            '3c53r1 1.webm': b'O\x144\x8d\x04h\xe8\xc4\xd6-\x02\x85 \xf4cI\xb5\xd3\xd8\xe4\xa8\x85\rJ\x9f0\xf5\x92O"e\xbe'}

        self.externalCommentImageHashes = {
            '2bby9l_comment_1 1.webm': b'\x0cN\xe1\x96\x1eo\xc8r3A\xbf{:\xba\xfa\x90\xcd\x95\xd1\xa1\xaa\xe03fP\xcb\xf6~\xfa\x9c\xd0\x07',
            '2bby9l_comment_2 1.gif': b'\xe7\xca\xa6\xe9\x0f\xb7ZPE\x82{\x9b\xd4V\x15M\x815\xa4i\xf3\xb5\xbd\xa5\xbbf@yz\xd7!\xe8',
            '2bby9l_comment_3 1.jpg': b'\xa6\xc8p\x86\t\x0c\xef\xf1d\x8c\x93S\x94\xa6\xa3\xf0a\x7fp\xac\xe2\xd3Q\x17\x06\xd3\xbf)P\xfb\xf8\xf7',
            '2bby9l_comment_4 1.gif': b'\x03\xba\xa8\xdeC\xd1\xba\xb4\x84\xad[d]\x16\xff\x11\xa3\xbeb/\xbc\xfd\xa3C\xa32l\xfd\xe8y\x10h',
            '2bby9l_comment_4 2.gif': b'4\x86rl/CAq6Bn\xe8\xbc\x1fb5ie\x1c$\x88!\xb8\x9fw\x8cP\xadYs\x9bF',
            '2b8uyr_comment_1 1.webm': b'\xd6\x07r\xd0\xbbo\x12\xd1\x1b\x07\xa8:\xbf[ r\xabn<t\xa5\x84\xe3\xd4Vy_\x8e\x15\x1b\xf4<',
            '2cebx6_comment_1 1_00001.mp4': b'@\xf0\xe7"\x8e[e\xdb\xea\x9c\x9f\xd5\x004q\xf8\x1d\xa6\xcc\\\xe8pfu\xc5\xa4O\xffsU2\x87',
            '2bcnhu_comment_1 1.jpg': b'\xd5r8\xb0e\x7f\\M\xbe\x14\xe7\x13\xcd\xe4};s\xe0\x1ad\x14\x9b(H\xb1\\[/\x1b\x9b\xe8\xbe'}

        self.externalSelftextImageHashes = {
            '2bcokj_selftext_2 1.png': b"\xba\xe37g\xb1\x8f\x97\xdc\xdeB\x12S\x12\xd7\xa1\xc2g\xfbL\x18\xf698R\xa3\x06?\x0b'V\xb0\xa1",
            '2bcma6_selftext_1 1.jpg': b'\x16m\x81\x81I\x00\xa9\xd2d\xe7\xb1\xd8_o\xf9\xb8\xb1\x9ej<\xb0r\x03\xbae\x96g\x02\xfb\xa7\r\x19',
            '2bcokj_selftext_1 3.jpg': b'\xbf<\x15\x8b#\xd5\x9dZ\xa2~\x8d\xa9j\xf4\x84/\xd0K\x08-}I\xb4]9\xdc\xb3\x8d\xd1\xf9;\x95',
            '2bcnhu_selftext_1 1.jpg': b'+%\xf7\xc1\x8d\x14 J)\x84\xfc=\xf3\xeb\x943\xc7\xa8\xa3\xc8\xf8\xd6\x17;D;\x8f\xbe\xc2\xdc5%',
            '2bcokj_selftext_1 1.jpg': b'\xed\t\xd2\x02i%\xd3\x05\x8b}\x85\xb6b\x8d}\xf4J\xb6\xaa\xb6U\xadZ\xa6"_\xaf\x08\xd8[\x93}',
            '2bcokj_selftext_1 2.jpg': b'<\x00|M\xdca\xd5y&G\x10\xbf6\x81\xf4e\xb9\x86\xb9\xe9\xaaF\x9a\xbaS\xd0\xda\xa7^m\xba\xc0',
            '2cecdc_selftext_1 1_00001.mp4': b'\xdd{lG\x82h\xbbH\xf6Y~c\xc0"\xa9iq\x1d\xbd\xe2\x0c[r\\y\xa0M\x1dv\xad>\xc0'}

        self.userName = "rddt_data_extractor"

        self.userCommentExternalDownloads = {'http://i.minus.com/iZfA0KDJtn3rp.gif', 'http://i.imgur.com/kJzROu3.jpg',
                                             'http://i.imgur.com/9Zgw1z6.gif', 'http://i.imgur.com/QSwFyyg.gif',
                                             'http://i.imgur.com/kLsgG6I.jpg',
                                             'http://zippy.gfycat.com/ThankfulInfiniteAmericancrow.webm',
                                             'http://fat.gfycat.com/UnkemptInsidiousGermanshorthairedpointer.webm',
                                             'http://www.cnn.com/video/data/2.0/video/bestoftv/2013/09/20/ab-anthony-bourdain-parts-unknown-new-mexico-3.cnn.html'}
        self.userCommentRedditSubmissions = {
        'https://www.reddit.com/r/reddit_data_extractor/comments/2bby9l/textpost_no_link_comments_with_links/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8uyr/gfycat_gif_direct/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2bcnhu/textpost_link_comments_with_links/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2cebx6/selftext_no_link_comment_with_video_link/'}

        self.userSubmissionExternalDownloads = {'http://i.minus.com/ibjZuvlB5STFck.gif',
                                                'http://i.minus.com/iTML5h4UapbNx.gif',
                                                'http://www.vidble.com/g8LQqiKCVU_med.jpg',
                                                'http://i.imgur.com/YFSXROu.jpg',
                                                'https://s3.amazonaws.com/br-cdn/temp_images/2014/07/04/657f7564a8d7785b8747311b3275abaf.gif?1404508284',
                                                'http://i.imgur.com/OK2RXHQ.jpg',
                                                'http://www.vidble.com/9LPShmlZOn.jpg',
                                                'http://www.vidble.com/LckxM9EYoH_med.jpg',
                                                'http://i.imgur.com/VDjOWMx.jpg',
                                                'http://www.vidble.com/rmiqXMbpPm_med.jpg',
                                                'http://zippy.gfycat.com/ThinVastErin.webm',
                                                'http://www.vidble.com/LZNUFKV1ot_med.jpg',
                                                'http://www.vidble.com/8qzzbdcwJc_med.jpg',
                                                'http://i.imgur.com/gxePU46.jpg',
                                                'http://www.vidble.com/wjDwGwuuKB.gif',
                                                'http://zippy.gfycat.com/RightIndelibleCottonmouth.webm',
                                                'http://i.imgur.com/2wtfRlv.jpg', 'http://i.imgur.com/VpxANpN.gif',
                                                'http://i.imgur.com/X8fICEo.jpg',
                                                'http://fat.gfycat.com/UnkemptInsidiousGermanshorthairedpointer.webm',
                                                'https://www.youtube.com/watch?v=hpigjnKl7nI',
                                                'http://i.imgur.com/7i4vIHl.gif',
                                                'http://i.imgur.com/ZndFj3U.webm'}

        self.userSubmissionRedditSubmissions = {
        'https://www.reddit.com/r/reddit_data_extractor/comments/2vi2g9/youtube_video/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8w9y/minus_gif_direct/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8wdl/minus_gif_page/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8nag/imgur_album_hashtag/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8vjl/gfycat_gif_hashtag_format/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8s5r/imgur_single_gif/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b9cru/vidble_gif_page/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b9dm4/vidble_jpg_direct/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8tbe/gfycat_webm_page/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b83a2/imgur_single_direct/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8vpe/s3_amazonaws_gif_direct/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8uyr/gfycat_gif_direct/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b9cfw/vidble_album/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/3c51k9/imgur_gifv_direct/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/3c53r1/imgur_gifv_page/'}

        self.userSelftextExternalDownloads = {'http://i.imgur.com/IvvH2jQ.jpg', 'http://i.imgur.com/QnzS9se.jpg',
                                              'http://i.imgur.com/QwxVxlY.jpg', 'http://www.vidble.com/ubq1myyQQk.jpg',
                                              'http://i.imgur.com/T5CFNo4.jpg', 'http://i.imgur.com/v9Wfk4k.png',
                                              'http://www.dailymotion.com/video/x22mrag_cristiano-ronaldo-amazing-goal-bayern-munich-vs-real-madrid-0-4-29-04-2014_sport'}
        self.userSelftextRedditSubmissions = {
        'https://www.reddit.com/r/reddit_data_extractor/comments/2bcnhu/textpost_link_comments_with_links/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2bcokj/textpost_imgur_gallery_link_comments_without_links/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2bcma6/textpost_link_no_comments/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2cecdc/selftext_dailymotion_video_link_no_comments/'}

        self.userJSONExternalDownloads = set()
        self.userJSONRedditSubmissions = {
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8w9y/minus_gif_direct/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8nag/imgur_album_hashtag/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8380/imgur_single_page/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2bcnhu/textpost_link_comments_with_links/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2bcokj/textpost_imgur_gallery_link_comments_without_links/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8s5r/imgur_single_gif/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b9cru/vidble_gif_page/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b9dm4/vidble_jpg_direct/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b9cfw/vidble_album/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8wdl/minus_gif_page/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2bby9l/textpost_no_link_comments_with_links/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b9geu/textpost_no_link_comments_without_links/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b83a2/imgur_single_direct/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8vpe/s3_amazonaws_gif_direct/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b9gbo/textpost_no_link_no_comments/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8uyr/gfycat_gif_direct/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8tbe/gfycat_webm_page/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2bcma6/textpost_link_no_comments/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2b8vjl/gfycat_gif_hashtag_format/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2cebx6/selftext_no_link_comment_with_video_link/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2vi2g9/youtube_video/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/2cecdc/selftext_dailymotion_video_link_no_comments/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/3c51k9/imgur_gifv_direct/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/3c53r1/imgur_gifv_page/',
        'https://www.reddit.com/r/reddit_data_extractor/comments/3c53c6/imgur_gifv_page/' # this one was deleted... may need to remove in future
        }

        self.contentFileTypes = ["*.jpg", "*.jpeg", "*.gif", "*.png", "*.webm", "*.mp4", "*.mkv", "*.flv", "*.gifv"]
        self.jsonFileTypes = ["*.txt"]

    def tearDown(self):
        shutil.rmtree(os.path.join("Downloads", self.userName), ignore_errors=True)

    def changeToTestConfig(self):
        listName = "test subreddit"
        self.form.subredditList._lstChooser.addItem(listName)
        self.form.subredditList._lstChooser.setCurrentIndex(self.form.subredditList._lstChooser.count() - 1)
        self.form.subredditList._chooserDict[listName] = ListModel([], self.form.subredditList._classToUse)
        self.form.subredditList.chooseNewList(self.form.subredditList._lstChooser.count() - 1)

        QTest.mouseClick(self.form.addUserBtn, Qt.LeftButton)
        index = self.form.userList.model().createIndex(0, 0)
        self.form.userList.model().setData(index, self.userName)
        self.assertIn(self.userName, self.form.userList.model().stringsInLst)

        QTest.mouseClick(self.form.addSubredditBtn, Qt.LeftButton)
        index = self.form.subredditList.model().createIndex(0, 0)
        self.form.subredditList.model().setData(index, "reddit_data_extractor")
        self.assertIn("reddit_data_extractor", self.form.subredditList.model().stringsInLst)

        # Please don't steal this client-id. I don't want to get rate-limited.
        self.form._rddtDataExtractor.imgurAPIClientID = 'e0ea61b57d4c3c9'

    def hashfile(self, fileName, blocksize=65536):
        hasher = sha256()
        with fileName.open('rb') as file:
            buf = file.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = file.read(blocksize)
        return hasher.digest()

    def compareHashes(self, fileTypes, knownGoodHashes, downloadedFilePaths):
        downloadedFilesSet = set()
        for filePath in downloadedFilePaths:
            downloadedFilesSet = downloadedFilesSet.union(
                set(itertools.chain(*[filePath.glob(fileType) for fileType in fileTypes])))
        hashesDownloaded = {fileName.stem + fileName.suffix: self.hashfile(fileName) for fileName in downloadedFilesSet}
        if hashesDownloaded.get('2vi2g9_00001.mp4') is not None:
            del hashesDownloaded['2vi2g9_00001.mp4']  # Youtube hashes change :(
        print(hashesDownloaded)
        self.assertEqual(hashesDownloaded, knownGoodHashes)

    def compareJSON(self, fileNames):
        for fileName in fileNames:
            goodJSONFilePath = pathlib.Path("knownGoodTestFiles", fileName)
            testJSONFilePath = pathlib.Path("Downloads", self.userName, fileName)
            with goodJSONFilePath.open() as goodJSONFile:
                with testJSONFilePath.open() as testJSONFile:
                    goodJSON = json.load(goodJSONFile)
                    testJSON = json.load(testJSONFile)
                    # some items change by a small amount like created so check specific things that should never change
                    self.assertEqual(testJSON['subreddit_id'], goodJSON['subreddit_id'])
                    self.assertEqual(testJSON['selftext_html'], goodJSON['selftext_html'])
                    self.assertEqual(testJSON['subreddit'], goodJSON['subreddit'])
                    self.assertEqual(testJSON['is_self'], goodJSON['is_self'])
                    self.assertEqual(testJSON['domain'], goodJSON['domain'])
                    self.assertEqual(testJSON['distinguished'], goodJSON['distinguished'])
                    self.assertEqual(testJSON['url'], goodJSON['url'])
                    self.assertEqual(testJSON['comments'], goodJSON['comments'])
                    self.assertEqual(testJSON['author'], goodJSON['author'])
                    self.assertEqual(testJSON['name'], goodJSON['name'])
                    self.assertEqual(testJSON['id'], goodJSON['id'])
                    self.assertEqual(testJSON['over_18'], goodJSON['over_18'])
                    self.assertEqual(testJSON['num_comments'], goodJSON['num_comments'])
                    self.assertEqual(testJSON['selftext'], goodJSON['selftext'])
                    self.assertEqual(testJSON['thumbnail'], goodJSON['thumbnail'])
                    self.assertEqual(testJSON['title'], goodJSON['title'])
                    self.assertEqual(testJSON['permalink'], goodJSON['permalink'])


    def compareJSONFiles(self, fileTypes):
        downloadedFilesSet = set(itertools.chain(
            *[pathlib.Path("Downloads", self.userName).glob(fileType) for fileType in fileTypes]))
        knownGoodJSONFilesSet = set(itertools.chain(
            *[pathlib.Path("knownGoodTestFiles").glob(fileType) for fileType in fileTypes]))
        knownGoodJSONFiles = {pathlib.Path(fileName).stem + pathlib.Path(fileName).suffix for fileName in
                              knownGoodJSONFilesSet}
        filesDownloaded = {pathlib.Path(fileName).stem + pathlib.Path(fileName).suffix for fileName in
                           downloadedFilesSet}
        self.assertEqual(filesDownloaded, knownGoodJSONFiles)
        self.compareJSON(filesDownloaded)


    def download(self):
        QTest.mouseClick(self.form.downloadBtn, Qt.LeftButton)

        # gross workarounds for signals being missed due to not being in an event loop in the GUI
        redditorValidator = self.form.redditorValidator
        maxIter = 2
        i = 0
        while len(redditorValidator.validUsersOrSubs) <= 0 and i < maxIter:
            time.sleep(5)
            i += 1
        if len(redditorValidator.validUsersOrSubs) > 0:
            self.form.downloadValidUserOrSub(redditorValidator.validUsersOrSubs)
            i = 0
            while not self.form.downloader.finishSignalForTest:
                i += 1
                time.sleep(5)
            print("Took " + str(i) + " iterations to complete download.")

            self.form.reactivateBtns()
            i = 0
            maxIter = 2
            while self.form.downloadBtn.text() == "Downloading... Press here to stop the download (In progress downloads will continue until done)." and i < maxIter:
                time.sleep(5)
                i += 1

    def checkUser(self, userName, blacklist, externalDownloads, redditSubmissions, downloadedContentType,
                  mostRecentDownloadTimestamp=None):
        user = self.form.userList.model().lst[0]
        self.assertEqual(user.name, userName)
        self.assertEqual(user._blacklist, blacklist)
        self.assertEqual(user.externalDownloads, externalDownloads)
        self.assertEqual(set(user.redditSubmissions.keys()), redditSubmissions)
        if mostRecentDownloadTimestamp is not None:
            self.assertEqual(user._mostRecentDownloadTimestamp, mostRecentDownloadTimestamp)
        else:
            self.assertTrue(user._mostRecentDownloadTimestamp is not None)
        for key in user.redditSubmissions.keys():
            downloadedContent = user.redditSubmissions.get(key)
            self.assertEqual(len(downloadedContent), 1)
            self.assertEqual(downloadedContent[0].type, downloadedContentType)
            self.assertTrue(len(downloadedContent[0].files) > 0)
            if downloadedContentType is not DownloadedContentType.JSON_DATA:
                self.assertTrue(len(downloadedContent[0].externalDownloadURLs) > 0)
            self.assertTrue(downloadedContent[0].representativeImage is not None)

    def testDownloadCommentExternals(self):
        self.changeToTestConfig()
        self.form._rddtDataExtractor.getSubmissionContent = False
        self.form._rddtDataExtractor.getExternalContent = False
        self.form._rddtDataExtractor.getCommentExternalContent = True
        self.download()
        self.compareHashes(self.contentFileTypes, self.externalCommentImageHashes,
                           [pathlib.Path("Downloads", self.userName, self.userName),
                            pathlib.Path("Downloads", self.userName, "GfycatLinkFixerBot")])
        self.checkUser(self.userName, set(), self.userCommentExternalDownloads, self.userCommentRedditSubmissions,
                       DownloadedContentType.EXTERNAL_COMMENT_DATA)

    def testDownloadSubmission(self):
        self.changeToTestConfig()
        self.download()
        # The order of JSON files is not always the same because it's like a dictionary. So we
        # can't use hashes. Must compare the actual JSON
        self.compareJSONFiles(self.jsonFileTypes)
        self.checkUser(self.userName, set(), self.userJSONExternalDownloads, self.userJSONRedditSubmissions,
                       DownloadedContentType.JSON_DATA)

    def testDownloadExternal(self):
        self.changeToTestConfig()
        self.form._rddtDataExtractor.getSubmissionContent = False
        self.form._rddtDataExtractor.getExternalContent = True
        self.download()
        self.compareHashes(self.contentFileTypes, self.externalImageHashes, [pathlib.Path("Downloads", self.userName)])
        self.checkUser(self.userName, set(), self.userSubmissionExternalDownloads, self.userSubmissionRedditSubmissions,
                       DownloadedContentType.EXTERNAL_SUBMISSION_DATA)

    def testDownloadSelftextExternals(self):
        self.changeToTestConfig()
        self.form._rddtDataExtractor.getSubmissionContent = False
        self.form._rddtDataExtractor.getExternalContent = False
        self.form._rddtDataExtractor.getSelftextExternalContent = True
        self.download()
        self.compareHashes(self.contentFileTypes, self.externalSelftextImageHashes,
                           [pathlib.Path("Downloads", self.userName)])
        self.checkUser(self.userName, set(), self.userSelftextExternalDownloads, self.userSelftextRedditSubmissions,
                       DownloadedContentType.EXTERNAL_SELFTEXT_DATA)


if __name__ == "__main__":
    unittest.main()
