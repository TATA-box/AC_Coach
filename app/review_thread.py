from PySide6.QtCore import QThread, Signal
from llm import generate_review_material

class ReviewMaterialThread(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, error_cards, user_prompt = "", thinking="disabled"):
        super().__init__()
        self.error_cards = error_cards
        self.user_prompt = user_prompt
        self.thinking = thinking

    def run(self):
        try:
            review = generate_review_material(
                error_cards=self.error_cards,
                user_prompt=self.user_prompt,
                thinking=self.thinking
            )
            self.finished.emit(review)
        except Exception as e:
            self.error.emit(str(e))