from PyQt4.Qt import QAbstractListModel, QObject, QModelIndex, Qt
from .genericListModelObjects import User, Subreddit

class ListModel(QAbstractListModel):
    def __init__(self, lst, lstObjType, parent=QObject()):
        super().__init__(parent)
        self.lst = lst
        self.lstObjType = lstObjType
        self.stringsInLst = set([lstObj.name.lower() for lstObj in self.lst])

    def swapStrs(self, oldStr, newStr):
        self.stringsInLst.remove(oldStr.lower())
        self.stringsInLst.add(newStr.lower())
        print(self.stringsInLst)

    def removeFromStringsInLst(self, string):
        self.stringsInLst.remove(string.lower())

    def generateUniqueStr(self, name="New List Item"):
        count = 1
        uniqueName = name + " " + str(count)
        while uniqueName.lower() in self.stringsInLst:
            count += 1
            uniqueName = name + " " + str(count)
        return uniqueName

    def rowCount(self, parent=QModelIndex()):
        return len(self.lst)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.lst[index.row()].name
        elif role == Qt.DecorationRole:
            return None  # can make it display a picture here
        elif role == Qt.ToolTipRole:
            obj = self.lst[index.row()]
            if isinstance(obj, User):
                return "User name: " + obj.name
            elif isinstance(obj, Subreddit):
                return "Subreddit: " + obj.name
        elif role == Qt.EditRole:
            return self.lst[index.row()].name

    def getObjectInLst(self, index):
        return self.lst[index.row()]

    def getIndexOfName(self, name):
        for i in range(len(self.lst)):
            obj = self.lst[i]
            if obj.name == name:
                return i
        return -1


    def flags(self, index):
        # All items have these properties so we don't care about index
        return Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            row = index.row()
            obj = self.lst[row]
            oldName = obj.name
            if value.lower() in self.stringsInLst:
                # Can't add duplicates
                return False
            else:
                newObj = self.lstObjType(value)
                self.lst[row] = newObj
                self.swapStrs(oldName, value)
                self.dataChanged.emit(index, index)
                return True
        return False

    def insertRows(self, position, rows, parent=QModelIndex()):
        self.beginInsertRows(QModelIndex(), position, position + rows - 1)
        for i in range(rows):
            newName = self.generateUniqueStr()
            newObj = self.lstObjType(newName)
            self.stringsInLst.add(newName.lower())
            self.lst.insert(position, newObj)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QModelIndex()):
        self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
        for i in range(rows):
            obj = self.lst[position]
            self.lst.remove(obj)
            self.removeFromStringsInLst(obj.name)
        self.endRemoveRows()
        return True