from PyQt6.QtWidgets import QLineEdit

class PasswordLineEdit(QLineEdit):
    def displayText(self):
        return "*" * len(super().displayText())
    