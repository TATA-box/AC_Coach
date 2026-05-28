import json
from database import Database
from llm import analyze_problem, structure_problem_text, start_auto_coach_session

class LLMIntegration:
    def __init__(self, db: Database):
        self.db = db

    def analyze_and_save_problem(self, problem_text: str, title: str = ""):
        problem_struct = structure_problem_text(problem_text)
        analysis = analyze_problem(problem_text)

        if not title:
            title = problem_struct.get("title", analysis.get("summary", problem_text[:50]))

        problem_id = self.db.add_problem(
            title=title,
            content=problem_text,
            summary=analysis.get("summary", ""),
            input_format=analysis.get("input_format", ""),
            output_format=analysis.get("output_format", ""),
            knowledge_points=json.dumps(analysis.get("knowledge_points", []), ensure_ascii=False),
            constraints=json.dumps(analysis.get("constraints", []), ensure_ascii=False),
            common_pitfalls=json.dumps(analysis.get("common_pitfalls", []), ensure_ascii=False),
            suggested_approach=json.dumps(analysis.get("suggested_approach", []), ensure_ascii=False),
            difficulty=analysis.get("difficulty", ""),
            structured_title=problem_struct.get("title", ""),
            structured_background=problem_struct.get("background", ""),
            structured_description=problem_struct.get("description", ""),
            structured_input_desc=problem_struct.get("input_description", ""),
            structured_output_desc=problem_struct.get("output_description", ""),
            structured_samples=json.dumps(problem_struct.get("samples", []), ensure_ascii=False),
            structured_notes=problem_struct.get("notes", ""),
            structured_other=problem_struct.get("other", ""),
            structured_validate_passed=1 if problem_struct.get("_validate_passed") else 0
        )

        return problem_id, analysis, problem_struct

    def diagnose_and_save(self, problem_id: int, problem_text: str, problem_analysis: dict,
                            code: str, program_output: str = "", expected_output: str = "",
                            error_message: str = "", oj_result: str = "", extra_info: str = ""):
        code_record_id = self.db.add_code_record(problem_id, code)

        if program_output:
            self.db.update_code_result(code_record_id, program_output, True)

        session = start_auto_coach_session(
            problem_text=problem_text,
            problem_analysis=problem_analysis,
            code=code,
            program_output=program_output,
            expected_output=expected_output,
            error_message=error_message,
            oj_result=oj_result,
            extra_info=extra_info,
            auto_analyze_problem=False
        )

        mode = session.mode
        print(f"当前模式：{mode}")

        diagnosis_id = self.db.add_diagnosis(
            code_record_id=code_record_id,
            problem_id=problem_id
        )

        steps = []
        while True:
            step = session.next_step()
            if step is None:
                break
            steps.append(step)

            self.db.add_guide_step(
                diagnosis_id=diagnosis_id,
                step_no=step.get("step_no", len(steps)),
                title=step.get("title", ""),
                guide=step.get("guide", ""),
                start_line=step.get("start_line"),
                end_line=step.get("end_line"),
                student_question=step.get("student_question", ""),
                expected_discovery=step.get("expected_discovery", ""),
                focus=step.get("focus", "")
            )

        diagnosis_dict = {}
        if mode == "debug":
            result = session.wait()
            if result:
                diagnosis_dict = result.to_dict()

                self.db.update_diagnosis(
                    diagnosis_id=diagnosis_id,
                    has_error=diagnosis_dict.get("has_error", ""),
                    error_summary=diagnosis_dict.get("error_summary", ""),
                    error_type=diagnosis_dict.get("error_type", ""),
                    knowledge_points=json.dumps(diagnosis_dict.get("knowledge_points", []), ensure_ascii=False),
                    suspected_locations=json.dumps(diagnosis_dict.get("suspected_locations", []), ensure_ascii=False),
                    confidence=diagnosis_dict.get("confidence", ""),
                    reason_for_uncertainty=diagnosis_dict.get("reason_for_uncertainty", ""),
                    debug_suggestion=diagnosis_dict.get("debug_suggestion", ""),
                    guide_steps=json.dumps(diagnosis_dict.get("guide_steps", []), ensure_ascii=False)
                )

        return diagnosis_id, mode, diagnosis_dict, steps