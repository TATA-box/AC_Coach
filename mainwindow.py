from pathlib import Path
import json

from PySide6.QtCore import QTimer,QSettings,Qt
from PySide6.QtWidgets import (QFileDialog,QFileSystemModel,QMainWindow,QMessageBox,QInputDialog,QLineEdit,
                                QWidget,QVBoxLayout,QDialog,)

from ui.ui_form import Ui_MainWindow
from app.editor_manager import EditorManager
from app.cpp_runner import CppRunner
from app.panel_manager import PanelManager
from app.problem_controller import ProblemController
from app.coach_service import CoachController
from app.review_manager import ReviewManager
from app.exam_manager import ExamManager
from app.exam_dialog import ExamListDialog
from app.exam_history_dialog import ExamHistoryDialog
from app.exam_answer_dialog import ExamAnswerDialog
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

        self.review_manager = ReviewManager(self.db, self)
        self.exam_manager = ExamManager(self.db, self)

        self.settings=QSettings("AC_coach", "AC_coach")
        self.llm_api_key=self.settings.value("deepseek/api_key","")

        self.ai_panel_default_width=390
        QTimer.singleShot(0,self.hide_ai_panel)

        self.connect_signals()

        self.setup_review_page()


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

        self.ui.refreshButton.clicked.connect(self.refresh_mistake_list)
        self.ui.generatereviewButton.clicked.connect(self.generate_review_material)
        self.ui.filterCombo.currentTextChanged.connect(self.refresh_mistake_list)
        self.ui.knowledgeCombo.currentTextChanged.connect(self.refresh_mistake_list)
        self.ui.searchEdit.textChanged.connect(self.refresh_mistake_list)
        self.ui.showexamsButton.clicked.connect(self.show_exam_history)

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
        self.refresh_mistake_list()

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

    def setup_review_page(self):
        if self.ui.scrollContent.layout() is None:
            layout = QVBoxLayout(self.ui.scrollContent)
            layout.setSpacing(10)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.addStretch()

        self.review_manager.update_knowledge_combo(self.ui.knowledgeCombo)

        self.review_manager.review_generated.connect(self.on_review_generated)
        self.review_manager.review_error.connect(self.on_review_error)

        self.exam_manager.exam_generated.connect(self.on_exam_generated)
        self.exam_manager.exam_error.connect(self.on_exam_error)

    def refresh_mistake_list(self):
        self.review_manager.refresh_mistake_list(
            self.ui.scrollContent, self.ui.statsLabel, self.ui.filterCombo,
            self.ui.knowledgeCombo, self.ui.searchEdit, self.db
        )

    def generate_review_material(self):
        self.review_manager.generate_review_material(self, self.ensure_api_key)

    def on_review_generated(self, review):
        self.ui.statsLabel.setText("复习资料生成完成")
        self.review_manager.show_review_material_dialog(
            self, review, lambda dialog: self.on_generate_exam_from_dialog(dialog)
        )

    def on_review_error(self, error_msg):
        self.ui.statsLabel.setText("复习资料生成失败")
        QMessageBox.warning(self, "生成失败", f"生成复习资料时出错：{error_msg}")

    def on_generate_exam_from_dialog(self, review_dialog):
        review_dialog.accept()
        self.generate_exam()

    def generate_exam(self):
        mistakes = self.db.get_all_mistakes(include_mastered=True)

        if not mistakes:
            QMessageBox.information(self, "生成考题", "暂无错因记录，请先进行一些调试并生成错因卡片。")
            return

        if not self.ensure_api_key():
            return

        error_cards = []
        for m in mistakes:
            card = {
                "title": m.get("error_card_title", m.get("error_type", "")),
                "error_type": m.get("error_type", ""),
                "root_cause": m.get("root_cause", ""),
                "knowledge_points": json.loads(m.get("knowledge_points", "[]")) if m.get("knowledge_points") else [],
                "wrong_code_pattern": m.get("wrong_pattern", ""),
                "priority": m.get("review_priority", "medium"),
            }
            error_cards.append(card)

        self.ui.statsLabel.setText("正在生成考题，请稍候...")
        self.exam_manager.generate_exam(self, error_cards, self.ensure_api_key)

    def on_exam_generated(self, paper, exam_id):
        self.ui.statsLabel.setText("考题生成完成")

        questions = paper.get("questions", [])
        for q in questions:
            q["status"] = "in_progress"  # 新生成的题目状态为进行中

        self.exam_manager.save_questions_to_db(exam_id, questions)

        dialog = ExamListDialog(
            title=paper.get("paper_plan", {}).get("paper_title", exam_id),
            questions=paper.get("questions", []),
            parent=self
        )

        if dialog.exec() == QDialog.Accepted:
            selected = dialog.get_selected_question()
            if selected:
                self.show_answer_interface(selected, exam_id)

    def on_exam_error(self, error_msg):
        self.ui.statsLabel.setText("考题生成失败")
        QMessageBox.warning(self, "生成失败", f"生成考题时出错：{error_msg}")

    def show_answer_interface(self, question, exam_id):
        """显示答题界面"""
        dialog = ExamAnswerDialog(question, exam_id, self.db, self)
        dialog.exec()

    def show_exam_history(self):
        """显示历史考题对话框"""
        # 从数据库获取所有历史记录
        attempts = self.db.get_all_exam_attempts()

        if not attempts:
            QMessageBox.information(self, "历史考题", "暂无历史记录")
            return

        # 按 exam_id 分组，让用户先选择哪次考试
        from collections import defaultdict
        grouped = defaultdict(list)
        for a in attempts:
            grouped[a.get("exam_id")].append(a)

        # 构建考试列表
        exams = []
        for exam_id, questions in grouped.items():
            # 统计完成情况
            total = len(questions)
            completed = sum(1 for q in questions if q.get("status") == "completed")

            exams.append({
                "exam_id": exam_id,
                "title": f"试卷 {exam_id}",
                "questions": questions,
                "progress": f"{completed}/{total}"
            })

        # 显示选择考试的对话框
        dialog = ExamHistoryDialog(exams, self.db, self)

        if dialog.exec() == QDialog.Accepted:
            selected_exam = dialog.get_selected_exam()
            if selected_exam:
                questions = self.exam_manager.get_questions_from_db(selected_exam["exam_id"])
                # 使用同一个 ExamListDialog
                dialog2 = ExamListDialog(
                    title=selected_exam["title"],
                    questions=questions,
                    db=self.db,
                    exam_id=selected_exam["exam_id"],
                    parent=self
                )

                if dialog2.exec() == QDialog.Accepted:
                    selected = dialog2.get_selected_question()
                    if selected:
                        self.show_answer_interface(selected, selected_exam["exam_id"])
