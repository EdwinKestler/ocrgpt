import os
import cv2
import pytesseract
import openai
from pdf2image import convert_from_path
from dotenv import load_dotenv
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QTextEdit, QLineEdit


load_dotenv()
openai.organization = "org-P44J2sYyfEEfBF2gCYM7wSgX"
openai.api_key = os.getenv("OPENAI_API_KEY")

def convert_pdf_to_images(pdf_path):
    images = convert_from_path(pdf_path)
    return images

def extract_text_from_image(image_path):
    img = cv2.imread(image_path)
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray_img)
    return text.strip()

def generate_summary(text):
    response = openai.Completion.create(
        engine="gpt-3.5-turbo",
        prompt=f"Please provide a short summary of the following text:\n\n{text}",
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.5,
    )

    summary = response.choices[0].text.strip()
    return summary

class OCRSummarizerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("OCR Scanner & Summarizer")

        layout = QVBoxLayout()

        self.api_key_label = QLabel("OpenAI API Key:")
        layout.addWidget(self.api_key_label)

        self.api_key_edit = QLineEdit()
        layout.addWidget(self.api_key_edit)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)

        self.text_edit = QTextEdit()
        layout.addWidget(self.text_edit)

        self.load_image_button = QPushButton("Load Image")
        self.load_image_button.clicked.connect(self.load_image)
        layout.addWidget(self.load_image_button)

        self.summarize_button = QPushButton("Summarize")
        self.summarize_button.clicked.connect(self.summarize)
        layout.addWidget(self.summarize_button)

        self.setLayout(layout)

    def load_image(self):
        options = QFileDialog.Option.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image/PDF", "", "Images/PDF (*.png *.xpm *.jpg *.bmp *.pdf);;All Files (*)", options=options)

        if file_name:
            if file_name.lower().endswith(".pdf"):
                images = convert_pdf_to_images(file_name)
                if images:
                    pixmap = QPixmap.fromImage(QImage.fromData(images[0].save("temp.png").getvalue()))
                    self.image_pages = images
                else:
                    self.image_pages = []
            else:
                pixmap = QPixmap(file_name)
                self.image_pages = [pixmap]

            if self.image_pages:
                self.image_label.setPixmap(self.image_pages[0].scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio))
                self.image_path = file_name

    def summarize(self):
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            self.text_edit.setPlainText("Please enter a valid OpenAI API key.")
            return

        openai.api_key = api_key

        if hasattr(self, "image_path"):
            if self.image_path.lower().endswith(".pdf"):
                text = "\n".join([extract_text_from_image(page) for page in self.image_pages])
            else:
                text = extract_text_from_image(self.image_path)
            summary = generate_summary(text)
            self.text_edit.setPlainText(summary)
        else:
            self.text_edit.setPlainText("Please load an image or PDF first.")

def main():
    app = QApplication(sys.argv)
    window = OCRSummarizerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()