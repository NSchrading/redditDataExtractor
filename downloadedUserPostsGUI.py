from PyQt4.Qt import *
from PyQt4 import QtGui
from downloadedUserPosts_auto import Ui_DownloadedUserPostsDialog
import os
import glob


class DownloadedUserPostsGUI(QDialog, Ui_DownloadedUserPostsDialog):
    def __init__(self, user, confirmDialog, saveState):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)
        self.actionDelete_Post = QtGui.QAction(self)
        self.actionDelete_Post_And_Blacklist = QtGui.QAction(self)
        self.actionDelete_Post.setText("Delete post")
        self.actionDelete_Post_And_Blacklist.setText("Delete post and never download again")
        self.downloadedUserPostsList.addAction(self.actionDelete_Post)
        self.downloadedUserPostsList.addAction(self.actionDelete_Post_And_Blacklist)
        self.actionDelete_Post.triggered.connect(self.deletePost)
        self.actionDelete_Post_And_Blacklist.triggered.connect(self.deletePostAndBlacklist)
        self.user = user
        self.posts = []
        self.confirmDialog = confirmDialog
        self.saveState = saveState

    def deletePostAndBlacklist(self):
        selectedIndex = self.downloadedUserPostsList.currentRow()
        post = self.posts[selectedIndex]
        deleted = self.deletePost()
        if deleted:
            self.user.blacklist.add(post)
            self.saveState()

    def deletePost(self):
        selectedIndex = self.downloadedUserPostsList.currentRow()
        print(selectedIndex)
        post = self.posts[selectedIndex]
        imagePath = self.user.posts.get(post)
        imagePath = imagePath[:imagePath.rfind(" ")]  # strip out any number indicators
        fileExtension = os.path.splitext(imagePath)[1]
        images = glob.glob(imagePath + "*" + fileExtension)
        files = "".join([str(file) + "\n" for file in images])
        msgBox = self.confirmDialog(
            "This will delete these files: \n" + files + "Are you sure you want to delete them?")
        ret = msgBox.exec_()
        if ret == QMessageBox.Yes:
            del self.user.posts[post]
            self.posts.remove(post)
            item = self.downloadedUserPostsList.takeItem(selectedIndex)
            del item
            for image in images:
                os.remove(image)
            QMessageBox.information(QMessageBox(), "Reddit Scraper", "Successfully removed requested images.")
            self.saveState()
            return True
        return False