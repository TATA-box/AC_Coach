import sys
from PySide6.QtWidgets import QApplication
from mainwindow import MainWindow
import database

if __name__=="__main__":
    app=QApplication(sys.argv)
    widget=MainWindow()
    widget.show()
    sys.exit(app.exec())
