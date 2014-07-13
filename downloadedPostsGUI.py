from PyQt4.Qt import *
from PyQt4 import QtGui
from downloadedPosts_auto import Ui_DownloadedPostsDialog
from downloader import DownloadedPostType
import os


class DownloadedPostsGUI(QDialog, Ui_DownloadedPostsDialog):
    def __init__(self, data, confirmDialog, saveState):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)
        self.actionDelete_Post = QtGui.QAction(self)
        self.actionDelete_Post_And_Blacklist = QtGui.QAction(self)
        self.actionDelete_Post.setText("Delete post")
        self.actionDelete_Post_And_Blacklist.setText("Delete post and never download again")
        self.downloadedPostsList.addAction(self.actionDelete_Post)
        self.downloadedPostsList.addAction(self.actionDelete_Post_And_Blacklist)
        self.actionDelete_Post.triggered.connect(self.deletePost)
        self.actionDelete_Post_And_Blacklist.triggered.connect(self.deletePostAndBlacklist)
        self.data = data
        self.posts = []
        self.confirmDialog = confirmDialog
        self.saveState = saveState

    def deletePostAndBlacklist(self):
        selectedIndex = self.downloadedPostsList.currentRow()
        postURL, type = self.posts[selectedIndex]
        deleted = self.deletePost()
        if deleted:
            self.data.blacklist.add(postURL)
            self.saveState()

    def deletePost(self):
        selectedIndex = self.downloadedPostsList.currentRow()
        print(selectedIndex)
        postURL, type = self.posts[selectedIndex]
        posts = self.data.redditPosts.get(postURL)
        for post in posts:
            if post.type == type:
                files = post.files
                fileStr = "".join([str(file) + "\n" for file in files])
                msgBox = self.confirmDialog("This will delete these files: \n" + fileStr + "Are you sure you want to delete them?")
                ret = msgBox.exec_()
                if ret == QMessageBox.Yes:
                    posts.remove(post)
                    if(len(posts) <= 0):
                        del self.data.redditPosts[postURL]
                    else:
                        self.data.redditPosts[postURL] = posts
                    for post in posts:
                        print(post.redditURL)
                    if type == DownloadedPostType.EXTERNAL_DATA:
                        del self.data.externalDownloads[postURL]
                    self.posts.remove((postURL, type))
                    item = self.downloadedPostsList.takeItem(selectedIndex)
                    del item
                    for file in files:
                        os.remove(file)
                    QMessageBox.information(QMessageBox(), "Reddit Scraper", "Successfully removed requested files.")
                    self.saveState()
                    return True
                return False
        return False