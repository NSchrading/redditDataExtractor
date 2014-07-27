from PyQt4.Qt import QMessageBox
from contextlib import closing

def confirmDialog(message):
    """
    Make a simple Yes / No confirmation dialog box with a message
    :type message: str
    """
    msgBox = QMessageBox()
    msgBox.setText(message)
    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msgBox.setDefaultButton(QMessageBox.No)
    return msgBox

def exceptionSafeJsonRequest(requestsSession, *args, **kwargs):
    """
    Method to make requests for JSON data to the passed in url in args using
    the request session.

    :type: requests.Session
    :rtype: dict
    """
    try:
        with closing(requestsSession.get(*args, **kwargs)) as response:
            if response.status_code == 200 and 'json' in response.headers['Content-Type']:
                return response.json()
            else:
                return None
    except:
        # probably should actually do something here like log the error
        pass
    return None