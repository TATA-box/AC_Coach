from pathlib import Path

from PySide6.QtCore import QTimer,QSettings
from PySide6.QtWidgets import (QFileDialog,QFileSystemModel,QMainWindow,QMessageBox,QInputDialog,QLineEdit,)

from ui.ui_form import Ui_MainWindow
from app.editor_manager import EditorManager
from app.cpp_runner import CppRunner
from app.panel_manager import PanelManager
from app.problem_controller import ProblemController
from app.coach_service import CoachController
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

        self.problem_controller=ProblemController(
            window=self,
            editor_manager=self.editor_manager,
            db=self.db,
        )

        self.coach_controller = CoachController(
            window=self,
            editor_manager=self.editor_manager,
            db=self.db,
        )

        self.settings=QSettings("AC_coach", "AC_coach")
        self.llm_api_key=self.settings.value("deepseek/api_key","")

        self.ai_panel_default_width=390
        QTimer.singleShot(0,self.hide_ai_panel)

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

        self.ui.act_config.triggered.connect(self.config_api_key)
        self.ui.act_analyse.triggered.connect(self.summon_coach)

        self.ui.act_compile_run.triggered.connect(self.compile_run)

        self.cpp_runner.output.connect(self.panel_manager.append_output)
        self.cpp_runner.problems_ready.connect(self.panel_manager.show_problems)
        self.cpp_runner.run_context_ready.connect(self.coach_controller.set_latest_run_context)

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

    def show_ai_panel(self):
        splitter=self.ui.codingMainSplitter
        sizes=splitter.sizes()
        total=sum(sizes) if sum(sizes)>0 else splitter.width()
        tree_width=sizes[0] if len(sizes)>=1 and sizes[0]>0 else 160
        right_width=self.ai_panel_default_width
        center_width=max(450,total-tree_width-right_width)
        splitter.setSizes([tree_width,center_width,right_width])
        self.ui.aiwidget.show()
        self.ai_panel_visible=True

    def hide_ai_panel(self):
        splitter=self.ui.codingMainSplitter
        sizes=splitter.sizes()
        total=sum(sizes) if sum(sizes)>0 else splitter.width()
        tree_width=sizes[0] if len(sizes)>=1 and sizes[0]>0 else 160
        center_width=max(450,total-tree_width)
        splitter.setSizes([tree_width,center_width,0])
        self.ai_panel_visible=False

    def summon_coach(self):
        if not self.ensure_api_key():
            return
        self.show_ai_panel()
        self.coach_controller.show_config_page()

    def config_api_key(self):
        text,ok =QInputDialog.getText(
            self,
            "配置 API Key",
            "请输入 DeepSeek API Key：",
            QLineEdit.Password,
            self.llm_api_key,
        )
        if not ok:
            return False
        text=(text or "").strip()
        if not text:
            QMessageBox.warning(self,"配置 API Key","API Key 不能为空。")
            return False
        self.llm_api_key=text
        self.settings.setValue("deepseek/api_key", self.llm_api_key)
        self.settings.sync()
        QMessageBox.information(self, "配置 API Key", "API Key 已保存。")
        return True

    def ensure_api_key(self):
        self.llm_api_key = self.settings.value("deepseek/api_key", "")
        if (self.llm_api_key or "").strip():
            return True
        reply = QMessageBox.question(
            self,
            "AI 助教",
            "还没有配置 DeepSeek API Key，是否现在配置？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply != QMessageBox.Yes:
            return False
        return self.config_api_key()

