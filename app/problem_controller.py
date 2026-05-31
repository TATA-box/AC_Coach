import json
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QTextEdit,
    QVBoxLayout,
)

from llm import analyze_problem, structure_problem_text


def _json_dump(value):
    if value is None:
        return ""

    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)

    return str(value)


def _json_load(value, default):
    if value in (None, ""):
        return default

    try:
        return json.loads(value)
    except Exception:
        return value


class ProblemEditDialog(QDialog):
    def __init__(self, old_text="", parent=None):
        super().__init__(parent)

        self.setWindowTitle("录入 / 修改题目")
        self.resize(720, 520)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("请粘贴当前 .cpp 对应的题目原文：", self))

        self.problem_edit = QPlainTextEdit(self)
        self.problem_edit.setPlainText(old_text or "")
        self.problem_edit.setPlaceholderText(
            "把题目标题、背景、题目描述、输入输出、样例、提示、数据范围等全部粘贴到这里。"
        )
        layout.addWidget(self.problem_edit)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText("保存并分析")
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.button_box)

    def problem_text(self):
        return self.problem_edit.toPlainText().strip()


class ProblemCheckDialog(QDialog):
    def __init__(self, markdown_text, parent=None):
        super().__init__(parent)

        self.setWindowTitle("查看题目")
        self.resize(780, 620)

        layout = QVBoxLayout(self)

        self.text_view = QTextEdit(self)
        self.text_view.setReadOnly(True)
        self.text_view.setMarkdown(markdown_text)

        layout.addWidget(self.text_view)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close,
            self,
        )
        self.button_box.button(QDialogButtonBox.StandardButton.Close).setText("关闭")
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self.accept)

        layout.addWidget(self.button_box)


class ProblemAnalyzeWorker(QObject):
    finished = Signal(dict)
    failed = Signal(int, str)
    progress = Signal(str)

    def __init__(self, db, problem_id, problem_text, parent=None):
        super().__init__(parent)

        self.db = db
        self.problem_id = problem_id
        self.problem_text = problem_text

    def run(self):
        try:
            self.progress.emit("开始整理题面 structure_problem_text() ...")

            problem_struct = structure_problem_text(
                self.problem_text,
                max_retries=1,
            ) or {}

            self.progress.emit("题面整理完成，开始分析题目 analyze_problem() ...")

            analysis = analyze_problem(self.problem_text) or {}

            self.progress.emit("题目分析完成，正在写入数据库 ...")

            title = (
                    problem_struct.get("title")
                    or analysis.get("summary")
                    or self.problem_text[:30]
                    or "未命名题目"
            )

            fields = dict(
                title=title,
                content=self.problem_text,

                summary=analysis.get("summary", ""),
                input_format=analysis.get("input_format", ""),
                output_format=analysis.get("output_format", ""),
                knowledge_points=_json_dump(analysis.get("knowledge_points", [])),
                constraints=_json_dump(analysis.get("constraints", [])),
                common_pitfalls=_json_dump(analysis.get("common_pitfalls", [])),
                suggested_approach=_json_dump(analysis.get("suggested_approach", [])),
                difficulty=analysis.get("difficulty", ""),

                structured_title=problem_struct.get("title", ""),
                structured_background=problem_struct.get("background", ""),
                structured_description=problem_struct.get("description", ""),
                structured_input_desc=problem_struct.get("input_description", ""),
                structured_output_desc=problem_struct.get("output_description", ""),
                structured_samples=_json_dump(problem_struct.get("samples", [])),
                structured_notes=problem_struct.get("notes", ""),
                structured_other=problem_struct.get("other", ""),
                structured_validate_passed=1 if problem_struct.get("_validate_passed") else 0,
            )

            self.db.update_problem(self.problem_id, **fields)
            self.db.set_problem_analysis_status(self.problem_id, "done", "")

            problem = self.db.get_problem(self.problem_id)

            self.progress.emit("数据库写入完成。")
            self.finished.emit(problem)

        except Exception as exc:
            self.failed.emit(self.problem_id, str(exc))


class ProblemController:
    def __init__(self, window, editor_manager, db):
        self.window = window
        self.editor_manager = editor_manager
        self.db = db

        self.worker_jobs = []

    def current_cpp_path(self):
        path = self.editor_manager.cur_filepath()

        if path is None:
            result = QMessageBox.question(
                self.window,
                "Question",
                "当前文件还没有保存。需要先保存成 .cpp 文件，才能绑定题目。现在保存吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if result != QMessageBox.StandardButton.Yes:
                return None

            if not self.editor_manager.savefile():
                QMessageBox.information(self.window, "Question", "保存失败，无法绑定题目。")
                return None

            path = self.editor_manager.cur_filepath()

        if path is None:
            return None

        path = Path(path).resolve()

        if path.suffix.lower() != ".cpp":
            QMessageBox.information(self.window, "Question", "当前文件不是 .cpp 文件。")
            return None

        return path

    def modify_current_problem(self):
        path = self.current_cpp_path()

        if path is None:
            return

        old_problem = self.db.get_problem_by_file(path)
        old_text = old_problem.get("content", "") if old_problem else ""

        dialog = ProblemEditDialog(old_text, self.window)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        problem_text = dialog.problem_text()

        if not problem_text:
            QMessageBox.information(self.window, "Question", "题目内容不能为空。")
            return

        title = problem_text[:30] or "未命名题目"

        if old_problem:
            problem_id = old_problem["id"]

            self.db.update_problem(
                problem_id,
                title=title,
                content=problem_text,
            )
        else:
            problem_id = self.db.add_problem(
                title=title,
                content=problem_text,
            )

        self.db.bind_problem_file(path, problem_id)
        self.db.set_problem_analysis_status(problem_id, "analyzing", "")

        self.log(f"已绑定题目：{path.name}")
        self.log("正在分析题目，请稍后再点击 Check 查看分析结果。")

        self.start_problem_analysis(path, problem_text, problem_id)

    def check_current_problem(self):
        path = self.current_cpp_path()

        if path is None:
            return

        problem = self.db.get_problem_by_file(path)

        if not problem:
            result = QMessageBox.question(
                self.window,
                "Question",
                "当前 .cpp 还没有绑定题目。现在录入吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if result == QMessageBox.StandardButton.Yes:
                self.modify_current_problem()

            return
        status = problem.get("analysis_status") or "done"

        if status == "analyzing":
            self.log(f"题目已经绑定，但仍在分析中：{path.name}")

            QMessageBox.information(
                self.window,
                "Question",
                "当前 .cpp 已经绑定题目，但题目还在分析中。\n\n请稍等一会儿，看到下方日志提示分析完成后再点击 Check。"
            )
            return

        if status == "failed":
            error = problem.get("analysis_error") or "未知错误"

            result = QMessageBox.question(
                self.window,
                "Question",
                "当前 .cpp 已经绑定题目，但上一次分析失败。\n\n"
                f"错误信息：\n{error}\n\n"
                "是否重新分析？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if result == QMessageBox.StandardButton.Yes:
                self.db.set_problem_analysis_status(problem["id"], "analyzing", "")
                self.log(f"重新开始分析题目：{path.name}")
                self.start_problem_analysis(path, problem.get("content", ""), problem["id"])

            return

        markdown = self.format_problem_markdown(problem)
        dialog = ProblemCheckDialog(markdown, self.window)
        dialog.exec()

    def start_problem_analysis(self, path, problem_text, problem_id):
        self.window.statusBar().showMessage("正在整理题面并分析题目……")

        thread = QThread(self.window)
        worker = ProblemAnalyzeWorker(
            self.db,
            problem_id,
            problem_text,
        )

        worker.moveToThread(thread)
        self.log(f"后台分析线程已启动：{Path(path).name}")
        thread.started.connect(worker.run)

        worker.finished.connect(self.on_problem_analysis_finished)
        worker.failed.connect(self.on_problem_analysis_failed)
        worker.progress.connect(self.log)

        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)

        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        job = {
            "thread": thread,
            "worker": worker,
        }

        self.worker_jobs.append(job)

        def cleanup_job():
            if job in self.worker_jobs:
                self.worker_jobs.remove(job)

        thread.finished.connect(cleanup_job)

        thread.start()

    def on_problem_analysis_finished(self, problem):
        self.log("题目分析完成，可以点击 Check 查看。")
        self.window.statusBar().showMessage("题目已保存并分析完成", 5000)

    def on_problem_analysis_failed(self, problem_id, message):
        self.db.set_problem_analysis_status(problem_id, "failed", message)

        self.log("题目分析失败：" + message)
        self.window.statusBar().showMessage("题目分析失败", 5000)

        QMessageBox.warning(
            self.window,
            "Question",
            "题目已绑定，但分析失败。\n\n"
            "你可以之后点击 Check，然后选择重新分析。\n\n"
            "错误信息：\n" + message,
        )

    def format_problem_markdown(self, problem):
        def add_section(parts, title, text):
            if text:
                parts.append(f"## {title}\n{text}")

        def add_list_section(parts, title, value):
            value = _json_load(value, [])

            if isinstance(value, list) and value:
                lines = "\n".join(f"- {item}" for item in value)
                parts.append(f"## {title}\n{lines}")
            elif isinstance(value, str) and value:
                parts.append(f"## {title}\n{value}")

        title = problem.get("structured_title") or problem.get("title") or "未命名题目"
        parts = [f"# {title}"]

        if problem.get("structured_validate_passed"):
            add_section(parts, "背景", problem.get("structured_background"))
            add_section(parts, "题目描述", problem.get("structured_description"))
            add_section(parts, "输入描述", problem.get("structured_input_desc"))
            add_section(parts, "输出描述", problem.get("structured_output_desc"))

            samples = _json_load(problem.get("structured_samples"), [])

            if isinstance(samples, list) and samples:
                sample_blocks = []

                for index, sample in enumerate(samples, start=1):
                    if not isinstance(sample, dict):
                        continue

                    sample_input = sample.get("input", "")
                    sample_output = sample.get("output", "")
                    explanation = sample.get("explanation", "")

                    block = [f"### 样例 {index}"]

                    if sample_input:
                        block.append(f"**输入：**\n```text\n{sample_input}\n```")

                    if sample_output:
                        block.append(f"**输出：**\n```text\n{sample_output}\n```")

                    if explanation:
                        block.append(f"**解释：**\n{explanation}")

                    sample_blocks.append("\n\n".join(block))

                if sample_blocks:
                    parts.append("## 样例\n" + "\n\n".join(sample_blocks))

            add_section(parts, "提示 / 数据范围", problem.get("structured_notes"))
            add_section(parts, "其他", problem.get("structured_other"))

        else:
            add_section(parts, "原始题面", problem.get("content"))

        add_section(parts, "题目概括", problem.get("summary"))
        add_section(parts, "输入格式", problem.get("input_format"))
        add_section(parts, "输出格式", problem.get("output_format"))

        add_list_section(parts, "知识点", problem.get("knowledge_points"))
        add_list_section(parts, "限制条件", problem.get("constraints"))
        add_list_section(parts, "常见错误", problem.get("common_pitfalls"))
        add_list_section(parts, "建议思路", problem.get("suggested_approach"))

        add_section(parts, "难度", problem.get("difficulty"))

        return "\n\n---\n\n".join(parts)

    def log(self, text):
        message = f"[Problem] {text}"

        try:
            self.window.panel_manager.append_output(message)
        except Exception:
            pass

        try:
            self.window.statusBar().showMessage(text, 5000)
        except Exception:
            pass
