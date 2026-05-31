from pathlib import Path

from PySide6.QtWidgets import (QFileDialog,QFileSystemModel,QMainWindow,QMessageBox,)

from ui.ui_form import Ui_MainWindow
from app.editor_manager import EditorManager
from app.cpp_runner import CppRunner
from app.panel_manager import PanelManager
from app.problem_controller import ProblemController
from database import Database


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.mainstackedWidget.setCurrentWidget(self.ui.codingPage)
        self.filemodel=None
        self.setup_filetree()

        self.db=Database()

        self.editor_manager=EditorManager(self.ui.editorWidget)
        self.panel_manager=PanelManager(self.ui)
        self.cpp_runner=CppRunner(self)

        self.problem_controller = ProblemController(
            window=self,
            editor_manager=self.editor_manager,
            db=self.db,
        )

        self.connect_signals()

    def setup_filetree(self):
        self.filemodel=QFileSystemModel(self)
        self.filemodel.setNameFilters(["*.cpp","*.c","*.h","*.hpp","*.txt","*.md"])
        self.filemodel.setNameFilterDisables(False)

    def connect_signals(self):
        self.ui.codingmodeButton.clicked.connect(self.show_codingmode)
        self.ui.reviewmodeButton.clicked.connect(self.show_reviewmode)

        self.ui.act_exit.triggered.connect(self.close)
        self.ui.act_about.triggered.connect(self.show_about)
        self.ui.act_openfolder.triggered.connect(self.openfolder)
        self.ui.act_save.triggered.connect(self.savefile)
        self.ui.act_saveall.triggered.connect(self.saveall)
        self.ui.act_new.triggered.connect(self.new_file_then_modify)

        self.ui.projectTree.doubleClicked.connect(self.openfile)

        self.ui.act_modify.triggered.connect(self.problem_controller.modify_current_problem)
        self.ui.act_check.triggered.connect(self.problem_controller.check_current_problem)

        self.ui.act_compile_run.triggered.connect(self.compile_run)

        self.cpp_runner.output.connect(self.panel_manager.append_output)
        self.cpp_runner.problems_ready.connect(self.panel_manager.show_problems)

        self.ui.act_undo.triggered.connect(self.editor_manager.undo)
        self.ui.act_redo.triggered.connect(self.editor_manager.redo)
        self.ui.act_cut.triggered.connect(self.editor_manager.cut)
        self.ui.act_copy.triggered.connect(self.editor_manager.copy)
        self.ui.act_paste.triggered.connect(self.editor_manager.paste)

    def show_codingmode(self):
        self.ui.mainstackedWidget.setCurrentWidget(self.ui.codingPage)
        self.ui.codingmodeButton.setChecked(True)
        self.ui.reviewmodeButton.setChecked(False)
        self.statusBar().showMessage("Coding Mode")
    def show_reviewmode(self):
        self.ui.mainstackedWidget.setCurrentWidget(self.ui.reviewPage)
        self.ui.codingmodeButton.setChecked(False)
        self.ui.reviewmodeButton.setChecked(True)
        self.statusBar().showMessage("Review Mode")

    def show_about(self):
        QMessageBox.information(self,"About AC_coach","pat pat")

    def openfolder(self):
        path=QFileDialog.getExistingDirectory(self,"Open Folder",str(Path.home()))
        if not path:return
        self.ui.projectTree.setModel(self.filemodel)
        self.ui.projectTree.setRootIndex(self.filemodel.setRootPath(path))
        for col in range(1,4):self.ui.projectTree.hideColumn(col)

    def openfile(self,idx):
        path=Path(self.filemodel.filePath(idx))
        success=self.editor_manager.openfile(path)
        if not success:
            QMessageBox.information(self,"Open","Open Failed")
            return
    def savefile(self):
        success=self.editor_manager.savefile()
        if not success:
            QMessageBox.information(self,"Save","Save Failed")
            return
    def saveall(self):
        success=self.editor_manager.saveall()
        if not success:
            QMessageBox.information(self,"Save","Save Failed")
            return

    def compile_run(self):
        if not self.editor_manager.savefile():
            QMessageBox.information(self,"Run","Save failed.")
            return
        path=self.editor_manager.cur_filepath()
        if path is None:
            QMessageBox.information(self, "Run", "No file to run.")
            return
        self.panel_manager.clear_all()
        self.cpp_runner.compile_run(path)

    def new_file_then_modify(self):
        success=self.editor_manager.createfile()
        if not success:
            QMessageBox.information(self, "New", "Create file failed.")
            return
        self.problem_controller.modify_current_problem()
