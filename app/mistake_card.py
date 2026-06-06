import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame


class MistakeCard(QWidget):
    def __init__(self, data, db, parent=None):
        super().__init__(parent)
        self.data = data
        self.db = db
        self.mistake_id = data.get("id")
        self.is_mastered = data.get("is_mastered", False)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 10, 12, 10)

        # 标题行
        title_layout = QHBoxLayout()

        priority = self.data.get("review_priority", "medium")
        priority_icon = {"high": "🔴高优先级：", "medium": "🟡中优先级：", "low": "🟢低优先级："}.get(priority, "⚪")
        error_type = self.data.get("error_type", "未知错误")

        title_label = QLabel(f"{priority_icon} {error_type}")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.mastered_btn = QPushButton("✅ 已掌握" if self.is_mastered else "⭐ 未掌握")
        self.mastered_btn.setCheckable(True)
        self.mastered_btn.setChecked(self.is_mastered)
        self.mastered_btn.clicked.connect(self.toggle_mastered)
        self.mastered_btn.setMaximumWidth(100)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.mastered_btn)

        # 错误描述
        desc = self.data.get("error_description", "")
        desc_label = QLabel(f"📝 错误描述：{desc}")
        desc_label.setWordWrap(True)

        # 知识点
        kp_text = self.data.get("knowledge_points", "")
        if kp_text:
            try:
                points = json.loads(kp_text) if isinstance(kp_text, str) else kp_text
                if isinstance(points, list) and points:
                    kp_label = QLabel(f"📚 知识点：{', '.join(points[:3])}")
                    kp_label.setStyleSheet("color: #555; font-size: 12px;")
                    layout.addWidget(kp_label)
            except:
                pass

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e0e0e0; max-height: 1px;")

        layout.addLayout(title_layout)
        layout.addWidget(desc_label)
        layout.addWidget(line)

        self.setStyleSheet("""
            MistakeCard {
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
            MistakeCard:hover {
                background-color: #f5f5f5;
                border-color: #bbb;
            }
        """)

    def toggle_mastered(self):
        self.is_mastered = not self.is_mastered
        self.mastered_btn.setText("✅ 已掌握" if self.is_mastered else "⭐ 未掌握")
        self.db.mark_mistake_mastered(self.mistake_id, self.is_mastered)