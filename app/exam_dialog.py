import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QFrame, QMessageBox
)
from PySide6.QtCore import Qt


class ExamListDialog(QDialog):
    """通用考题列表对话框，支持新生成和历史记录"""

    def __init__(self, title, questions, db=None, exam_id=None, parent=None):
        """
        title: 对话框标题
        questions: 题目列表，每个元素包含 qid, title, question_type, status 等
        db: 数据库连接（历史记录模式时需要）
        exam_id: 试卷ID（历史记录模式时需要）
        """
        super().__init__(parent)
        self.title = title
        self.questions = questions
        self.db = db
        self.exam_id = exam_id
        self.selected_question = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(self.title)
        self.resize(550, 450)

        layout = QVBoxLayout(self)

        # 标题
        layout.addWidget(QLabel(f"📝 {self.title}"))

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(line)

        # 题目列表
        layout.addWidget(QLabel("请选择要做的题目："))

        self.question_list = QListWidget()

        for q in self.questions:
            qid = q.get("qid", 0)
            qtype = q.get("question_type", "unknown")
            title = q.get("title", "未命名题目")
            status = q.get("status", "in_progress")

            type_name = {
                "short_blank": "短代码补全",
                "long_blank": "长代码补全",
                "rewrite": "从零重写"
            }.get(qtype, qtype)

            # 状态图标
            status_icon = "⏳" if status == "in_progress" else "✅"
            status_text = "进行中" if status == "in_progress" else "已完成"

            item_text = f"第{qid}题 [{type_name}] {title}  {status_icon} {status_text}"

            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, q)  # 存储题目数据
            self.question_list.addItem(item)

        layout.addWidget(self.question_list)

        # 按钮
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始答题")
        self.start_btn.setEnabled(False)
        cancel_btn = QPushButton("取消")

        btn_layout.addStretch()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # 连接信号
        self.question_list.currentRowChanged.connect(self.on_selection_changed)
        self.start_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

    def on_selection_changed(self, row):
        self.start_btn.setEnabled(row >= 0)
        if row >= 0:
            self.selected_question = self.question_list.item(row).data(Qt.UserRole)

    def get_selected_question(self):
        return self.selected_question