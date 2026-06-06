import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QSplitter, QMessageBox, QWidget, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from pyqcodeeditor.QCodeEditor import QCodeEditor
from pyqcodeeditor.highlighters import QCXXHighlighter
from pyqcodeeditor.completers import QCXXCompleter
import html
import re


class ExamAnswerDialog(QDialog):
    """答题界面"""
    def __init__(self, question, exam_id, db, parent=None):
        super().__init__(parent)
        self.question = question
        self.exam_id = exam_id
        self.db = db
        self.question_id = question.get("qid", 0)

        self.setup_ui()
        self.load_saved_code()

    def is_dark_mode(self):
        #判断是否为深色模式
        style_hints = QGuiApplication.styleHints()
        return style_hints.colorScheme() == Qt.ColorScheme.Dark

    def setup_ui(self):
        if self.is_dark_mode():
            self.setStyleSheet("""
                QDialog {
                    background-color: #2d2d2d;
                    color: #a0a0a0;
                }
                QLabel {
                    color: #a0a0a0;
                }
                QTextEdit {
                    background-color: #3c3c3c;
                    color: #a0a0a0;
                    border: 1px solid #555;
                }
                QPlainTextEdit {
                    background-color: #3c3c3c;
                    color: #a0a0a0;
                    border: 1px solid #555;
                }
                QPushButton {
                    background-color: #555;
                    color: #a0a0a0;
                    border: none;
                    padding: 6px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #666;
                }
            """)
        else:
            self.setStyleSheet("""
                QTextEdit, QPlainTextEdit {
                border: 1px solid #ddd;
                }
            """)
        self.setWindowTitle(f"答题 - {self.question.get('title', '未命名题目')}")
        self.resize(900, 700)

        layout = QVBoxLayout(self)

        # 主分割器（上下分割：题目描述在上，代码编辑器在下）
        splitter = QSplitter(Qt.Vertical)

        # 题目描述区域
        self.problem_text = QTextEdit()
        self.problem_text.setReadOnly(True)
        self.problem_text.setHtml(self.format_problem_html())
        splitter.addWidget(self.problem_text)

        # 代码编辑区域
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        editor_layout.addWidget(QLabel("代码编辑区："))

        self.code_editor = QCodeEditor()
        self.code_editor.setHighlighter(QCXXHighlighter())
        self.code_editor.setCompleter(QCXXCompleter())


        # 设置代码模板
        code_template = self.question.get("user_view", {}).get("code_template", "")
        if code_template:
            self.code_editor.setPlainText(code_template)

        editor_layout.addWidget(self.code_editor)

        splitter.addWidget(editor_widget)

        # 设置分割比例（60% 题目描述，40% 代码编辑）
        splitter.setSizes([int(self.height() * 0.6), int(self.height() * 0.4)])

        layout.addWidget(splitter)

        # 按钮区域
        btn_layout = QHBoxLayout()

        self.submit_btn = QPushButton("提交")
        self.submit_btn.clicked.connect(self.submit_code)

        self.save_btn = QPushButton("保存草稿")
        self.save_btn.clicked.connect(self.save_draft)

        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close_and_save)

        btn_layout.addStretch()
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def format_problem_html(self):
        """格式化题目描述为 HTML，支持 Markdown 代码块"""
        user_view = self.question.get("user_view", {})
        problem_statement = user_view.get("problem_statement", "")
        submit_instruction = user_view.get("submit_instruction", "")
        code_template = user_view.get("code_template", "")

        qtype = self.question.get("question_type", "")
        type_name = {"short_blank": "短代码补全", "long_blank": "长代码补全", "rewrite": "从零重写"}.get(qtype, qtype)

        title_escaped = html.escape(self.question.get('title', ''))
        submit_instruction_escaped = html.escape(submit_instruction).replace("\n", "<br>")
        code_template_escaped = html.escape(code_template)

        # 处理 problem_statement：将 Markdown 代码块转换为 HTML
        problem_statement_html = self.markdown_to_html(problem_statement)

        # 代码模板部分
        code_html = ""
        if code_template:
            code_html = f"""
            <div class="code-block">
                <b>代码模板：</b>
                <pre>{code_template_escaped}</pre>
            </div>
            """

        # 根据深色模式设置 CSS
        if self.is_dark_mode():
            css = """
                body {
                    background-color: #2d2d2d;
                    color: #d4d4d4;
                    font-family: Arial, sans-serif;
                    margin: 15px;
                }
                h1 { color: #ffffff; }
                .type { color: #66d9ef; font-size: 14px; margin-bottom: 10px; }
                .statement { margin-top: 15px; line-height: 1.5; }
                .instruction { margin-top: 15px; padding: 10px; background-color: #3c3c3c; border-radius: 5px; }
                .code-block { margin-top: 15px; }
                pre {
                    background-color: #3c3c3c;
                    color: #d4d4d4;
                    padding: 10px;
                    border-radius: 5px;
                    font-family: 'Courier New', monospace;
                    font-size: 13px;
                    overflow-x: auto;
                }
            """
        else:
            css = """
                body {
                    font-family: Arial, sans-serif;
                    margin: 15px;
                }
                h1 { color: #2c3e50; }
                .type { color: #3498db; font-size: 14px; margin-bottom: 10px; }
                .statement { margin-top: 15px; line-height: 1.5; }
                .instruction { margin-top: 15px; padding: 10px; background-color: #f0f8ff; border-radius: 5px; }
                .code-block { margin-top: 15px; }
                pre {
                    background-color: #f5f5f5;
                    padding: 10px;
                    border-radius: 5px;
                    font-family: 'Courier New', monospace;
                    font-size: 13px;
                    overflow-x: auto;
                }
            """

        html_content = f"""
        <html>
        <head><style>{css}</style></head>
        <body>
        <h1>{title_escaped}</h1>
        <div class="type">题型：{type_name}</div>
        <div class="statement">{problem_statement_html}</div>
        {code_html}
        <div class="instruction"><b>提交说明：</b><br>{submit_instruction_escaped}</div>
        </body>
        </html>
        """
        return html_content

    def markdown_to_html(self, text):
        """将 Markdown 代码块转换为 HTML"""
        if not text:
            return ""

        # 先转义 HTML
        text = html.escape(text)

        # 匹配 ```cpp ... ``` 代码块
        pattern = r'```(?:cpp|c\+\+)?\s*\n(.*?)\n```'
        text = re.sub(pattern, r'<pre>\1</pre>', text, flags=re.DOTALL)

        # 将普通文本的换行转换为 <br>
        text = text.replace('\n', '<br>')

        return text

    def format_text_with_code(self, text):
        """将文本中的代码块用 <pre> 标签包裹，保留缩进"""
        if not text:
            return ""

        text = html.escape(text)
        lines = text.split('\n')
        result = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 检测是否是代码块开始
            # 条件：当前行不是纯文本（包含 { } ; 等代码特征），或者有缩进
            is_code_line = False
            if line.strip():
                # 有缩进 或者 包含代码特征字符
                if line.startswith(' ') or line.startswith('\t'):
                    is_code_line = True
                elif any(c in line for c in ['{', '}', ';', '(', ')', '#include', 'int ', 'void ', 'return']):
                    is_code_line = True

            if is_code_line:
                # 收集连续的代码行（直到遇到空行或明确的非代码行）
                code_lines = []
                while i < len(lines):
                    current = lines[i]
                    is_continue = False
                    if current.strip():
                        if current.startswith(' ') or current.startswith('\t'):
                            is_continue = True
                        elif any(c in current for c in ['{', '}', ';', '(', ')', '#include', 'int ', 'void ', 'return']):
                            is_continue = True

                    if is_continue or (not current.strip() and code_lines):
                        # 空行在代码块中也保留
                        code_lines.append(current)
                        i += 1
                    else:
                        break

                code_block = '\n'.join(code_lines)
                result.append(f'<pre>{code_block}</pre>')
            else:
                # 普通文本
                result.append(line if line else '')
                i += 1

        return '<br>'.join(result)

    def load_saved_code(self):
        """加载之前保存的代码"""
        attempt = self.db.get_exam_attempt(self.exam_id, self.question_id)
        if attempt and attempt.get("user_code"):
            self.code_editor.setPlainText(attempt["user_code"])

    def save_draft(self):
        """保存草稿"""
        user_code = self.code_editor.toPlainText()

        user_view = self.question.get("user_view", {})
        hidden_tests = self.question.get("hidden_tests", [])

        self.db.save_exam_attempt(
            exam_id=self.exam_id,
            question_id=self.question_id,
            question_type=self.question.get("question_type", ""),
            title=self.question.get("title", ""),
            problem_statement=user_view.get("problem_statement", ""),
            code_template=user_view.get("code_template", ""),
            user_code=user_code,
            standard_code=self.question.get("standard_code", ""),
            hidden_tests=json.dumps(hidden_tests, ensure_ascii=False)
        )

        QMessageBox.information(self, "保存成功", "草稿已保存")

    def submit_code(self):
        """提交代码并进行评判"""
        user_code = self.code_editor.toPlainText()

        # 先保存草稿
        self.save_draft()

        # 获取标准答案和隐藏测试
        standard_code = self.question.get("standard_code", "")
        hidden_tests = self.question.get("hidden_tests", [])

        if not standard_code:
            QMessageBox.warning(self, "提交失败", "缺少标准答案代码")
            return

        if not hidden_tests:
            QMessageBox.warning(self, "提交失败", "缺少测试用例")
            return

        # 显示等待提示
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("评判中...")
        QApplication.processEvents()

        # 在后台线程中评判
        from PySide6.QtCore import QThread, Signal

        class JudgeThread(QThread):
            finished = Signal(dict)

            def __init__(self, user_code, standard_code, hidden_tests):
                super().__init__()
                self.user_code = user_code
                self.standard_code = standard_code
                self.hidden_tests = hidden_tests

            def run(self):
                from app.code_judge import CodeJudge
                judge = CodeJudge()
                result = judge.judge(self.user_code, self.standard_code, self.hidden_tests)
                self.finished.emit(result)

        self.judge_thread = JudgeThread(user_code, standard_code, hidden_tests)
        self.judge_thread.finished.connect(lambda r: self.on_judge_finished(r))
        self.judge_thread.start()

    def on_judge_finished(self, result):
        """评判完成"""
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("提交")

        result_text = result.get("result", "CE")

        # 保存提交记录
        attempt = self.db.get_exam_attempt(self.exam_id, self.question_id)
        if attempt:
            self.db.add_exam_submission(attempt["id"], self.code_editor.toPlainText(), result_text)

        # 显示结果
        if result_text == "AC":
            QMessageBox.information(self, "提交结果", "✅ 答案正确！")
            self.accept()  # 关闭对话框
        elif result_text == "WA":
            failed_index = result.get("failed_test_index", 0)
            user_output = result.get("user_outputs", [])
            expected_output = result.get("expected_outputs", [])

            msg = f"❌ 答案错误\n\n"
            if failed_index < len(user_output) and failed_index < len(expected_output):
                msg += f"测试用例 {failed_index + 1}:\n"
                msg += f"你的输出：{user_output[failed_index].get('stdout', '')}\n"
                msg += f"期望输出：{expected_output[failed_index].get('stdout', '')}"

                QMessageBox.warning(self, "提交结果", msg)
        elif result_text == "RE":
            QMessageBox.warning(self, "提交结果", f"❌ 运行时错误\n\n{result.get('error_message', '')}")
        elif result_text == "TLE":
            QMessageBox.warning(self, "提交结果", "❌ 运行超时")
        else:
            QMessageBox.warning(self, "提交结果", f"❌ 编译错误\n\n{result.get('error_message', '')}")

    def close_and_save(self):
        """关闭并保存"""
        self.save_draft()
        self.accept()