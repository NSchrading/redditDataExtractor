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