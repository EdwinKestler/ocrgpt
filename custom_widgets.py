from PyQt6.QtWidgets import QLineEdit, QLabel, QFrame
from PyQt6.QtCore import Qt

class PasswordLineEdit(QLineEdit):
    def displayText(self):
        return "*" * len(super().displayText())
    
class ImagePreview(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        self.setMinimumSize(400, 400)
    