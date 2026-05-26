import json
from database import Database
from llm import analyze_problem, start_debug_guide_session

class LLMIntegration:
    def __init__(self, db: Database):
        self.db = db

    def analyze_and_save_problem(self, problem_text: str, title: str = ""):
        analysis = analyze_problem(problem_text)

        if not title:
            title = analysis.get("summary", problem_text[:50])

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
            difficulty=analysis.get("difficulty", "")
        )

        return problem_id, analysis

    def diagnose_and_save(self, problem_id: int, problem_text: str, problem_analysis: dict,
                            code: str, program_output: str = "", expected_output: str = "",
                            error_message: str = "", oj_result: str = "", extra_info: str = ""):
        code_record_id = self.db.add_code_record(problem_id, code)

        if program_output:
            self.db.update_code_result(code_record_id, program_output, True)

        session = start_debug_guide_session(
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

