from PyQt4.Qt import *
from user import User


class UserListModel(QAbstractListModel):
    def __init__(self, users, parent=None):
        super().__init__(parent)
        self.users = users
        self.userNames = set([user.name for user in self.users])

    def swapUserNames(self, oldName, newName):
        self.userNames.remove(oldName)
        self.userNames.add(newName)
        print(self.userNames)

    def removeFromUserNames(self, name):
        self.userNames.remove(name)

    def generateUniqueUserName(self, name="New User"):
        count = 1
        uniqueName = name + " " + str(count)
        while uniqueName in self.userNames:
            count += 1
            uniqueName = name + " " + str(count)
        return uniqueName

    def rowCount(self, parent=QModelIndex()):
        return len(self.users)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.users[index.row()].name
        elif role == Qt.DecorationRole:
            return None  # can make it display a picture here
        elif role == Qt.ToolTipRole:
            return "User name: " + self.users[index.row()].name
        elif role == Qt.EditRole:
            return self.users[index.row()].name

    def getUser(self, index):
        return self.users[index.row()]

    def flags(self, index):
        # All items have these properties so we don't care about index
        return Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            row = index.row()
            user = self.users[row]
            oldName = user.name
            if value in self.userNames:
                # Can't add duplicates
                return False
            else:
                user = User(value)
                self.users[row] = user
                self.swapUserNames(oldName, value)
                self.dataChanged.emit(index, index)
                return True
        return False

    def insertRows(self, position, rows, parent=QModelIndex()):
        self.beginInsertRows(QModelIndex(), position, position + rows - 1)
        for i in range(rows):
            newName = self.generateUniqueUserName()
            newUser = User(newName)
            self.userNames.add(newName)
            self.users.insert(position, newUser)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QModelIndex()):
        self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
        for i in range(rows):
            user = self.users[position]
            self.users.remove(user)
            self.removeFromUserNames(user.name)
        self.endRemoveRows()
        return True