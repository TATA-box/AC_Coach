from pathlib import Path


class FileManager:
    def readfile(self,_path:str|Path)->str:
        return Path(_path).read_text(encoding="utf-8")
    def writefile(self,_path:str|Path,text:str)->None:
        Path(_path).write_text(text,encoding="utf-8")
