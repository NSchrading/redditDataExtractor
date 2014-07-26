from PyQt4.Qt import QDialog, QMessageBox
from .imgurClientId_auto import Ui_ImgurClientIdDialog
from contextlib import closing
import requests

class ImgurClientIdGUI(QDialog, Ui_ImgurClientIdDialog):
    def __init__(self):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)

        self.enterClientIdBtn.clicked.connect(self.checkClientIdLineEdit)
        self.enterLaterBtn.clicked.connect(self.enterLater)

        self.requestsSession = requests.session()
        self.requestsSession.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'

        self.imgurAPIClientID = None

    def exceptionSafeJsonRequest(self, *args, **kwargs):
        try:
            with closing(self.requestsSession.get(*args, **kwargs)) as response:
                if response.status_code == 200 and 'json' in response.headers['Content-Type']:
                    return response.json()
                else:
                    return None
        except:
            # probably should actually do something here like log the error
            pass
        return None

    def validClientId(self):
        headers = {'Authorization': 'Client-ID ' + self.clientIdLineEdit.text()}
        apiURL = "https://api.imgur.com/3/credits"
        json = self.exceptionSafeJsonRequest(apiURL, headers=headers, stream=True)
        if json is not None and json.get('data') is not None and json.get('data').get('ClientRemaining') is not None and json.get('data').get('ClientRemaining') > 0:
            return True
        return False

    def checkClientIdLineEdit(self):
        if len(self.clientIdLineEdit.text()) <= 0:
            QMessageBox.warning(QMessageBox(), "Reddit Data Extractor", "Please enter your client-id in the box and then press 'Enter Client-id'.")
            return False
        if not self.validClientId():
            QMessageBox.warning(QMessageBox(), "Reddit Data Extractor", "The client-id you entered does not appear to be valid. Check the value and try again.")
            return False
        self.accept()
        return True

    def accept(self):
        self.imgurAPIClientID = self.clientIdLineEdit.text()
        super().accept()

    def enterLater(self):
        self.reject()