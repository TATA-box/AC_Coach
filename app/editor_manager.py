from pathlib import Path

from PySide6.QtWidgets import QTabWidget, QMessageBox, QFileDialog, QTextEdit
from PySide6.QtGui import QColor, QTextCursor, QTextFormat
from pyqcodeeditor.QCodeEditor import QCodeEditor
from pyqcodeeditor.highlighters import QCXXHighlighter
from pyqcodeeditor.completers import QCXXCompleter

from .file_manager import FileManager


class CodeEditor(QCodeEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._coach_extra_selections = []
        self._editor_extra_selections = []
        self._updating_extra_selections = False
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.setHighlighter(QCXXHighlighter())
        self.setCompleter(QCXXCompleter())

    def setExtraSelections(self, selections):
        if not hasattr(self, "_coach_extra_selections") or self._updating_extra_selections:
            super().setExtraSelections(selections)
            return

        self._editor_extra_selections = list(selections or [])
        self._apply_extra_selections()

    def set_coach_extra_selections(self, selections):
        self._coach_extra_selections = list(selections or [])
        self._apply_extra_selections()

    def clear_coach_extra_selections(self):
        self._coach_extra_selections = []
        self._apply_extra_selections()

    def _apply_extra_selections(self):
        self._updating_extra_selections = True
        try:
            super().setExtraSelections(
                self._editor_extra_selections + self._coach_extra_selections
            )
        finally:
            self._updating_extra_selections = False


class EditorManager:
    def __init__(self,_tabs:QTabWidget):
        self.tabs=_tabs
        self.file_manager=FileManager()
        self.tabs.clear()
        self.tabs.tabCloseRequested.connect(self.closefile)

    def createfile(self)->bool:
        editor=CodeEditor()
        editor.file_path=None
        editor.document().setModified(False)
        editor.document().modificationChanged.connect(
            lambda modified: self.update_tabtitle(editor, modified)
        )
        num = 1

        for i in range(self.tabs.count()):
            title = self.tabs.tabText(i)
            if title.startswith("未命名") and title.endswith(".cpp"):
                num_part = title[3:-4]  # 取出“未命名”和“.cpp”中间的部分
                if num_part.isdigit():   # 必须是纯数字
                    num = max(int(num_part), num) + 1

        filename = f"未命名{num}.cpp"

        self.tabs.setCurrentIndex(self.tabs.addTab(editor, filename))
        return True

    def openfile(self,path:Path)->bool:
        for idx in range(self.tabs.count()):
            if getattr(self.tabs.widget(idx),"file_path",None)==path:
                self.tabs.setCurrentIndex(idx)
                return True

        try:text=self.file_manager.readfile(path)
        except Exception:return False
        editor=CodeEditor()
        editor.setPlainText(text)
        editor.file_path=path
        editor.document().setModified(False)
        editor.document().modificationChanged.connect(
            lambda modified:self.update_tabtitle(editor,modified)
        )
        self.tabs.setCurrentIndex(self.tabs.addTab(editor,path.name))
        return True;

    def saveasfile(self)->bool:
        editor = self.tabs.currentWidget()
        if not editor:
            return False
        # 弹出保存对话框
        path_str, _ = QFileDialog.getSaveFileName(
            self.tabs.window(), "另存为", "", "C++ 文件 (*.cpp);;头文件 (*.h);;所有文件 (*.*)"
        )
        if not path_str:
            return False

        path = Path(path_str)
        # 写入文件
        try:
            self.file_manager.writefile(path, editor.toPlainText())
        except Exception:
            return False

        # 更新路径和标签标题
        editor.file_path = Path(path)
        editor.document().setModified(False)
        self.tabs.setTabText(self.tabs.currentIndex(), path.name)
        return True

    def savefile(self)->bool:
        editor=self.tabs.currentWidget()
        if editor is None:return False;
        path=getattr(editor,"file_path",None)

        if path is None:
            return self.saveasfile()

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
        path=getattr(editor,"file_path",None)
        if path is None:
            title = self.tabs.tabText(self.tabs.indexOf(editor))
        else:
            title = path.name
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

    def current_code(self):
        editor = self.tabs.currentWidget()
        if editor is None:
            return ""
        return editor.toPlainText()

    def highlight_lines(self, start_line, end_line):
        editor = self.tabs.currentWidget()
        if editor is None:
            return

        try:
            start_line = int(start_line)
            end_line = int(end_line)
        except Exception:
            return

        if start_line <= 0 or end_line <= 0:
            return

        if start_line > end_line:
            start_line, end_line = end_line, start_line

        selections = []

        for line_no in range(start_line, end_line + 1):
            block = editor.document().findBlockByNumber(line_no - 1)

            if not block.isValid():
                continue

            selection = QTextEdit.ExtraSelection()
            selection.cursor = QTextCursor(block)
            selection.cursor.clearSelection()
            selection.format.setBackground(QColor("#fff3cd"))
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selections.append(selection)
        editor.set_coach_extra_selections(selections)
        if selections:
            target_block = editor.document().findBlockByNumber(start_line - 1)
            if target_block.isValid():
                cursor = QTextCursor(target_block)
                editor.setTextCursor(cursor)
                if hasattr(editor, "centerCursor"):
                    editor.centerCursor()
                elif hasattr(editor, "ensureCursorVisible"):
                    editor.ensureCursorVisible()

    def clear_highlight(self):
        editor = self.tabs.currentWidget()
        if editor is not None:
            editor.clear_coach_extra_selections()




