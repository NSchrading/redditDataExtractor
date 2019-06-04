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

from PyQt4.Qt import QAbstractListModel, QObject, QModelIndex, Qt
from .genericListModelObjects import User, Subreddit


class ListModel(QAbstractListModel):
    def __init__(self, lst, lstObjType, parent=QObject()):
        """
        A QAbstractListModel for the ListViews in the GUI that show the Users / Subreddits
        :param list: a list of genericListModelObjects (Users or Subreddits)
        :param lstObjType: the function (constructor?) to call to make a User / Subreddit
        :type lst: list
        :type lstObjType: function
        """
        QAbstractListModel.__init__(self, parent)
        self.lst = lst
        self.lstObjType = lstObjType
        self.stringsInLst = set([lstObj.name.lower() for lstObj in self.lst])

    def swapStrs(self, oldStr, newStr):
        """
        Function called when changing the name of the user / subreddit in the list
        :type oldStr: str
        :type newStr: str
        """
        self.stringsInLst.remove(oldStr.lower())
        self.stringsInLst.add(newStr.lower())

    def removeFromStringsInLst(self, string):
        """
        Function to remove the passed in string from the stringsInLst set
        :type string: str
        """
        self.stringsInLst.remove(string.lower())

    def generateUniqueStr(self, name="New List Item"):
        """
        Function to make a new temporary name in the list guaranteed to be unique
        :rtype: str
        """
        count = 1
        uniqueName = name + " " + str(count)
        while uniqueName.lower() in self.stringsInLst:
            count += 1
            uniqueName = name + " " + str(count)
        return uniqueName

    def rowCount(self, parent=QModelIndex()):
        """
        :rtype: int
        """
        return len(self.lst)

    def data(self, index, role=Qt.DisplayRole):
        """
        Function that returns relevant data given the role.
        :type index: QModelIndex
        :type role: Qt.ItemDataRole
        """
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
        """
        :type index: QModelIndex
        :rtype: RedditDataExtractor.GUI.genericListModelObjects.GenericListModelObj
        """
        return self.lst[index.row()]

    def getIndexOfName(self, name):
        for i in range(len(self.lst)):
            obj = self.lst[i]
            if obj.name == name:
                return i
        return -1

    def flags(self, index):
        """
        All items have these properties so we don't care about index
        """
        return Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def setData(self, index, value, role=Qt.EditRole):
        """
        Function called when the user wants to set the name of the user / subreddit
        :type index: QModelIndex
        :type value: str
        :rtype: bool
        """
        if role == Qt.EditRole:
            row = index.row()
            obj = self.lst[row]
            oldName = obj.name
            value = str(value.toString())
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
        """
        Function to insert new data into the list
        :type position: int
        :type rows: int
        :rtype: bool
        """
        self.beginInsertRows(QModelIndex(), position, position + rows - 1)
        for i in range(rows):
            newName = self.generateUniqueStr()
            newObj = self.lstObjType(newName)
            self.stringsInLst.add(newName.lower())
            self.lst.insert(position, newObj)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QModelIndex()):
        """
        Function to remove data from the list
        :type position: int
        :type rows: int
        :rtype: bool
        """
        self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
        for i in range(rows):
            obj = self.lst[position]
            self.lst.remove(obj)
            self.removeFromStringsInLst(obj.name)
        self.endRemoveRows()
        return True
