from pathlib import Path
from PySide6.QtWidgets import (QFileDialog,QFileSystemModel,QMainWindow,QMessageBox,)
from ui.ui_form import Ui_MainWindow
from app.editor_manager import EditorManager
from app.cpp_runner import CppRunner
from app.panel_manager import PanelManager
from database import Database
from llm_integration import LLMIntegration
import json

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.mainstackedWidget.setCurrentWidget(self.ui.codingPage)
        self.filemodel=None
        self.setup_filetree()

        self.editor_manager=EditorManager(self.ui.editorWidget)
        self.panel_manager=PanelManager(self.ui)
        self.cpp_runner=CppRunner(self)

        self.connect_signals()



        self.test_database_and_llm()#测试用的，之后要删


    def test_database_and_llm(self):
        """测试数据库和 LLM 集成"""
        print("=" * 50)
        print("开始测试数据库和 LLM 集成")
        print("=" * 50)

        # 1. 初始化数据库（使用测试文件，避免影响正式数据）
        db = Database("test_accoach.db")
        llm_int = LLMIntegration(db)

        # ========== 测试1: 添加题目 ==========
        print("\n【测试1】添加题目")
        problem_text = """给定一个长度为 n 的整数序列，请求出它的最大连续子段和。
1 <= n <= 100000
-10000 <= ai <= 10000
样例输入：
5
1 2 -3 4 5
样例输出：
9
解释：4+5=9 是最大子段和
"""

        problem_id, analysis, problem_struct = llm_int.analyze_and_save_problem(problem_text, "最大连续子段和")
        print(f"题目添加成功，ID: {problem_id}")

        # ========== 测试2: 调试模式 ==========
        print("\n【测试2】调试模式测试")

        wrong_code = """n = int(input())
a = list(map(int, input().split()))
ans = 0
cur = 0
for x in a:
    cur = max(0, cur + x)
    ans = max(ans, cur)
print(ans)
"""

        diagnosis_id, mode, diagnosis_dict, steps = llm_int.diagnose_and_save(
            problem_id=problem_id,
            problem_text=problem_text,
            problem_analysis=analysis,
            code=wrong_code,
            program_output="9",
            expected_output="9",
            extra_info="代码在样例上能通过，但提交到 OJ 后 WA"
        )

        print(f"诊断ID: {diagnosis_id}")
        print(f"模式: {mode}")
        print(f"生成步骤数: {len(steps)}")
        if diagnosis_dict:
            print(f"错误类型: {diagnosis_dict.get('error_type', '无')}")
            print(f"错误概括: {diagnosis_dict.get('error_summary', '无')[:100]}")

        # ========== 测试3: 获取引导步骤 ==========
        print("\n【测试3】获取引导步骤")
        steps = db.get_guide_steps(diagnosis_id)
        for step in steps:
            print(f"  步骤{step['step_no']}: {step['title']}")

        print("\n" + "=" * 50)
        print("测试完成！")
        print("=" * 50)
        self.print_all_tables()

    def print_all_tables(self):
        """打印数据库中所有表的内容"""
        print("\n" + "=" * 60)
        print("数据库全部内容")
        print("=" * 60)

        db = Database("test_accoach.db")  # 使用你测试用的数据库

        # 1. problems 表
        print("\n【problems 表】")
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM problems")
        rows = cursor.fetchall()
        for row in rows:
            print(dict(row))
        conn.close()

        # 2. code_records 表
        print("\n【code_records 表】")
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM code_records")
        rows = cursor.fetchall()
        for row in rows:
            print(dict(row))
        conn.close()

        # 3. diagnoses 表
        print("\n【diagnoses 表】")
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM diagnoses")
        rows = cursor.fetchall()
        for row in rows:
            d = dict(row)
            # 截断过长的字段
            if d.get("knowledge_points"):
                d["knowledge_points"] = d["knowledge_points"][:100] + "..."
            if d.get("suspected_locations"):
                d["suspected_locations"] = d["suspected_locations"][:100] + "..."
            print(d)
        conn.close()

        # 4. guide_steps 表
        print("\n【guide_steps 表】")
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM guide_steps")
        rows = cursor.fetchall()
        for row in rows:
            print(dict(row))
        conn.close()

        # 5. mistake_library 表
        print("\n【mistake_library 表】")
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mistake_library")
        rows = cursor.fetchall()
        for row in rows:
            print(dict(row))
        conn.close()

        print("\n" + "=" * 60)
        print("打印完成")
        print("=" * 60)

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
        self.ui.projectTree.doubleClicked.connect(self.openfile)
        self.ui.act_save.triggered.connect(self.savefile)
        self.ui.act_saveall.triggered.connect(self.saveall)
        self.ui.act_new.triggered.connect(self.editor_manager.createfile)

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
        path=self.editor_manager.cur_filepath()
        if not self.editor_manager.savefile():
            QMessageBox.information(self,"Run","Save failed.")
            return
        self.panel_manager.clear_all()
        self.cpp_runner.compile_run(path)

