from PyQt4.Qt import *
from downloadedUserPosts_auto import Ui_DownloadedUserPostsDialog


class DownloadedUserPostsGUI(QDialog, Ui_DownloadedUserPostsDialog):
    def __init__(self):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)