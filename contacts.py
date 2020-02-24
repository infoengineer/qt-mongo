import pymongo
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId

from PySide2.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide2.QtGui import QGuiApplication, QIcon
from PySide2.QtWidgets import (
    QApplication, QMainWindow, QAction, QTableView, QHeaderView, QMessageBox)
import sys

URI = 'mongodb://localhost:27017/'
DATABASENAME = 'contacts2'
TABLE = 'contacts2'

g_database = None


class QMongoDatabase():

    def __init__(self):
        self.client = None
        self.database_name = None
        self.uri = None
        self.host = None
        self.port = None

    def setUri(self, uri):
        self.uri = uri

    def setHostPort(self, host, port):
        self.host, self.port = host, port

    def setDatabaseName(self, database_name):
        self.database_name = database_name

    def open(self):
        global g_database
        if self.host and self.port:
            self.client = pymongo.MongoClient(self.host, self.port)
        elif self.uri:
            self.client = pymongo.MongoClient(self.uri)
        else:
            self.client = pymongo.MongoClient()

        try:
            self.client.admin.command('ismaster')
            g_database = self.client[self.database_name]
            return True
        except ConnectionFailure:
            return False

    def close(self):
        self.client.close()


class QMongoModel(QAbstractTableModel):

    def __init__(self):
        super().__init__()
        self.table = []
        self.contacts = None
        self.headerdata = ['Id', ]
        self.columns = ['_id', ]

    def setTable(self, table_name):
        global g_database
        self.contacts = g_database[table_name]

    def select(self):
        self.beginResetModel()
        self.table = [
            list(contact.values()) for contact in self.contacts.find()
        ]
        self.endResetModel()

    def insertRow(self, count, parent=QModelIndex()):
        if '' in [x[0] for x in self.table]:
            return False
        self.beginInsertRows(parent, count, count)
        self.table.append([''] * len(self.columns))
        self.endInsertRows()
        return True

    def removeRow(self, row, parent=QModelIndex()):
        self.beginRemoveRows(parent, row, row)
        del_row = self.table.pop(row)
        _id = del_row[0]
        if _id:
            self.contacts.delete_one({'_id': ObjectId(_id)})
        self.endRemoveRows()
        return True

    def rowCount(self, parent=QModelIndex):
        return len(self.table)

    def columnCount(self, parent=QModelIndex):
        return len(self.columns)

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        self.headerdata.append(value)
        self.columns.append(value.replace(' ', '').lower())

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headerdata[section]
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            _id = self.table[section][0]
            if _id:
                return section + 1
            else:
                return '*'
        return None

    def data(self, index=QModelIndex, role=None):
        if not index.isValid:
            return None
        elif role != Qt.DisplayRole and role != Qt.EditRole:
            return None
        return str(self.table[index.row()][index.column()])

    def setData(self, index, value, role=None):
        if role != Qt.EditRole:
            return False
        self.table[index.row()][index.column()] = value
        _id = self.table[index.row()][0]
        if _id and self.contacts.count_documents({'_id': ObjectId(_id)}) > 0:
            self.contacts.update_one(
                {'_id': ObjectId(_id)},
                {'$set': {self.columns[index.column()]: value}})
        else:
            contact = dict(zip(self.columns[1:], self.table[index.row()][1:]))
            self.contacts.insert_one(contact)
        self.select()
        return True

    def sort(self, col, order=Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        reverse = order == Qt.AscendingOrder
        self.table = sorted(self.table, key=lambda x: x[col], reverse=reverse)
        self.layoutChanged.emit()

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable


class App(QMainWindow):

    def __init__(self, db, model, view):
        super().__init__()
        self.db = db
        self.model = model
        self.view = view
        self.title = 'Contacts'
        self.width = self.frameGeometry().width()
        self.height = self.frameGeometry().height()
        self.initUI()

    def initUI(self):

        self.setCentralWidget(self.view)

        screen = QGuiApplication.primaryScreen()
        screenGeometry = screen.geometry()
        screenHeight = screenGeometry.height()
        screenWidth = screenGeometry.width()

        self.setGeometry(
            (screenWidth/2)-(self.width/2),
            (screenHeight/2)-(self.height/2),
            self.width, self.height)

        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon('contacts.png'))
        self.statusBar().showMessage('Ready')

        newAction = QAction(QIcon('add.png'), '&Add', self)
        newAction.setShortcut('Ins')
        newAction.setStatusTip('New contact')
        newAction.triggered.connect(self.addrow)
        delAction = QAction(QIcon('delete.png'), '&Delete', self)
        delAction.setShortcut('Del')
        delAction.setStatusTip('Delete contact')
        delAction.triggered.connect(self.delrow)
        refreshAction = QAction(QIcon('refresh.png'), '&Refresh', self)
        refreshAction.setShortcut('F5')
        refreshAction.setStatusTip('Refresh')
        refreshAction.triggered.connect(self.refresh)
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('&Database')
        self.fileMenu.addAction(refreshAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(exitAction)
        self.fileMenu = self.menubar.addMenu('&Contact')
        self.fileMenu.addAction(newAction)
        self.fileMenu.addAction(delAction)

        self.toolbar = self.addToolBar('Contacts')
        self.toolbar.addAction(refreshAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(newAction)
        self.toolbar.addAction(delAction)
        self.toolbar.addSeparator()
        self.toolbar.addAction(exitAction)

        self.show()

    def addrow(self):
        self.model.insertRow(self.model.rowCount())

    def delrow(self):
        reply = QMessageBox.question(
            self,
            'Attention',
            'The record will be deleted. Are you really sure?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.model.removeRow(self.view.currentIndex().row())

    def refresh(self):
        self.model.select()

    def closeEvent(self, event):
        self.db.close()


class XQTableView(QTableView):

    def __init__(self):
        super().__init__()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.model().select()


if __name__ == '__main__':

    app = QApplication(sys.argv)

    db = QMongoDatabase()
    db.setUri(URI)
    db.setDatabaseName(DATABASENAME)
    if not db.open():
        QMessageBox.critical(
            None,
            'Cannot open database',
            'Unable to establish a database connection.\n'
            'This example needs MongoDB support. Please read the MongoDB '
            'documentation for information how to build it.\n\n'
            'Click Cancel to exit.',
            QMessageBox.Cancel
        )
        sys.exit(1)

    model = QMongoModel()
    model.setTable(TABLE)
    model.select()
    model.setHeaderData(0, Qt.Horizontal, 'First name')
    model.setHeaderData(1, Qt.Horizontal, 'Last name')
    model.setHeaderData(2, Qt.Horizontal, 'Address')
    model.setHeaderData(3, Qt.Horizontal, 'Phone')
    model.setHeaderData(4, Qt.Horizontal, 'Email')
    model.setHeaderData(5, Qt.Horizontal, 'Website url')

    view = XQTableView()
    view.setModel(model)
    view.setColumnHidden(0, True)
    view.setSortingEnabled(True)
    view.sortByColumn(0, Qt.AscendingOrder)
    view.sortByColumn(1, Qt.AscendingOrder)
    view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    ex = App(db, model, view)

    sys.exit(app.exec_())
