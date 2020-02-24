import sys

from PySide2.QtCore import Qt
from PySide2.QtGui import QGuiApplication, QIcon
from PySide2.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel
from PySide2.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableView, QHeaderView, QAction  
 

def createConnection():
    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName('contacts.db')
    if not db.open():
        QMessageBox.critical(None, 'Cannot open database',
                'Unable to establish a database connection.\n'
                'This example needs SQLite support. Please read the Qt SQL '
                'driver documentation for information how to build it.\n\n'
                'Click Cancel to exit.',
                QMessageBox.Cancel)
        return False
    query = QSqlQuery()
    query.exec_('Create table if not exists contacts('
                'firstname varchar(50), lastname varchar(50),'
                'address varchar(200), phone varchar(50),'
                'email varchar(200), website varchar(200))')
    return True


def initializeModel(model):
    model.setTable('contacts')    
    model.setEditStrategy(QSqlTableModel.OnFieldChange)
    model.select()    

    model.setHeaderData(0, Qt.Horizontal, 'First name')
    model.setHeaderData(1, Qt.Horizontal, 'Last name')
    model.setHeaderData(2, Qt.Horizontal, 'Address')
    model.setHeaderData(3, Qt.Horizontal, 'Phone')
    model.setHeaderData(4, Qt.Horizontal, 'Email')
    model.setHeaderData(5, Qt.Horizontal, 'Website url')


def addrow():
    model.insertRow(model.rowCount())


def delrow():
    reply = QMessageBox.question(
        app,
        'Attention',
        'The record will be deleted. Are you really sure?',
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
    if reply == QMessageBox.Yes:
        model.removeRow(view.currentIndex().row())
        model.select()


def refresh():
    model.select()


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'Contacts'
        self.width = self.frameGeometry().width()
        self.height = self.frameGeometry().height()
        self.initUI()

    def initUI(self):

        self.setCentralWidget(view)
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
        newAction.triggered.connect(addrow)
        delAction = QAction(QIcon('delete.png'), '&Delete', self)
        delAction.setShortcut('Del')
        delAction.setStatusTip('Delete contact')
        delAction.triggered.connect(delrow)
        refreshAction = QAction(QIcon('refresh.png'), '&Refresh', self)
        refreshAction.setShortcut('F5')
        refreshAction.setStatusTip('Refresh')
        refreshAction.triggered.connect(refresh)
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


if __name__ == '__main__':

    app = QApplication(sys.argv)

    if not createConnection():
        sys.exit(1)
 
    model = QSqlTableModel()
    view = QTableView()
    view.setModel(model)
    view.setSortingEnabled(True)
    view.sortByColumn(0, Qt.AscendingOrder)
    view.sortByColumn(1, Qt.AscendingOrder)
    view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    initializeModel(model)
    ex = App()
    
    sys.exit(app.exec_())