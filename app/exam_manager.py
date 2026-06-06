from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QTextEdit, QPushButton, QCheckBox, QFrame, QLineEdit, QMessageBox
import json
import time
from app.exam_thread import ExamPaperThread

class ExamManager(QObject):
    exam_generated = Signal(object, str)
    exam_error = Signal(str)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.exam_thread = None

    def get_exam_config_dialog(self, parent):
        #考题配置相关对话框
        dialog = QDialog(parent)
        dialog.setWindowTitle("生成考题配置")
        dialog.resize(450, 500)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("试卷名称（可选）："))
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("留空则自动使用时间戳")
        layout.addWidget(name_edit)

        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        layout.addWidget(line1)

        layout.addWidget(QLabel("题目数量配置："))

        short_layout = QHBoxLayout()
        short_layout.addWidget(QLabel("短代码补全题数量（0至5）："))
        short_spin = QSpinBox()
        short_spin.setRange(0, 5)
        short_spin.setValue(2)
        short_layout.addWidget(short_spin)
        short_layout.addStretch()
        layout.addLayout(short_layout)

        long_layout = QHBoxLayout()
        long_layout.addWidget(QLabel("长代码补全题数量（0至5）："))
        long_spin = QSpinBox()
        long_spin.setRange(0, 5)
        long_spin.setValue(1)
        long_layout.addWidget(long_spin)
        long_layout.addStretch()
        layout.addLayout(long_layout)

        rewrite_layout = QHBoxLayout()
        rewrite_layout.addWidget(QLabel("从零重写题数量（0至3）："))
        rewrite_spin = QSpinBox()
        rewrite_spin.setRange(0, 3)
        rewrite_spin.setValue(1)
        rewrite_layout.addWidget(rewrite_spin)
        rewrite_layout.addStretch()
        layout.addLayout(rewrite_layout)

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        layout.addWidget(line2)

        layout.addWidget(QLabel("AI 生成设置："))
        thinking_checkbox = QCheckBox("开启深度思考（速度更慢，但效果更好）")
        thinking_checkbox.setChecked(False)
        layout.addWidget(thinking_checkbox)

        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        layout.addWidget(line3)

        layout.addWidget(QLabel("额外要求（可选）："))
        layout.addWidget(QLabel("例如：重点考数组、难度中等偏上"))
        user_prompt_edit = QTextEdit()
        user_prompt_edit.setMaximumHeight(100)
        user_prompt_edit.setPlaceholderText("输入你的额外要求...")
        layout.addWidget(user_prompt_edit)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        result = None

        def on_ok():
            nonlocal result
            exam_id = name_edit.text().strip()
            if not exam_id:
                exam_id = str(int(time.time()))

            result = {
                "exam_id": exam_id,
                "short_blank": short_spin.value(),
                "long_blank": long_spin.value(),
                "rewrite": rewrite_spin.value(),
                "user_prompt": user_prompt_edit.toPlainText().strip(),
                "thinking": "enabled" if thinking_checkbox.isChecked() else "disabled",
            }
            dialog.accept()

        def on_cancel():
            dialog.reject()

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(on_cancel)

        dialog.exec()

        return result

    def generate_exam(self, parent, error_cards, api_key_callback):
        exam_config = self.get_exam_config_dialog(parent)
        if exam_config is None:
            return False

        total = exam_config["short_blank"] + exam_config["long_blank"] + exam_config["rewrite"]
        if total == 0:
            QMessageBox.warning(parent, "生成考题", "请至少选择一道题。")
            return False

        exam_id = exam_config["exam_id"]

        self.exam_thread = ExamPaperThread(
            error_cards=error_cards,
            short_blank_count=exam_config["short_blank"],
            long_blank_count=exam_config["long_blank"],
            rewrite_count=exam_config["rewrite"],
            user_prompt=exam_config["user_prompt"],
            thinking=exam_config["thinking"],
        )
        self.exam_thread.finished.connect(lambda paper: self.exam_generated.emit(paper, exam_id))
        self.exam_thread.error.connect(self.exam_error.emit)
        self.exam_thread.start()
        return True

    def save_questions_to_db(self, exam_id, questions):
        for q in questions:
            user_view = q.get("user_view", {})
            hidden_tests = q.get("hidden_tests", [])

            self.db.save_exam_attempt(
                exam_id=exam_id,
                question_id=q.get("qid", 0),
                question_type=q.get("question_type", ""),
                title=q.get("title", ""),
                problem_statement=user_view.get("problem_statement", ""),
                code_template=user_view.get("code_template", ""),
                user_code="",  # 初始为空
                standard_code=q.get("standard_code", ""),
                hidden_tests=json.dumps(hidden_tests, ensure_ascii=False)
            )

    def get_questions_from_db(self, exam_id):
        attempts = self.db.get_all_exam_attempts(exam_id=exam_id)

        questions = []
        for a in attempts:
            q = {
                "qid": a.get("question_id"),
                "question_type": a.get("question_type"),
                "title": a.get("title"),
                "status": a.get("status", "in_progress"),
                "user_view": {
                    "problem_statement": a.get("problem_statement", ""),
                    "code_template": a.get("code_template", ""),
                    "submit_instruction": ""
                },
                "standard_code": a.get("standard_code", ""),
                "hidden_tests": json.loads(a.get("hidden_tests", "[]"))
            }
            questions.append(q)
        return questions

