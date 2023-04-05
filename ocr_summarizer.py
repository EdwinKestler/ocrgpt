import os
import cv2
import pytesseract
import openai
from pdf2image import convert_from_path
from dotenv import load_dotenv
import sys
from PyQt6.QtCore import Qt, QByteArray, QBuffer, QIODevice, QSize
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QTextEdit, QLineEdit
import time

#pytesseract.pytesseract.tesseract_cmd = r'D:\Program Files\Tesseract-OCR\tesseract.exe'  # Replace with the correct path to tesseract.exe

load_dotenv()

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
        engine="text-davinci-003",
        prompt=f"Please provide main information of:\n\n{text}\n\nTl;dr:",
        max_tokens=200,
        n=1,
        stop=None,
        temperature=0.7,
        frequency_penalty=0.0,
        presence_penalty=1.0,
        top_p=1.0,
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
        
        self.org_label = QLabel("OpenAI Organization:")
        layout.addWidget(self.org_label)
        
        self.org_edit = QLineEdit()
        layout.addWidget(self.org_edit)
        
        self.tesseract_label = QLabel("Tesseract Executable:")
        layout.addWidget(self.tesseract_label)

        self.tesseract_edit = QLineEdit()
        self.tesseract_edit.setReadOnly(True)
        layout.addWidget(self.tesseract_edit)

        self.tesseract_button = QPushButton("Browse")
        self.tesseract_button.clicked.connect(self.browse_tesseract)
        layout.addWidget(self.tesseract_button)

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
        
    def browse_tesseract(self):
        options = QFileDialog.Option.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Tesseract Executable", "", "Executable Files (*.exe);;All Files (*)", options=options)

        if file_name:
            self.tesseract_edit.setText(file_name)
            pytesseract.pytesseract.tesseract_cmd = file_name

    def load_image(self):
        options = QFileDialog.Option.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image/PDF", "", "Images/PDF (*.png *.xpm *.jpg *.bmp *.pdf);;All Files (*)", options=options)

        if file_name:
            if file_name.lower().endswith(".pdf"):
                images = convert_pdf_to_images(file_name)
                if images:
                    byte_array = QByteArray()
                    buffer = QBuffer(byte_array)
                    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                    images[0].save(buffer, "PNG")
                    pixmap = QPixmap()
                    pixmap.loadFromData(byte_array, "PNG")
                    self.image_pages = images
                else:
                    self.image_pages = []
            else:
                pixmap = QPixmap(file_name)
                self.image_pages = [pixmap]

            if self.image_pages:
                # Create a thumbnail
                thumbnail_size = QSize(400, 400)
                thumbnail_image = self.image_pages[0].toqimage().scaled(thumbnail_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                thumbnail_pixmap = QPixmap.fromImage(thumbnail_image)

                # Save the thumbnail to the openai_ocr folder with a timestamp ID
                self.timestamp = str(int(time.time()))
                thumbnail_filename = f"thumbnail_{self.timestamp}.png"
                thumbnail_folder = os.path.join(os.path.expanduser("~"), "Documents", "openai_ocr")
                os.makedirs(thumbnail_folder, exist_ok=True)
                thumbnail_filepath = os.path.join(thumbnail_folder, thumbnail_filename)
                thumbnail_pixmap.save(thumbnail_filepath)
                                    
                # Display the thumbnail
                self.image_label.setPixmap(thumbnail_pixmap)
                self.image_path = file_name
                
    def summarize(self):
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            self.text_edit.setPlainText("Please enter a valid OpenAI API key.")
            return
        
        org = self.org_edit.text().strip()
        if not org:
            self.text_edit.setPlainText("Please enter a valid OpenAI organization.")
            return


        openai.api_key = api_key
        openai.organization = org

        if hasattr(self, "image_path"):
            if self.image_path.lower().endswith(".pdf"):
                temp_image_files = []
                for i, page in enumerate(self.image_pages):
                    temp_filename = f"temp_page_{i}.png"
                    page.save(temp_filename, "PNG")
                    temp_image_files.append(temp_filename)

                text = "\n".join([extract_text_from_image(temp_file) for temp_file in temp_image_files])
                # Save OCR text to the openai_ocr folder with a timestamp ID
                ocr_filename = f"ocr_text_{self.timestamp}.txt"
                ocr_folder = os.path.join(os.path.expanduser("~"), "Documents", "openai_ocr")
                os.makedirs(ocr_folder, exist_ok=True)
                ocr_filepath = os.path.join(ocr_folder, ocr_filename)
                with open(ocr_filepath, "w") as f:
                    f.write(text)

                # Clean up temporary image files
                for temp_file in temp_image_files:
                    os.remove(temp_file)
            else:
                text = extract_text_from_image(self.image_path)
            summary = generate_summary(text)
            self.text_edit.setPlainText(summary)
            # Save OCR text to the openai_ocr folder with a timestamp ID
            openai_filename = f"openai_response_{self.timestamp}.txt"
            openai_folder  = os.path.join(os.path.expanduser("~"), "Documents", "openai_ocr")
            os.makedirs(openai_folder , exist_ok=True)
            openai_filepath  = os.path.join(openai_folder , openai_filename)
            with open(openai_filepath , "w") as f:
                f.write(summary)
        else:
            self.text_edit.setPlainText("Please load an image or PDF first.")

def main():
    app = QApplication(sys.argv)
    window = OCRSummarizerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()