from PyQt4.Qt import QDialog, QMessageBox
from .imgurClientId_auto import Ui_ImgurClientIdDialog
from .GUIFuncs import exceptionSafeJsonRequest
import requests

class ImgurClientIdGUI(QDialog, Ui_ImgurClientIdDialog):
    def __init__(self):
        """
        A simple dialog for letting the user know that a client-id needs to be set to use album / gallery / page
        downloads from Imgur
        """
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.enterClientIdBtn.clicked.connect(self._checkClientIdLineEdit)
        self.enterLaterBtn.clicked.connect(self._enterLater)

        self._requestsSession = requests.session()
        self._requestsSession.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'

        self.imgurAPIClientID = None

    def _validClientId(self):
        headers = {'Authorization': 'Client-ID ' + self.clientIdLineEdit.text()}
        apiURL = "https://api.imgur.com/3/credits"
        json = exceptionSafeJsonRequest(self._requestsSession, apiURL, headers=headers, stream=True)
        if json is not None and json.get('data') is not None and json.get('data').get('ClientRemaining') is not None and json.get('data').get('ClientRemaining') > 0:
            return True
        return False

    def _checkClientIdLineEdit(self):
        if len(self.clientIdLineEdit.text()) <= 0:
            QMessageBox.warning(QMessageBox(), "Data Extractor for reddit", "Please enter your client-id in the box and then press 'Enter Client-id'.")
            return False
        if not self._validClientId():
            QMessageBox.warning(QMessageBox(), "Data Extractor for reddit", "The client-id you entered does not appear to be valid. Check the value and try again.")
            return False
        self.accept()
        return True

    def _enterLater(self):
        self.reject()

    def accept(self):
        self.imgurAPIClientID = self.clientIdLineEdit.text()
        super().accept()