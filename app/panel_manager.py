from PySide6.QtWidgets import QTableWidgetItem
from PySide6.QtGui import QTextCursor

class PanelManager:
    def __init__(self,ui):
        self.ui=ui

    def clear_all(self):
        self.ui.compilelogEdit.clear()
        self.ui.problemWidget.setRowCount(0)

    def append_output(self,text):
        self.ui.panelWidget.setCurrentWidget(self.ui.compilelogPage)
        edit=self.ui.compilelogEdit
        edit.moveCursor(QTextCursor.MoveOperation.End)
        edit.insertPlainText(str(text)+"\n")

    def show_problems(self,problems:list[dict]):
        self.ui.problemWidget.setRowCount(0)
        if problems:
            for problem in problems:
                table=self.ui.problemWidget
                row=table.rowCount()
                table.insertRow(row)
                table.setItem(row,0,QTableWidgetItem(str(problem.get("level", ""))))
                table.setItem(row,1,QTableWidgetItem(str(problem.get("file", ""))))
                table.setItem(row,2,QTableWidgetItem(str(problem.get("line", ""))))
                table.setItem(row,3,QTableWidgetItem(str(problem.get("column", ""))))
                table.setItem(row,4,QTableWidgetItem(str(problem.get("message", ""))))
            self.ui.panelWidget.setCurrentWidget(self.ui.problemsPage)
