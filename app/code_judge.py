import subprocess
import tempfile
import os
from pathlib import Path


class CodeJudge:
    """代码评判器"""

    def __init__(self):
        self.compiler = "g++"
        self.timeout = 5  # 运行超时（秒）

    def judge(self, user_code, standard_code, hidden_tests, language="cpp"):
        """
        评判用户代码

        参数:
            user_code: 用户提交的代码
            standard_code: 标准答案代码
            hidden_tests: 隐藏测试用例列表，每个元素是 {"input": "..."}
            language: 编程语言（目前只支持 cpp）

        返回:
            {
                "result": "AC"/"WA"/"RE"/"TLE"/"CE",  # 结果
                "user_outputs": [...],                # 用户代码输出列表
                "expected_outputs": [...],            # 期望输出列表
                "error_message": ""                   # 错误信息
            }
        """
        if language != "cpp":
            return {"result": "CE", "error_message": f"不支持的语言: {language}"}

        # 编译用户代码
        user_exe = self._compile_code(user_code, "user_code")
        if user_exe is None:
            return {"result": "CE", "error_message": "编译错误"}

        # 编译标准答案代码
        std_exe = self._compile_code(standard_code, "std_code")
        if std_exe is None:
            return {"result": "CE", "error_message": "标准答案编译错误"}

        try:
            # 运行测试用例
            user_outputs = []
            expected_outputs = []

            for test in hidden_tests:
                test_input = test.get("input", "")

                # 运行用户代码
                user_output = self._run_code(user_exe, test_input)
                # 运行标准答案
                expected_output = self._run_code(std_exe, test_input)

                user_outputs.append(user_output)
                expected_outputs.append(expected_output)

                # 检查是否有运行时错误
                if user_output.get("error") == "timeout":
                    return {"result": "TLE", "user_outputs": user_outputs, "expected_outputs": expected_outputs}
                elif user_output.get("error") == "runtime":
                    return {"result": "RE", "user_outputs": user_outputs, "expected_outputs": expected_outputs, "error_message": user_output.get("message", "")}

            # 对比所有测试用例
            for i, (user_out, expected_out) in enumerate(zip(user_outputs, expected_outputs)):
                if user_out.get("stdout", "").strip() != expected_out.get("stdout", "").strip():
                    return {
                        "result": "WA",
                        "user_outputs": user_outputs,
                        "expected_outputs": expected_outputs,
                        "failed_test_index": i
                    }

            return {"result": "AC", "user_outputs": user_outputs, "expected_outputs": expected_outputs}

        finally:
            # 清理临时文件
            self._cleanup(user_exe, std_exe)

    def _compile_code(self, code, prefix):
        """编译代码，返回可执行文件路径，失败返回 None"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', prefix=prefix, delete=False) as f:
            f.write(code)
            source_path = f.name

        exe_path = source_path.replace('.cpp', '.exe')

        try:
            result = subprocess.run(
                [self.compiler, "-std=c++17", "-Wall", source_path, "-o", exe_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return None

            return exe_path
        except Exception:
            return None

    def _run_code(self, exe_path, input_data):
        """运行可执行文件，返回输出结果"""
        try:
            result = subprocess.run(
                [exe_path],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": None
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "",
                "error": "timeout",
                "message": "运行超时"
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": "",
                "error": "runtime",
                "message": str(e)
            }

    def _cleanup(self, *paths):
        """清理临时文件"""
        for path in paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass