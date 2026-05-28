import re
from pathlib import Path
from PySide6.QtCore import QObject,Signal,QProcess

class CppRunner(QObject):

    output=Signal(str)
    problems_ready=Signal(list)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.compiler="g++"
        self.process:QProcess|None=None
        self.path:Path|None=None
        self.exepath:Path|None=None
        self.errortext=""

    def compile_run(self,_path)->None:
        self.path=Path(_path)
        if self.process is not None:
            self.output.emit("Compile process is already running.")
            return
        if not self.path.exists():
            self.output.emit("Source file does not exist.")
            return
        if self.path.suffix.lower()!=".cpp":
            self.output.emit("Source file is not .cpp")
            return
        self.exepath=self.path.with_suffix(".exe")
        self.errortext=""
        args=[
            "-std=c++17",
            "-Wall",
            "-Wextra",
            str(self.path),
            "-o",
            str(self.exepath),
        ]
        self.process=QProcess(self)
        self.process.setWorkingDirectory(str(self.path.parent))

        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.finished.connect(self.compile_finished)
        self.process.errorOccurred.connect(self.compile_error)

        self.process.start(self.compiler,args)

    def read_stdout(self):
        out=self.process.readAllStandardOutput()
        text=bytes(out).decode("utf-8",errors="replace")
        if text:self.output.emit(text)

    def read_stderr(self):
        out=self.process.readAllStandardError()
        text=bytes(out).decode("utf-8",errors="replace")
        if text:
            self.errortext+=text
            self.output.emit(text)

    def compile_finished(self,exit_code,exit_status):
        success=exit_code==0
        if self.errortext:
            problems=[]
            pattern=re.compile(r"^(.*):(\d+):(\d+):\s*(fatal error|error|warning|note):\s*(.*)$")
            for line in self.errortext.splitlines():
                match=pattern.match(line.strip())
                if not match:continue
                file_path,line_no,column_no,level,message=match.groups()
                problems.append(
                    {
                        "file":file_path,
                        "line":int(line_no),
                        "column":int(column_no),
                        "level":level,
                        "message":message
                    }
                )
            self.problems_ready.emit(problems)

        self.process.deleteLater()
        self.process=None

        if success:
            self.output.emit("Compile succeeded.")

            if not self.exepath.exists():
               self.output.emit("Executable file does not exist.")
               return

            success=QProcess.startDetached(
                "cmd.exe",
                ["/c","start","","cmd.exe","/k",str(self.exepath)],
                str(self.exepath.parent)
            )

            if success:self.output.emit(f"Program started: {self.exepath}")
            else:self.output.emit("Failed to open executable in cmd.")

        else:
            self.output.emit("Compile failed.")

    def compile_error(self,error):
        if self.process:
            error_str = self.process.errorString()
            self.output.emit(f"❌ 编译器启动失败详情：{error_str}")
        self.output.emit("Failed to start compiler.")
        if self.process is not None:
            self.process.deleteLater()
            self.process=None


