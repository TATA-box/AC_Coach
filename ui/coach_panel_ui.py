from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QComboBox,
    QCheckBox,
    QPlainTextEdit,
    QTextEdit,
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QSizePolicy,
)


class CoachPanelUI:

    def __init__(self, ui):
        self.ui = ui

        self.stack = ui.coachStack
        self.config_page = ui.coachConfigPage
        self.result_page = ui.coachResultPage

        self._build_config_page()
        self._build_result_page()

        self.show_config_page()

    # ---------- public methods ----------

    def show_config_page(self):
        """显示求助前配置页。"""
        self.stack.setCurrentWidget(self.config_page)
        self.extra_info_edit.setFocus()

    def show_result_page(self):
        """显示助教结果页。"""
        self.stack.setCurrentWidget(self.result_page)

    def read_config(self):
        """
        读取配置页用户填写的信息。

        """
        return {
            "selected_mode": self.mode_box.currentData(),
            "thinking": "enabled" if self.thinking_check.isChecked() else "disabled",
            "program_input": self.program_input_edit.toPlainText().strip() or None,
            "program_output": self.program_output_edit.toPlainText().strip() or None,
            "expected_output": self.expected_output_edit.toPlainText().strip() or None,
            "oj_result": self.oj_result_edit.toPlainText().strip() or None,
            "extra_info": self.extra_info_edit.toPlainText().strip() or None,
        }

    def set_compile_error_mode(self, error_message):
        """
        检测到编译错误时调用。

        作用：
        - 显示提示条
        - 隐藏输入/输出/期望输出区域
        """
        self.auto_error_label.setVisible(True)
        self.auto_error_label.setText(
            "已检测到最近一次编译/运行错误，助教会自动分析错误信息。"
        )
        self.io_group.setVisible(False)

    def set_normal_mode(self):
        """
        没有检测到编译错误时调用。

        作用：
        - 隐藏自动错误提示
        - 显示输入输出区域
        """
        self.auto_error_label.setVisible(False)
        self.io_group.setVisible(True)

    def set_program_output_if_empty(self, text):
        """如果实际输出框为空，就自动填入程序输出。"""
        if text and not self.program_output_edit.toPlainText().strip():
            self.program_output_edit.setPlainText(text)

    def set_status(self, text):
        """设置结果页状态文字。"""
        self.status_label.setText(text)

    def set_step_html(self, html):
        """设置结果页提示内容。"""
        self.step_view.setHtml(html)

    def clear_step_view(self):
        """清空结果页提示内容。"""
        self.step_view.clear()

    def set_action_button(self, text, enabled=True):
        """设置结果页主按钮文字和可用状态。"""
        self.action_button.setText(text)
        self.action_button.setEnabled(enabled)

    # ---------- config page ----------

    def _build_config_page(self):
        self._clear_page(self.config_page)

        root_layout = QVBoxLayout(self.config_page)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        title_row = self._create_title_row("AI 助教")
        self.config_close_button = title_row["close_button"]
        root_layout.addLayout(title_row["layout"])

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(8)

        # 助教模式
        form_layout.addWidget(self._label("助教模式"))

        self.mode_box = QComboBox()
        self.mode_box.setObjectName("coachModeBox")
        self.mode_box.addItem("自动判断", "auto")
        self.mode_box.addItem("纠错调试", "debug")
        self.mode_box.addItem("下一步提示", "next_hint")
        form_layout.addWidget(self.mode_box)

        # 深度思考
        self.thinking_check = QCheckBox("使用深度思考")
        self.thinking_check.setObjectName("coachThinkingCheck")
        self.thinking_check.setToolTip(
            "速度会更慢，但复杂错误或隐藏测试点错误时可能更准确。"
        )
        form_layout.addWidget(self.thinking_check)

        # 自动错误提示
        self.auto_error_label = QLabel()
        self.auto_error_label.setObjectName("coachAutoErrorLabel")
        self.auto_error_label.setWordWrap(True)
        self.auto_error_label.setVisible(False)
        self.auto_error_label.setStyleSheet(
            """
            QLabel {
                color: #8a6d3b;
                background-color: #fff3cd;
                border: 1px solid #ffeeba;
                border-radius: 4px;
                padding: 6px;
            }
            """
        )
        form_layout.addWidget(self.auto_error_label)

        # 输入输出区域
        self.io_group = QGroupBox("输入输出信息，可选")
        self.io_group.setObjectName("coachIOGroup")
        io_layout = QVBoxLayout(self.io_group)
        io_layout.setSpacing(6)

        io_layout.addWidget(self._label("程序输入 program_input，可选"))
        self.program_input_edit = self._plain_text_edit(
            object_name="coachProgramInputEdit",
            placeholder="填写本次运行输入，例如样例输入",
            max_height=70,
        )
        io_layout.addWidget(self.program_input_edit)

        io_layout.addWidget(self._label("实际输出 program_output，可选"))
        self.program_output_edit = self._plain_text_edit(
            object_name="coachProgramOutputEdit",
            placeholder="填写程序实际输出",
            max_height=70,
        )
        io_layout.addWidget(self.program_output_edit)

        io_layout.addWidget(self._label("期望输出 expected_output，可选"))
        self.expected_output_edit = self._plain_text_edit(
            object_name="coachExpectedOutputEdit",
            placeholder="填写样例输出或正确输出",
            max_height=70,
        )
        io_layout.addWidget(self.expected_output_edit)

        form_layout.addWidget(self.io_group)

        # OJ 结果
        form_layout.addWidget(self._label("OJ 结果 oj_result，可选"))
        self.oj_result_edit = self._plain_text_edit(
            object_name="coachOjResultEdit",
            placeholder="例如：WA / RE / TLE / 样例过了但隐藏点错",
            max_height=60,
        )
        form_layout.addWidget(self.oj_result_edit)

        # 学生补充描述
        form_layout.addWidget(self._label("学生补充描述 extra_info，可选"))
        self.extra_info_edit = self._plain_text_edit(
            object_name="coachExtraInfoEdit",
            placeholder="例如：我不知道下一步怎么写；样例过了但提交 WA；我怀疑边界情况错了",
            max_height=90,
        )
        form_layout.addWidget(self.extra_info_edit)

        form_layout.addStretch()

        scroll.setWidget(form_widget)
        root_layout.addWidget(scroll, stretch=1)

        self.start_button = QPushButton("求助助教")
        self.start_button.setObjectName("coachStartButton")
        self.start_button.setMinimumHeight(34)
        self.start_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.start_button.setStyleSheet("font-weight: bold; padding: 6px;")
        root_layout.addWidget(self.start_button)

    # ---------- result page ----------

    def _build_result_page(self):
        self._clear_page(self.result_page)

        root_layout = QVBoxLayout(self.result_page)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        title_row = self._create_title_row("AI 助教")
        self.result_close_button = title_row["close_button"]
        root_layout.addLayout(title_row["layout"])

        self.status_label = QLabel("尚未开始")
        self.status_label.setObjectName("coachStatusLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #555; padding: 4px;")
        root_layout.addWidget(self.status_label)

        self.step_view = QTextEdit()
        self.step_view.setObjectName("coachStepView")
        self.step_view.setReadOnly(True)
        self.step_view.setPlaceholderText("助教提示会显示在这里")
        self.step_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root_layout.addWidget(self.step_view, stretch=1)

        self.action_button = QPushButton("下一步")
        self.action_button.setObjectName("coachActionButton")
        self.action_button.setEnabled(False)
        self.action_button.setMinimumHeight(34)
        self.action_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        root_layout.addWidget(self.action_button)

    # ---------- helper methods ----------

    def _create_title_row(self, title_text):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = QLabel(title_text)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        close_button = QPushButton("×")
        close_button.setFixedSize(30, 28)

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(close_button)

        return {
            "layout": layout,
            "title_label": title,
            "close_button": close_button,
        }

    def _label(self, text):
        label = QLabel(text)
        label.setWordWrap(True)
        return label

    def _plain_text_edit(self, object_name, placeholder="", max_height=70):
        edit = QPlainTextEdit()
        edit.setObjectName(object_name)
        edit.setPlaceholderText(placeholder)
        edit.setMaximumHeight(max_height)
        edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return edit

    def _clear_page(self, page):
        old_layout = page.layout()

        if old_layout is None:
            return

        self._clear_layout(old_layout)

        QWidget().setLayout(old_layout)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
                continue

            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout(child_layout)
