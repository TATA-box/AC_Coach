import sqlite3
import json
import hashlib

from pathlib import Path

class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Path(__file__).resolve().parent / "accoach.db"
        self.db_path = str(Path(db_path).resolve())
        self._init_database()

    def _get_connection(self):
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS problems(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                summary TEXT,
                input_format TEXT,
                output_format TEXT,
                knowledge_points TEXT,
                constraints TEXT,
                common_pitfalls TEXT,
                suggested_approach TEXT,
                difficulty TEXT,
                structured_title TEXT,
                structured_background TEXT,
                structured_description TEXT,
                structured_input_desc TEXT,
                structured_output_desc TEXT,
                structured_samples TEXT,
                structured_notes TEXT,
                structured_other TEXT,
                structured_validate_passed BOOLEAN DEFAULT 0,
                analysis_status TEXT DEFAULT "done",
                analysis_error TEXT DEFAULT "",
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_records(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id INTEGER,
                code_content TEXT NOT NULL,
                language TEXT DEFAULT "cpp",
                run_output TEXT,
                run_success BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS diagnoses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code_record_id INTEGER,
                problem_id INTEGER,
                has_error TEXT,
                error_summary TEXT,
                error_type TEXT,
                knowledge_points TEXT,
                suspected_locations TEXT,
                confidence TEXT,
                reason_for_uncertainty TEXT,
                debug_suggestion TEXT,
                guide_steps TEXT,
                raw_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (code_record_id) REFERENCES code_records(id) ON DELETE CASCADE,
                FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guide_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                diagnosis_id INTEGER,
                step_no INTEGER,
                title TEXT,
                guide TEXT,
                start_line INTEGER,
                end_line INTEGER,
                student_question TEXT,
                expected_discovery TEXT,
                focus TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (diagnosis_id) REFERENCES diagnoses(id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS problem_files(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                problem_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
                CREATE TABLE IF NOT EXISTS mistake_library(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    problem_id INTEGER,
                    diagnosis_id INTEGER,
                    error_type TEXT NOT NULL,
                    error_description TEXT,
                    wrong_code TEXT,
                    wrong_code_start_line INTEGER,
                    wrong_code_end_line INTEGER,
                    knowledge_points TEXT,
                    is_mastered BOOLEAN DEFAULT 0,
                    error_card_title TEXT,
                    root_cause TEXT,
                    wrong_pattern TEXT,
                    review_question TEXT,
                    review_hint TEXT,
                    avoid_next_time TEXT,
                    tags TEXT,
                    review_priority TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE,
                    FOREIGN KEY (diagnosis_id) REFERENCES diagnoses(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id TEXT NOT NULL,
                question_id INTEGER NOT NULL,
                question_type TEXT,
                title TEXT,
                problem_statement TEXT,
                code_template TEXT,
                user_code TEXT,
                standard_code TEXT,
                hidden_tests TEXT,
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT "in_progress"
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER,
                user_code TEXT,
                result TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id) ON DELETE CASCADE
            )
        ''')
        self._ensure_problem_analysis_columns(cursor)
        self._ensure_coach_columns(cursor)
        conn.commit()
        conn.close()
        #print("数据库表创建完成")

    def add_problem(self, title, content="", summary="", input_format="", output_format="",
                        knowledge_points="", constraints="", common_pitfalls="", suggested_approach="", difficulty="",
                        structured_title="", structured_background="", structured_description="",
                        structured_input_desc="", structured_output_desc="", structured_samples="",
                        structured_notes="", structured_other="", structured_validate_passed=0):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO problems(title, content, summary, input_format, output_format,
                                knowledge_points, constraints, common_pitfalls, suggested_approach, difficulty,
                                structured_title, structured_background, structured_description,
                                structured_input_desc, structured_output_desc, structured_samples,
                                structured_notes, structured_other, structured_validate_passed)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (title, content, summary, input_format, output_format,
                knowledge_points, constraints, common_pitfalls, suggested_approach, difficulty,
                structured_title, structured_background, structured_description,
                structured_input_desc, structured_output_desc, structured_samples,
                structured_notes, structured_other, structured_validate_passed))

        conn.commit()
        problem_id = cursor.lastrowid
        conn.close()

        #print(f"问题已添加，id:{problem_id}")
        return problem_id

    def get_all_problems(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, title, created_at FROM problems ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_problem(self, problem_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM problems WHERE id = ?", (problem_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def add_code_record(
            self,
            problem_id,
            code_content,
            language="cpp",
            program_input="",
            program_output="",
            expected_output="",
            error_message="",
            oj_result="",
            extra_info="",
            run_success=None,
    ):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO code_records (
                problem_id,
                code_content,
                language,
                run_output,
                run_success,
                program_input,
                program_output,
                expected_output,
                error_message,
                oj_result,
                extra_info
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                problem_id,
                code_content,
                language,
                program_output or "",
                None if run_success is None else 1 if run_success else 0,
                program_input or "",
                program_output or "",
                expected_output or "",
                error_message or "",
                oj_result or "",
                extra_info or "",
            ),
        )

        conn.commit()
        record_id = cursor.lastrowid
        conn.close()

        #print(f"代码记录已添加，id:{record_id}")
        return record_id

    def update_code_result(self, record_id, output, success):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            UPDATE code_records
            SET run_output = ?,
                program_output = ?,
                run_success = ?
            WHERE id = ?
            ''',
            (output or "", output or "", 1 if success else 0, record_id),
        )

        conn.commit()
        conn.close()
        #print(f"代码记录已更新，id:{record_id}")

    def update_code_context(
            self,
            record_id,
            code_content=None,
            program_input="",
            program_output="",
            expected_output="",
            error_message="",
            oj_result="",
            extra_info="",
            run_success=None,
    ):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            UPDATE code_records
            SET code_content = COALESCE(?, code_content),
                program_input = ?,
                program_output = ?,
                expected_output = ?,
                error_message = ?,
                oj_result = ?,
                extra_info = ?,
                run_output = ?,
                run_success = COALESCE(?, run_success)
            WHERE id = ?
            ''',
            (
                code_content,
                program_input or "",
                program_output or "",
                expected_output or "",
                error_message or "",
                oj_result or "",
                extra_info or "",
                program_output or "",
                None if run_success is None else 1 if run_success else 0,
                record_id,
            ),
        )

        conn.commit()
        conn.close()

    def get_latest_code_record_by_problem(self, problem_id):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            SELECT *
            FROM code_records
            WHERE problem_id = ?
            ORDER BY id DESC
            LIMIT 1
            ''',
            (problem_id,),
        )

        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def ensure_code_record(
            self,
            problem_id,
            code_content,
            language="cpp",
            program_input="",
            program_output="",
            expected_output="",
            error_message="",
            oj_result="",
            extra_info="",
            run_success=None,
    ):
        latest = self.get_latest_code_record_by_problem(problem_id)

        if latest and latest.get("code_content") == code_content:
            self.update_code_context(
                record_id=latest["id"],
                code_content=code_content,
                program_input=program_input,
                program_output=program_output,
                expected_output=expected_output,
                error_message=error_message,
                oj_result=oj_result,
                extra_info=extra_info,
                run_success=run_success,
            )
            return latest["id"]

        return self.add_code_record(
            problem_id=problem_id,
            code_content=code_content,
            language=language,
            program_input=program_input,
            program_output=program_output,
            expected_output=expected_output,
            error_message=error_message,
            oj_result=oj_result,
            extra_info=extra_info,
            run_success=run_success,
        )

    def add_diagnosis(
            self,
            code_record_id,
            problem_id,
            has_error="",
            error_summary="",
            error_type="",
            knowledge_points="",
            suspected_locations="",
            confidence="",
            reason_for_uncertainty="",
            debug_suggestion="",
            guide_steps="",
            raw_response="",
            mode="",
            status="",
    ):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO diagnoses (
                code_record_id,
                problem_id,
                has_error,
                error_summary,
                error_type,
                knowledge_points,
                suspected_locations,
                confidence,
                reason_for_uncertainty,
                debug_suggestion,
                guide_steps,
                raw_response,
                mode,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                code_record_id,
                problem_id,
                has_error,
                error_summary,
                error_type,
                knowledge_points,
                suspected_locations,
                confidence,
                reason_for_uncertainty,
                debug_suggestion,
                guide_steps,
                raw_response,
                mode,
                status,
            ),
        )

        conn.commit()
        diagnosis_id = cursor.lastrowid
        conn.close()

        #print(f"诊断记录已添加，id:{diagnosis_id}")
        return diagnosis_id

    def set_diagnosis_mode_status(self, diagnosis_id, mode="", status=""):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            UPDATE diagnoses
            SET mode = ?,
                status = ?
            WHERE id = ?
            ''',
            (mode or "", status or "", diagnosis_id),
        )

        conn.commit()
        conn.close()

    def get_diagnoses_by_problem(self, problem_id):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT d.*, c.code_content
            FROM diagnoses d
            LEFT JOIN code_records c ON d.code_record_id = c.id
            WHERE d.problem_id = ?
            ORDER BY d.id DESC
        ''', (problem_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_diagnosis(
            self,
            diagnosis_id,
            has_error="",
            error_summary="",
            error_type="",
            knowledge_points="",
            suspected_locations="",
            confidence="",
            reason_for_uncertainty="",
            debug_suggestion="",
            guide_steps="",
            raw_response=None,
            status=None,
    ):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            UPDATE diagnoses SET
                has_error = ?,
                error_summary = ?,
                error_type = ?,
                knowledge_points = ?,
                suspected_locations = ?,
                confidence = ?,
                reason_for_uncertainty = ?,
                debug_suggestion = ?,
                guide_steps = ?,
                raw_response = COALESCE(?, raw_response),
                status = COALESCE(?, status)
            WHERE id = ?
            ''',
            (
                has_error,
                error_summary,
                error_type,
                knowledge_points,
                suspected_locations,
                confidence,
                reason_for_uncertainty,
                debug_suggestion,
                guide_steps,
                raw_response,
                status,
                diagnosis_id,
            ),
        )

        conn.commit()
        conn.close()
        #print(f"诊断记录已更新，id:{diagnosis_id}")

    def add_mistake(self, problem_id, diagnosis_id, error_type, error_description="", wrong_code="",
                        wrong_code_start_line=None, wrong_code_end_line=None,
                        knowledge_points="", error_card_title="", root_cause="", wrong_pattern="",
                        review_question="", review_hint="", avoid_next_time="",
                        tags="", review_priority=""):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO mistake_library (
                problem_id, diagnosis_id, error_type, error_description, wrong_code,
                wrong_code_start_line, wrong_code_end_line, knowledge_points, 
                error_card_title, root_cause, wrong_pattern,
                review_question, review_hint, avoid_next_time,
                tags, review_priority
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (problem_id, diagnosis_id, error_type, error_description, wrong_code,
                wrong_code_start_line, wrong_code_end_line, knowledge_points, 
                error_card_title, root_cause, wrong_pattern,
                review_question, review_hint, avoid_next_time,
                tags, review_priority))

        conn.commit()
        mistake_id = cursor.lastrowid
        conn.close()

        #print(f"错因已记录，id:{mistake_id}")
        return mistake_id

    def get_all_mistakes(self, include_mastered=True):
        conn = self._get_connection()
        cursor = conn.cursor()

        if include_mastered:
            cursor.execute('''
                SELECT m.*, p.title as problem_title
                FROM mistake_library m
                LEFT JOIN problems p ON m.problem_id = p.id
                ORDER BY m.is_mastered ASC, m.id DESC
            ''')
        else:
            cursor.execute('''
                SELECT m.*, p.title as problem_title
                FROM mistake_library m
                LEFT JOIN problems p ON m.problem_id = p.id
                WHERE m.is_mastered = 0
                ORDER BY m.id DESC
            ''')

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def mark_mistake_mastered(self, mistake_id, mastered=True):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE mistake_library SET is_mastered = ? WHERE id = ?",
            (1 if mastered else 0, mistake_id)
        )

        conn.commit()
        conn.close()

        #print(f"错因{mistake_id}已标记为{'已掌握' if mastered else '未掌握'}")

    def add_guide_step(
            self,
            diagnosis_id,
            step_no,
            title,
            guide,
            start_line=None,
            end_line=None,
            student_question="",
            expected_discovery="",
            focus="",
            what_to_try_next="",
    ):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO guide_steps (
                diagnosis_id,
                step_no,
                title,
                guide,
                start_line,
                end_line,
                student_question,
                expected_discovery,
                focus,
                what_to_try_next
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                diagnosis_id,
                step_no,
                title,
                guide,
                start_line,
                end_line,
                student_question,
                expected_discovery,
                focus,
                what_to_try_next,
            ),
        )

        conn.commit()
        step_id = cursor.lastrowid
        conn.close()
        return step_id

    def get_guide_steps(self, diagnosis_id):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM guide_steps WHERE diagnosis_id = ? ORDER BY step_no
        ''', (diagnosis_id,))

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_problem(self, problem_id, title, content="", summary="", input_format="", output_format="",
                        knowledge_points="", constraints="", common_pitfalls="", suggested_approach="", difficulty="",
                        structured_title="", structured_background="", structured_description="",
                        structured_input_desc="", structured_output_desc="", structured_samples="",
                        structured_notes="", structured_other="", structured_validate_passed=0):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE problems SET
                title = ?,
                content = ?,
                summary = ?,
                input_format = ?,
                output_format = ?,
                knowledge_points = ?,
                constraints = ?,
                common_pitfalls = ?,
                suggested_approach = ?,
                difficulty = ?,
                structured_title = ?,
                structured_background = ?,
                structured_description = ?,
                structured_input_desc = ?,
                structured_output_desc = ?,
                structured_samples = ?,
                structured_notes = ?,
                structured_other = ?,
                structured_validate_passed = ?
            WHERE id = ?
        ''', (title, content, summary, input_format, output_format,
                knowledge_points, constraints, common_pitfalls, suggested_approach, difficulty,
                structured_title, structured_background, structured_description,
                structured_input_desc, structured_output_desc, structured_samples,
                structured_notes, structured_other, structured_validate_passed, problem_id))

        conn.commit()
        conn.close()

    def bind_problem_file(self, file_path, problem_id):
        file_path = str(Path(file_path).resolve())
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO problem_files(file_path, problem_id)
            VALUES (?, ?)
            ON CONFLICT(file_path) DO UPDATE SET
                problem_id = excluded.problem_id,
                updated_at = CURRENT_TIMESTAMP
        ''', (file_path, problem_id))

        conn.commit()
        conn.close()

    def get_problem_by_file(self, file_path):
        file_path = str(Path(file_path).resolve())
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT p.*
            FROM problem_files pf
            JOIN problems p ON p.id = pf.problem_id
            WHERE pf.file_path = ?
        ''', (file_path,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def _ensure_problem_analysis_columns(self, cursor):
        cursor.execute("PRAGMA table_info(problems)")
        columns = [row[1] for row in cursor.fetchall()]

        if "analysis_status" not in columns:
            cursor.execute(
                'ALTER TABLE problems ADD COLUMN analysis_status TEXT DEFAULT "done"'
            )

        if "analysis_error" not in columns:
            cursor.execute(
                'ALTER TABLE problems ADD COLUMN analysis_error TEXT DEFAULT ""'
            )

    def _ensure_coach_columns(self, cursor):
        def columns_of(table_name):
            cursor.execute(f"PRAGMA table_info({table_name})")
            return [row[1] for row in cursor.fetchall()]

        def add_column(table_name, column_name, sql):
            if column_name not in columns_of(table_name):
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {sql}")

        add_column("code_records", "program_input", "program_input TEXT DEFAULT ''")
        add_column("code_records", "program_output", "program_output TEXT DEFAULT ''")
        add_column("code_records", "expected_output", "expected_output TEXT DEFAULT ''")
        add_column("code_records", "error_message", "error_message TEXT DEFAULT ''")
        add_column("code_records", "oj_result", "oj_result TEXT DEFAULT ''")
        add_column("code_records", "extra_info", "extra_info TEXT DEFAULT ''")

        add_column("diagnoses", "mode", "mode TEXT DEFAULT ''")
        add_column("diagnoses", "status", "status TEXT DEFAULT ''")

        add_column("guide_steps", "what_to_try_next", "what_to_try_next TEXT DEFAULT ''")

    def set_problem_analysis_status(self, problem_id, status, error=""):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            UPDATE problems
            SET analysis_status = ?,
                analysis_error = ?
            WHERE id = ?
            ''',
            (status, error, problem_id)
        )

        conn.commit()
        conn.close()

    def save_exam_attempt(self, exam_id, question_id, question_type, title,
                          problem_statement, code_template, user_code,
                          standard_code, hidden_tests):
        """保存或更新考题答题记录"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 检查是否已存在
        cursor.execute('''
            SELECT id FROM exam_attempts
            WHERE exam_id = ? AND question_id = ?
        ''', (exam_id, question_id))

        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE exam_attempts
                SET user_code = ?, last_modified = CURRENT_TIMESTAMP, status = ?
                WHERE exam_id = ? AND question_id = ?
            ''', (user_code, "in_progress", exam_id, question_id))
            attempt_id = existing["id"]
        else:
            cursor.execute('''
                INSERT INTO exam_attempts (
                    exam_id, question_id, question_type, title,
                    problem_statement, code_template, user_code,
                    standard_code, hidden_tests, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (exam_id, question_id, question_type, title,
                  problem_statement, code_template, user_code,
                  standard_code, hidden_tests, "in_progress"))
            attempt_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return attempt_id

    def get_exam_attempt(self, exam_id, question_id):
        """获取考题答题记录"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM exam_attempts
            WHERE exam_id = ? AND question_id = ?
        ''', (exam_id, question_id))

        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_exam_attempts(self, exam_id=None):
        """获取所有考题答题记录"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if exam_id:
            cursor.execute('''
                SELECT * FROM exam_attempts WHERE exam_id = ? ORDER BY question_id
            ''', (exam_id,))
        else:
            cursor.execute('''
                SELECT * FROM exam_attempts ORDER BY last_modified DESC
            ''')

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_exam_attempt_by_id(self, attempt_id):
        """根据 ID 获取考题答题记录"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM exam_attempts WHERE id = ?
        ''', (attempt_id,))

        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_exam_by_id(self, exam_id):
        """删除指定试卷的所有记录"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM exam_attempts WHERE exam_id = ?
        ''', (exam_id,))

        conn.commit()
        conn.close()

    def add_exam_submission(self, attempt_id, user_code, result):
        """添加提交记录"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO exam_submissions (attempt_id, user_code, result)
            VALUES (?, ?, ?)
        ''', (attempt_id, user_code, result))

        conn.commit()

        # 更新答题记录状态
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE exam_attempts SET status = 'completed' WHERE id = ?
        ''', (attempt_id,))
        conn.commit()
        conn.close()
