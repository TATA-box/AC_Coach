from pathlib import Path
from PySide6.QtWidgets import QPlainTextEdit,QTabWidget,QMessageBox
from .file_manager import FileManager

class EditorManager:
    def __init__(self,_tabs:QTabWidget):
        self.tabs=_tabs
        self.file_manager=FileManager()
        self.tabs.clear()
        self.tabs.tabCloseRequested.connect(self.closefile)

    def openfile(self,path:Path)->bool:
        for idx in range(self.tabs.count()):
            if getattr(self.tabs.widget(idx),"file_path",None)==path:
                self.tabs.setCurrentIndex(idx)
                return True

        try:text=self.file_manager.readfile(path)
        except Exception:return False
        editor=QPlainTextEdit()
        editor.setPlainText(text)
        editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        editor.file_path=path
        editor.document().setModified(False)
        editor.document().modificationChanged.connect(
            lambda modified:self.update_tabtitle(editor,modified)
        )
        self.tabs.setCurrentIndex(self.tabs.addTab(editor,path.name))
        return True;

    def savefile(self)->bool:
        editor=self.tabs.currentWidget()
        if editor is None:return False;
        path=getattr(editor,"file_path",None)
        try:self.file_manager.writefile(path,editor.toPlainText())
        except Exception:return False
        editor.document().setModified(False)
        return True

    def saveall(self)->bool:
        if self.tabs.count()==0:return False;
        allsuccess=True
        old_idx=self.tabs.currentIndex()
        for idx in range(self.tabs.count()):
            self.tabs.setCurrentIndex(idx)
            if not self.savefile():allsuccess=False
        self.tabs.setCurrentIndex(old_idx)
        return allsuccess

    def closefile(self,idx):
        editor=self.tabs.widget(idx)
        if editor.document().isModified():
            self.tabs.setCurrentIndex(idx)
            result=QMessageBox.question(
                self.tabs.window(),
                "Unsaved File",
                "This file is unsaved.Save before closing?",
                QMessageBox.StandardButton.Save
                |QMessageBox.StandardButton.Discard
                |QMessageBox.StandardButton.Cancel,
            )
            if result==QMessageBox.StandardButton.Cancel:return
            if result==QMessageBox.StandardButton.Save:
                success=self.savefile()
                if not success:
                    QMessageBox.information(self,"Save","Save Failed")
                    return
        self.tabs.removeTab(idx)
        editor.deleteLater()
        return

    def update_tabtitle(self,editor,modified):
        title=getattr(editor,"file_path",None).name
        if modified:title="*"+title
        self.tabs.setTabText(self.tabs.indexOf(editor),title)

    def undo(self):
        self.tabs.currentWidget().undo()
    def redo(self):
        self.tabs.currentWidget().redo()
    def cut(self):
        self.tabs.currentWidget().cut()
    def copy(self):
        self.tabs.currentWidget().copy()
    def paste(self):
        self.tabs.currentWidget().paste()

    def cur_filepath(self):
        return getattr(self.tabs.currentWidget(),"file_path",None)




