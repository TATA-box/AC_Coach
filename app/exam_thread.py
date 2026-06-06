from PySide6.QtCore import QThread, Signal
from llm import generate_exam_paper


class ExamPaperThread(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, error_cards, short_blank_count=2, long_blank_count=1, rewrite_count=1, user_prompt="", thinking="disabled"):
        super().__init__()
        self.error_cards = error_cards
        self.short_blank_count = short_blank_count
        self.long_blank_count = long_blank_count
        self.rewrite_count = rewrite_count
        self.user_prompt = user_prompt
        self.thinking = thinking

    def run(self):
        try:
            paper = generate_exam_paper(
                error_cards=self.error_cards,
                short_blank_count=self.short_blank_count,
                long_blank_count=self.long_blank_count,
                rewrite_count=self.rewrite_count,
                user_prompt=self.user_prompt,
                thinking=self.thinking
            )
            self.finished.emit(paper)
        except Exception as e:
            self.error.emit(str(e))