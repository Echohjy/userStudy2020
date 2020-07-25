import sys
from PyQt5 import QtCore, QtGui, QtWidgets

class StartingPage(QtWidgets.QMainWindow):

    parNum = QtCore.pyqtSignal(str)

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        self.setWindowTitle("Starting")

        self.centralwidget = QtWidgets.QWidget()
        self.vl = QtWidgets.QVBoxLayout(self.centralwidget)

        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setText("Please type in your participant number:")
        self.label.setWordWrap(True)
        font = QtGui.QFont("Times", 19, QtGui.QFont.Bold)
        self.label.setFont(font)
        self.label.setFixedSize(390, 70)

        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)

        self.confirmButton = QtWidgets.QPushButton(self.centralwidget)
        self.confirmButton.setText("Confirm")
        self.confirmButton.setStyleSheet("margin: 20px; padding:5px")

        self.vl.addWidget(self.label)
        self.vl.addWidget(self.lineEdit)
        self.vl.addWidget(self.confirmButton)
        self.centralwidget.setLayout(self.vl)
        self.setCentralWidget(self.centralwidget)
        
        self.confirmButton.clicked.connect(lambda:self.comfirmEvent())

    def comfirmEvent(self):
        string = ''
        text = self.lineEdit.text()
        if (text):
            if (not text.isdigit()): 
                self.numberError()
                return
            self.parNum.emit(self.lineEdit.text())

    def numberError(self):
        # self.times.append(time.time() - self.startTime)
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Error")
        msg.setText("Please assign a number.")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    start = StartingPage()
    start.resize(400, 100)
    start.show()
    sys.exit(app.exec_())