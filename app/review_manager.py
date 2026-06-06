from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox, QFrame, QCheckBox
import json
import html
from app.review_thread import ReviewMaterialThread
from app.mistake_card import MistakeCard

class ReviewManager(QObject):
    review_generated = Signal(object)#复习资料生成完成信号
    review_error = Signal(str)#错误信号

    def __init__(self, db, parent=None):
        super().__init__()
        self.db = db
        self.review_thread = None

    def get_review_config_dialog(self, parent):
        #生成复习资料配置相关的对话框
        dialog = QDialog(parent)
        dialog.setWindowTitle("复习资料生成要求")
        dialog.resize(500, 350)

        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("请输入你对复习资料的额外要求（可选）："))
        layout.addWidget(QLabel("例如：重点复习数组和指针、多关注边界条件、难度中等偏上等"))

        text_edit = QTextEdit()
        text_edit.setPlaceholderText("输入你的要求...")
        text_edit.setMaximumHeight(120)
        layout.addWidget(text_edit)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(line)

        layout.addWidget(QLabel("AI 生成设置："))
        thinking_checkbox = QCheckBox("开启深度思考（速度更慢，但效果更好）")
        thinking_checkbox.setChecked(False)
        layout.addWidget(thinking_checkbox)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        result = {"text": "", "thinking": "disabled", "ok": False}

        def on_ok():
            result["text"] = text_edit.toPlainText().strip()
            result["thinking"] = "enabled" if thinking_checkbox.isChecked() else "disabled"
            result["ok"] = True
            dialog.accept()

        def on_cancel():
            dialog.reject()

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(on_cancel)

        dialog.exec()

        return result if result["ok"] else None

    def generate_review_material(self, parent, api_key_callback):
        #生成复习资料
        mistakes = self.db.get_all_mistakes(include_mastered=True)

        if not mistakes:
            QMessageBox.information(parent, "复习资料", "暂无错因记录，请先进行一些调试并生成错因卡片。")
            return False

        if not api_key_callback():
            return False

        config = self.get_review_config_dialog(parent)
        if config is None:
            return False

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

        self.review_thread = ReviewMaterialThread(
            error_cards=error_cards,
            user_prompt=config["text"],
            thinking=config["thinking"]
        )
        self.review_thread.finished.connect(self.review_generated.emit)
        self.review_thread.error.connect(self.review_error.emit)
        self.review_thread.start()
        return True

    def format_review_material_html(self, review):
        #把复习资料格式化为HTML
        title = review.get("title", "复习资料")
        summary = review.get("summary", "")
        review_by_kp = review.get("review_by_knowledge_point", [])

        html_content = f"<h1>📚 {title}</h1><p><strong>总体建议：</strong>{summary}</p><hr><h2>知识点复习建议</h2>"

        for item in review_by_kp:
            kp = item.get("knowledge_point", "")
            priority = item.get("priority", "medium")
            what = item.get("what_to_review", "")
            how = item.get("how_to_test", "")
            html_content += f"<h3>📌 {kp} ({priority})</h3><p><b>复习什么：</b>{what}</p><p><b>如何考核：</b>{how}</p><hr>"

        return html_content

    def show_review_material_dialog(self, parent, review, on_generate_exam_callback):
        #显示复习资料对话框
        dialog = QDialog(parent)
        dialog.setWindowTitle("复习资料")
        dialog.resize(650, 550)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(self.format_review_material_html(review))
        layout.addWidget(text_edit)

        btn_layout = QHBoxLayout()

        generate_exam_btn = QPushButton("生成考题")
        generate_exam_btn.clicked.connect(lambda: on_generate_exam_callback(dialog))

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)

        btn_layout.addStretch()
        btn_layout.addWidget(generate_exam_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        dialog.exec()

    def update_knowledge_combo(self, combo_box):
        #更新知识点下拉栏
        mistakes = self.db.get_all_mistakes(include_mastered=True)
        all_knowledge = set()
        for m in mistakes:
            kp = m.get("knowledge_points", "")
            if kp:
                try:
                    points = json.loads(kp) if isinstance(kp, str) else kp
                    if isinstance(points, list):
                        all_knowledge.update(points)
                except:
                    pass

        combo_box.clear()
        combo_box.addItem("全部")
        for kp in sorted(all_knowledge):
            combo_box.addItem(kp)

    def refresh_mistake_list(self, scroll_content, stats_label, filter_combo, knowledge_combo, search_edit, db):
        layout = scroll_content.layout()
        if layout:
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget is not None and isinstance(widget, MistakeCard):
                    widget.deleteLater()

        filter_text = filter_combo.currentText()
        selected_knowledge = knowledge_combo.currentText()
        search_text = search_edit.text().strip().lower()

        include_mastered = (filter_text != "未掌握")
        mistakes = db.get_all_mistakes(include_mastered=include_mastered)

        if filter_text == "已掌握":
            mistakes = [m for m in mistakes if m.get("is_mastered")]

        if selected_knowledge != "全部":
            filtered_mistakes = []
            for m in mistakes:
                kp = m.get("knowledge_points", "")
                if kp:
                    try:
                        points = json.loads(kp) if isinstance(kp, str) else kp
                        if isinstance(points, list) and selected_knowledge in points:
                            filtered_mistakes.append(m)
                    except:
                        pass
            mistakes = filtered_mistakes

        if search_text:
            mistakes = [m for m in mistakes if search_text in m.get("error_type", "").lower() or
                        search_text in m.get("error_description", "").lower()]

        stats_label.setText(f"共{len(mistakes)}条错因")

        for mistake in mistakes:
            card = MistakeCard(mistake, db, scroll_content)
            layout.insertWidget(layout.count() - 1, card)