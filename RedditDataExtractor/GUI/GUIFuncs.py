from PyQt4.Qt import QMessageBox

def confirmDialog(message):
    msgBox = QMessageBox()
    msgBox.setText(message)
    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msgBox.setDefaultButton(QMessageBox.No)
    return msgBox