import json
import html

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QMessageBox

from ui.coach_panel_ui import CoachPanelUI
from llm import (
    start_auto_coach_session,
    start_debug_guide_session,
    start_next_hint_session,
    summarize_error_record,
    generate_exam_paper,
)


def _json_load(value, default):
    if value in (None, ""):
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _json_dump(value):
    return json.dumps(value, ensure_ascii=False)

def _normalize_code_for_compare(code):
    return (code or "").strip()

def extract_wrong_code(full_code, diagnosis, context_lines=5):
    """从完整代码中提取错误相关代码片段"""
    if not full_code or not diagnosis:
        return ""

    suspected_locations = diagnosis.get("suspected_locations", [])
    if not suspected_locations:
        return ""

    lines = full_code.splitlines()
    extracted_parts = []

    for location in suspected_locations:
        start = location.get("start_line", 1)
        end = location.get("end_line", start)

        start_idx = max(0, start - 1)
        end_idx = min(len(lines), end)

        # 提取上下文（前后各 context_lines 行）
        context_start = max(0, start_idx - context_lines)
        context_end = min(len(lines), end_idx + context_lines)

        part_lines = lines[context_start:context_end]
        extracted_parts.append("\n".join(part_lines))

    return "\n\n...\n\n".join(extracted_parts)

class FunctionWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self):
        try:
            self.finished.emit(self.func())
        except Exception as exc:
            self.failed.emit(str(exc))


class CoachController(QObject):
    def __init__(self, window, editor_manager, db):
        super().__init__(window)

        self.window = window
        self.editor_manager = editor_manager
        self.db = db

        self.panel = CoachPanelUI(window.ui)

        self.latest_run_context = {}
        self.session = None
        self.mode = ""
        self.problem_id = None
        self.code_record_id = None
        self.diagnosis_id = None
        self.last_context_code = ""
        self.worker_jobs = []

        self.panel.start_button.clicked.connect(self.start_session)
        self.panel.action_button.clicked.connect(self.on_action_clicked)
        self.panel.config_close_button.clicked.connect(self.window.hide_ai_panel)
        self.panel.result_close_button.clicked.connect(self.window.hide_ai_panel)

    def show_config_page(self):
        if self.latest_run_context.get("error_message"):
            self.panel.set_compile_error_mode(
                self.latest_run_context.get("error_message")
            )
        else:
            self.panel.set_normal_mode()

        if self.latest_run_context.get("program_output"):
            self.panel.set_program_output_if_empty(
                self.latest_run_context.get("program_output")
            )

        self.panel.show_config_page()

    def set_latest_run_context(self, context):
        self.latest_run_context = context or {}

        if self.latest_run_context.get("error_message"):
            self.panel.set_compile_error_mode(
                self.latest_run_context.get("error_message")
            )
        else:
            self.panel.set_normal_mode()

        if self.latest_run_context.get("program_output"):
            self.panel.set_program_output_if_empty(
                self.latest_run_context.get("program_output")
            )

    def collect_context(self):
        path = self.editor_manager.cur_filepath()

        if path is None:
            raise RuntimeError("当前没有打开或保存 .cpp 文件。请先保存代码文件。")

        problem = self.db.get_problem_by_file(path)

        if not problem:
            raise RuntimeError(
                "当前代码文件还没有绑定题目。请先通过 Question -> Modify 录入题目。"
            )

        config = self.panel.read_config()
        code = self.editor_manager.current_code()

        error_message = self.latest_run_context.get("error_message") or ""
        run_success = self.latest_run_context.get("run_success")

        program_input = config["program_input"]
        program_output = config["program_output"]
        expected_output = config["expected_output"]

        if error_message:
            program_input = None
            program_output = None
            expected_output = None

        problem_analysis = {
            "summary": problem.get("summary", ""),
            "input_format": problem.get("input_format", ""),
            "output_format": problem.get("output_format", ""),
            "knowledge_points": _json_load(problem.get("knowledge_points"), []),
            "constraints": _json_load(problem.get("constraints"), []),
            "common_pitfalls": _json_load(problem.get("common_pitfalls"), []),
            "suggested_approach": _json_load(problem.get("suggested_approach"), []),
            "difficulty": problem.get("difficulty", ""),
        }

        return {
            "problem": problem,
            "problem_id": problem["id"],
            "problem_text": problem.get("content", ""),
            "problem_analysis": problem_analysis,
            "code": code,
            "selected_mode": config["selected_mode"],
            "thinking": config["thinking"],
            "program_input": program_input,
            "program_output": program_output,
            "expected_output": expected_output,
            "error_message": error_message or None,
            "oj_result": config["oj_result"],
            "extra_info": config["extra_info"],
            "run_success": run_success,
        }

    def start_session(self):
        try:
            context = self.collect_context()
        except Exception as exc:
            QMessageBox.warning(self.window, "AI 助教", str(exc))
            return

        self.editor_manager.clear_highlight()

        self.panel.show_result_page()
        self.panel.clear_step_view()
        self.panel.set_status("正在启动助教……")
        self.panel.set_action_button("请稍等", enabled=False)

        self.problem_id = context["problem_id"]
        self.last_context_code = context["code"]

        self.code_record_id = self.db.ensure_code_record(
            problem_id=context["problem_id"],
            code_content=context["code"],
            language="cpp",
            program_input=context["program_input"] or "",
            program_output=context["program_output"] or "",
            expected_output=context["expected_output"] or "",
            error_message=context["error_message"] or "",
            oj_result=context["oj_result"] or "",
            extra_info=context["extra_info"] or "",
            run_success=context["run_success"],
        )

        self.diagnosis_id = self.db.add_diagnosis(
            code_record_id=self.code_record_id,
            problem_id=context["problem_id"],
            mode=context["selected_mode"],
            status="starting",
        )

        def task():
            kwargs = dict(
                problem_text=context["problem_text"],
                problem_analysis=context["problem_analysis"],
                code=context["code"],
                program_input=context["program_input"],
                program_output=context["program_output"],
                expected_output=context["expected_output"],
                error_message=context["error_message"],
                oj_result=context["oj_result"],
                extra_info=context["extra_info"],
                auto_analyze_problem=False,
                thinking=context["thinking"],
            )

            selected_mode = context["selected_mode"]

            if selected_mode == "debug":
                return "debug", start_debug_guide_session(**kwargs)

            if selected_mode == "next_hint":
                kwargs["need_analysis"] = {
                    "need_type": "next_hint",
                    "reason": "用户手动选择下一步提示模式",
                }
                return "next_hint", start_next_hint_session(**kwargs)

            kwargs["route_thinking"] = context["thinking"]
            session = start_auto_coach_session(**kwargs)
            return session.mode, session

        self.run_in_thread(task, self.on_session_started)

    def on_session_started(self, result):
        self.mode, self.session = result

        self.db.set_diagnosis_mode_status(
            self.diagnosis_id,
            mode=self.mode,
            status="running",
        )

        if self.mode == "debug":
            self.panel.set_status("当前模式：纠错调试。正在生成第一步……")
        else:
            self.panel.set_status("当前模式：下一步提示。正在生成提示……")

        self.fetch_next_step()

    def on_action_clicked(self):
        if self.session is None:
            return

        if self.mode == "next_hint":
            self.update_context_and_fetch()
        else:
            self.fetch_next_step()

    def fetch_next_step(self):
        if self.session is None:
            return

        self.panel.set_action_button("请稍等", enabled=False)
        self.panel.set_status("正在读取下一步提示……")

        def task():
            return self.session.next_step(timeout=120)

        self.run_in_thread(task, self.on_step_received)

    def on_step_received(self, step):
        if step is None:
            if self.mode == "debug":
                self.panel.set_status("调试步骤已经结束。")
                self.panel.set_action_button("已结束", enabled=False)
                self.finish_debug_session()
            else:
                self.panel.set_status("当前小提示已经给完。请先修改代码，再继续。")
                self.panel.set_action_button("我已修改，继续", enabled=True)

            return

        self.save_step(step)
        self.render_step(step)

        if self.mode == "debug":
            self.panel.set_status("当前模式：纠错调试")
            self.panel.set_action_button("下一步", enabled=True)
        else:
            self.panel.set_status("当前模式：下一步提示")
            self.panel.set_action_button("我已修改，继续", enabled=True)

    def save_step(self, step):
        if not self.diagnosis_id:
            return

        self.db.add_guide_step(
            diagnosis_id=self.diagnosis_id,
            step_no=step.get("step_no", 1),
            title=step.get("title", ""),
            guide=step.get("guide", ""),
            start_line=step.get("start_line"),
            end_line=step.get("end_line"),
            student_question=step.get("student_question", ""),
            expected_discovery=step.get("expected_discovery", ""),
            focus=step.get("focus", ""),
            what_to_try_next=step.get("what_to_try_next", ""),
        )

    def render_step(self, step):
        title = html.escape(str(step.get("title", "下一步")))
        focus = html.escape(str(step.get("focus", "")))
        guide = html.escape(str(step.get("guide", ""))).replace("\n", "<br>")
        question = html.escape(str(step.get("student_question", ""))).replace("\n", "<br>")
        discovery = html.escape(str(step.get("expected_discovery", ""))).replace("\n", "<br>")
        what_to_try_next = html.escape(str(step.get("what_to_try_next", ""))).replace("\n", "<br>")

        parts = [f"<h2>{title}</h2>"]

        if focus:
            parts.append(f"<p><b>这一轮关注：</b>{focus}</p>")

        if guide:
            parts.append(f"<p><b>助教提示：</b>{guide}</p>")

        if question:
            parts.append(f"<p><b>想一想：</b>{question}</p>")

        if what_to_try_next:
            parts.append(f"<p><b>现在动手做：</b>{what_to_try_next}</p>")

        if discovery:
            parts.append(f"<hr><p><b>你应该发现：</b>{discovery}</p>")

        self.panel.set_step_html("".join(parts))

        start_line = step.get("start_line")
        end_line = step.get("end_line")
        self.editor_manager.clear_highlight()
        if start_line is not None and end_line is not None:
            self.editor_manager.highlight_lines(start_line, end_line)

    def update_context_and_fetch(self):
        try:
            context = self.collect_context()
        except Exception as exc:
            QMessageBox.warning(self.window, "AI 助教", str(exc))
            return

        if self.mode == "next_hint":
            old_code = _normalize_code_for_compare(self.last_context_code)
            new_code = _normalize_code_for_compare(context["code"])

            if old_code == new_code:
                QMessageBox.information(
                    self.window,
                    "AI 助教",
                    "请先根据当前提示修改代码，再点击“我已修改，继续”。"
                )
                return

        if self.code_record_id:
            self.db.update_code_context(
                record_id=self.code_record_id,
                code_content=context["code"],
                program_input=context["program_input"] or "",
                program_output=context["program_output"] or "",
                expected_output=context["expected_output"] or "",
                error_message=context["error_message"] or "",
                oj_result=context["oj_result"] or "",
                extra_info=context["extra_info"] or "",
                run_success=context["run_success"],
            )
        self.last_context_code = context["code"]

        self.panel.set_action_button("我已修改，继续", enabled=False)
        self.panel.set_status("正在根据新代码更新上下文……")

        def task():
            self.session.update_context(
                code=context["code"],
                program_input=context["program_input"],
                program_output=context["program_output"],
                expected_output=context["expected_output"],
                error_message=context["error_message"],
                oj_result=context["oj_result"],
                extra_info=context["extra_info"],
            )

            return getattr(self.session, "mode", self.mode)

        self.run_in_thread(task, self.on_context_updated)

    def on_context_updated(self, mode):
        self.mode = mode

        if self.diagnosis_id:
            self.db.set_diagnosis_mode_status(
                self.diagnosis_id,
                mode=self.mode,
                status="running",
            )

        self.fetch_next_step()

    def finish_debug_session(self):
        if self.mode != "debug" or self.session is None or not self.diagnosis_id:
            return

        self.panel.set_status("正在整理调试结果……")

        def task():
            result = self.session.wait(timeout=120)
            if result is None:
                return {}
            return result.to_dict()

        self.run_in_thread(task, self.on_debug_finished)

    def on_debug_finished(self, diagnosis):
        self.db.update_diagnosis(
            diagnosis_id=self.diagnosis_id,
            has_error=diagnosis.get("has_error", ""),
            error_summary=diagnosis.get("error_summary", ""),
            error_type=diagnosis.get("error_type", ""),
            knowledge_points=_json_dump(diagnosis.get("knowledge_points", [])),
            suspected_locations=_json_dump(diagnosis.get("suspected_locations", [])),
            confidence=diagnosis.get("confidence", ""),
            reason_for_uncertainty=diagnosis.get("reason_for_uncertainty", ""),
            debug_suggestion=diagnosis.get("debug_suggestion", ""),
            guide_steps=_json_dump(diagnosis.get("guide_steps", [])),
            raw_response=_json_dump(diagnosis),
            status="finished",
        )

        self.generate_mistake_card_async(diagnosis)

    def generate_mistake_card_async(self, diagnosis):
        def task():
            try:
                # 获取当前的上下文信息，用于构建 archive_item
                problem = self.db.get_problem(self.problem_id) if self.problem_id else None
                code_record = self.db.get_latest_code_record_by_problem(self.problem_id) if self.problem_id else None
                if problem and code_record and self.diagnosis_id:
                    archive_item = {
                        "problem_text": problem.get("content", ""),
                        "problem_analysis": {
                            "summary": problem.get("summary", ""),
                            "input_format": problem.get("input_format", ""),
                            "output_format": problem.get("output_format", ""),
                            "knowledge_points": _json_load(problem.get("knowledge_points"), []),
                            "constraints": _json_load(problem.get("constraints"), []),
                            "common_pitfalls": _json_load(problem.get("common_pitfalls"), []),
                            "suggested_approach": _json_load(problem.get("suggested_approach"), []),
                            "difficulty": problem.get("difficulty", ""),
                        },
                        "code": code_record.get("code_content", ""),
                        "program_input": code_record.get("program_input", ""),
                        "program_output": code_record.get("program_output", ""),
                        "expected_output": code_record.get("expected_output", ""),
                        "error_message": code_record.get("error_message", ""),
                        "oj_result": code_record.get("oj_result", ""),
                        "extra_info": code_record.get("extra_info", ""),
                        "diagnosis": diagnosis,  # 诊断结果
                    }

                    error_card = summarize_error_record(archive_item)
                    self.db.add_mistake(
                        problem_id=self.problem_id,
                        diagnosis_id=self.diagnosis_id,
                        error_type=error_card.get("error_type", diagnosis.get("error_type", "")),
                        error_description=error_card.get("title", diagnosis.get("error_summary", "")),
                        wrong_code=extract_wrong_code(code_record.get("code_content", ""), diagnosis),  # 可选：提取错误代码片段
                        knowledge_points=_json_dump(error_card.get("knowledge_points", [])),
                        error_card_title=error_card.get("title", ""),
                        root_cause=error_card.get("root_cause", ""),
                        wrong_pattern=error_card.get("wrong_code_pattern", ""),
                        review_question=error_card.get("review_question", ""),
                        review_hint=error_card.get("review_hint", ""),
                        avoid_next_time=error_card.get("avoid_next_time", ""),
                        tags=_json_dump(error_card.get("tags", [])),
                        review_priority=error_card.get("review_priority", "medium"),
                    )

                    return "success"
            except Exception as e:
                return str(e)

        def on_finished(result):
            if result == "success":
                self.panel.set_status("调试结束，诊断结果和错因卡片已保存。")
            else:
                print(f"错因卡片生成失败：{result}")
                self.panel.set_status("调试结束，诊断结果已保存（错因卡片生成失败）。")

        self.run_in_thread(task, on_finished)


    def run_in_thread(self, func, on_success):
        thread = QThread(self.window)
        worker = FunctionWorker(func)

        worker.moveToThread(thread)

        thread.started.connect(worker.run)

        worker.finished.connect(on_success)
        worker.failed.connect(self.on_worker_failed)

        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)

        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        job = {
            "thread": thread,
            "worker": worker,
        }

        self.worker_jobs.append(job)

        def cleanup():
            if job in self.worker_jobs:
                self.worker_jobs.remove(job)

        thread.finished.connect(cleanup)
        thread.start()

    def on_worker_failed(self, message):
        if self.diagnosis_id:
            self.db.set_diagnosis_mode_status(
                self.diagnosis_id,
                mode=self.mode or "",
                status="failed",
            )

        self.panel.set_status("助教调用失败")
        self.panel.set_action_button(
            "我已修改，继续" if self.mode == "next_hint" else "下一步",
            enabled=self.session is not None,
        )

        QMessageBox.warning(self.window, "AI 助教", message)

    def generate_exam_paper(self, error_cards, short_blank_count=2, long_blank_count=1, rewrite_count=1, user_prompt=""):
        try:
            paper = generate_exam_paper(
                error_cards=error_cards,
                short_blank_count=short_blank_count,
                long_blank_count=long_blank_count,
                rewrite_count=rewrite_count,
                user_prompt=user_prompt,
            )
            return paper, None
        except Exception as e:
            return None, str(e)

