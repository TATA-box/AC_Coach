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
                    correct_suggestion TEXT,
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
        self._ensure_problem_analysis_columns(cursor)
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

        return [{"id":row[0], "title":row[1], "created_at":row[2]} for row in rows]

    def get_problem(self, problem_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM problems WHERE id = ?", (problem_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def add_code_record(self, problem_id, code_content, language="cpp"):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO code_records (problem_id, code_content, language) VALUES (?,?,?)",
            (problem_id, code_content, language)
        )

        conn.commit()
        record_id = cursor.lastrowid
        conn.close()

        print(f"代码记录已添加，id:{record_id}")
        return record_id

    def update_code_result(self, record_id, output, success):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE code_records SET run_output = ?, run_success = ? WHERE id = ?",
            (output, success, record_id)
        )

        conn.commit()
        conn.close()
        print(f"代码记录已更新，id:{record_id}")

    def add_diagnosis(self, code_record_id, problem_id, has_error="", error_summary="", error_type="",
                        knowledge_points="", suspected_locations="", confidence="",
                        reason_for_uncertainty="", debug_suggestion="", guide_steps="", raw_response=""):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO diagnoses (
                code_record_id, problem_id, has_error, error_summary, error_type,
                knowledge_points, suspected_locations, confidence, reason_for_uncertainty,
                debug_suggestion, guide_steps, raw_response
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (code_record_id, problem_id, has_error, error_summary, error_type,
                knowledge_points, suspected_locations, confidence, reason_for_uncertainty,
                debug_suggestion, guide_steps, raw_response))

        conn.commit()
        diagnosis_id = cursor.lastrowid
        conn.close()

        print(f"诊断记录已添加，id:{diagnosis_id}")
        return diagnosis_id

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

    def update_diagnosis(self, diagnosis_id, has_error="", error_summary="", error_type="",
                     knowledge_points="", suspected_locations="", confidence="",
                     reason_for_uncertainty="", debug_suggestion="", guide_steps=""):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE diagnoses SET
                has_error = ?,
                error_summary = ?,
                error_type = ?,
                knowledge_points = ?,
                suspected_locations = ?,
                confidence = ?,
                reason_for_uncertainty = ?,
                debug_suggestion = ?,
                guide_steps = ?
            WHERE id = ?
        ''', (has_error, error_summary, error_type, knowledge_points,
                suspected_locations, confidence, reason_for_uncertainty,
                debug_suggestion, guide_steps, diagnosis_id))

        conn.commit()
        conn.close()
        print(f"诊断记录已更新，id:{diagnosis_id}")

    def add_mistake(self, problem_id, diagnosis_id, error_type, error_description="", wrong_code="",
                        wrong_code_start_line=None, wrong_code_end_line=None,
                        knowledge_points="", correct_suggestion="",
                        error_card_title="", root_cause="", wrong_pattern="",
                        review_question="", review_hint="", avoid_next_time="",
                        tags="", review_priority=""):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO mistake_library (
                problem_id, diagnosis_id, error_type, error_description, wrong_code,
                wrong_code_start_line, wrong_code_end_line, knowledge_points, correct_suggestion,
                error_card_title, root_cause, wrong_pattern,
                review_question, review_hint, avoid_next_time,
                tags, review_priority
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (problem_id, diagnosis_id, error_type, error_description, wrong_code,
                wrong_code_start_line, wrong_code_end_line, knowledge_points, correct_suggestion,
                error_card_title, root_cause, wrong_pattern,
                review_question, review_hint, avoid_next_time,
                tags, review_priority))

        conn.commit()
        mistake_id = cursor.lastrowid
        conn.close()

        print(f"错因已记录，id:{mistake_id}")
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

        print(f"错因{mistake_id}已标记为{'已掌握' if mastered else '未掌握'}")

    def add_guide_step(self, diagnosis_id, step_no, title, guide, start_line=None, end_line=None,
                        student_question="", expected_discovery="", focus=""):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO guide_steps (diagnosis_id, step_no, title, guide, start_line, end_line,
                                        student_question, expected_discovery, focus)
            VALUES (?,?,?,?,?,?,?,?,?)
        ''', (diagnosis_id, step_no, title, guide, start_line, end_line, student_question, expected_discovery, focus))

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
