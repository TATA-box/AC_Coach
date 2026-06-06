from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QFrame, QMessageBox
)
from PySide6.QtCore import Qt


class ExamHistoryDialog(QDialog):
    """历史考试选择对话框"""

    def __init__(self, exams, db, parent=None):
        super().__init__(parent)
        self.exams = exams
        self.db = db
        self.selected_exam = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("历史考试记录")
        self.resize(500, 350)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("请选择要查看的考试："))

        self.exam_list = QListWidget()

        for exam in self.exams:
            item_text = f"📋 {exam['title']}  ({exam['progress']})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, exam)
            self.exam_list.addItem(item)

        layout.addWidget(self.exam_list)

        btn_layout = QHBoxLayout()
        self.select_btn = QPushButton("选择")
        self.select_btn.setEnabled(False)

        self.delete_btn = QPushButton("删除试卷")
        self.delete_btn.setEnabled(False)

        cancel_btn = QPushButton("取消")

        btn_layout.addStretch()
        btn_layout.addWidget(self.select_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.exam_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.select_btn.clicked.connect(self.accept)
        self.delete_btn.clicked.connect(self.delete_exam)
        cancel_btn.clicked.connect(self.reject)

    def on_selection_changed(self):
        """选中项改变"""
        selected_items = self.exam_list.selectedItems()
        has_selection = len(selected_items) > 0

        self.select_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

        if has_selection:
            self.selected_exam = selected_items[0].data(Qt.UserRole)
        else:
            self.selected_exam = None

    def delete_exam(self):
        """删除选中的试卷"""
        if not self.selected_exam:
            return

        exam_id = self.selected_exam["exam_id"]
        title = self.selected_exam["title"]
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除试卷「{title}」及其所有答题记录吗？\n此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # 删除该试卷的所有记录
                self.db.delete_exam_by_id(exam_id)

                QMessageBox.information(self, "删除成功", f"试卷「{title}」已删除")

                # 刷新列表
                self.refresh_list()

            except Exception as e:
                QMessageBox.warning(self, "删除失败", f"删除时出错：{str(e)}")

    def refresh_list(self):
        """刷新考试列表"""
        self.exam_list.clear()

        # 重新从数据库获取数据
        attempts = self.db.get_all_exam_attempts()

        if not attempts:
            # 如果没有记录，关闭对话框
            QMessageBox.information(self, "提示", "暂无历史记录")
            self.reject()
            return

        # 重新分组
        from collections import defaultdict
        grouped = defaultdict(list)
        for a in attempts:
            grouped[a.get("exam_id")].append(a)

        new_exams = []
        for exam_id, questions in grouped.items():
            total = len(questions)
            completed = sum(1 for q in questions if q.get("status") == "completed")
            new_exams.append({
                "exam_id": exam_id,
                "title": f"试卷 {exam_id}",
                "questions": questions,
                "progress": f"{completed}/{total}"
            })

        self.exams = new_exams

        for exam in self.exams:
            item_text = f"📋 {exam['title']}  ({exam['progress']})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, exam)
            self.exam_list.addItem(item)

        self.selected_exam = None
        self.select_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def get_selected_exam(self):
        return self.selected_exam