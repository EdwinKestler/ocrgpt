"""
    _summary_: ocr_summarizer.py is a Python script that uses OpenAI's API to summarize text from an image or PDF file.
    return: A thumbnail of the first page of the image/PDF file is saved to the user's Documents folder. The user is then prompted to enter their OpenAI API key and organization ID. The user can then select an image or PDF file to summarize. The script will then display the first page of the image/PDF file and the summary of the text in the image/PDF file.
    MIT License, by Edwin Kestler, 2023.
    
    promt: please review that all pages from the pdf document are processed and not only the first one.
"""
import os
import cv2
import pytesseract
import openai
from pdf2image import convert_from_path
from dotenv import load_dotenv
import sys
from PyQt6.QtCore import Qt, QByteArray, QBuffer, QIODevice, QSize, QThreadPool, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QTextEdit, QLineEdit, QScrollArea
import time
import json
import base64


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

class SummaryWorker(QObject):
    summary_ready = pyqtSignal(str, str)

    def __init__(self, image_path, image_pages):
        super().__init__()
        self.image_path = image_path
        self.image_pages = image_pages
    
    @pyqtSlot()
    def process_image_and_generate_summary(self):
        self.timestamp = str(int(time.time()))
        temp_image_files = []
        if self.image_path.lower().endswith(".pdf"):    
            for i, page in enumerate(self.image_pages):
                temp_filename = f"temp_page_{i}.png"
                page.save(temp_filename, "PNG")
                temp_image_files.append(temp_filename)
            text = "\n".join([extract_text_from_image(temp_file) for temp_file in temp_image_files])
        else:
            text = extract_text_from_image(self.image_path)
            
        summary = generate_summary(text)
            
        # Save OCR text to the openai_ocr folder with a timestamp ID
        ocr_filename = f"ocr_text_{self.timestamp}.txt"
        ocr_folder = os.path.join(os.path.expanduser("~"), "Documents", "openai_ocr")
        os.makedirs(ocr_folder, exist_ok=True)
        ocr_filepath = os.path.join(ocr_folder, ocr_filename)
        with open(ocr_filepath, "w") as f:
            f.write(text)
        
        self.summary_ready.emit(text, summary)

class PasswordLineEdit(QLineEdit):
    def displayText(self):
        return "*" * len(super().displayText())
      
class OCRSummarizerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_preferences()
    
    def load_preferences(self):
        preferences_path = os.path.join(os.path.expanduser("~"), "Documents", "openai_ocr", "preferences.json")
        if os.path.exists(preferences_path):
            with open(preferences_path, "r") as f:
                preferences = json.load(f)
            self.api_key_edit.setText(base64.b64decode(preferences.get("api_key", "").encode()).decode())
            self.org_edit.setText(base64.b64decode(preferences.get("organization_id", "").encode()).decode())
            pytesseract.pytesseract.tesseract_cmd = preferences.get("tesseract_path", "")

    def save_preferences(self):
        preferences_path = os.path.join(os.path.expanduser("~"), "Documents", "openai_ocr", "preferences.json")
        os.makedirs(os.path.dirname(preferences_path), exist_ok=True)
        preferences = {
            "api_key":  base64.b64encode(self.api_key_edit.text().strip().encode()).decode(),
            "organization_id": base64.b64encode(self.org_edit.text().strip().encode()).decode(),
            "tesseract_path": pytesseract.pytesseract.tesseract_cmd,
        }
        with open(preferences_path, "w") as f:
            json.dump(preferences, f)

    def init_ui(self):
        self.setWindowTitle("OCR Scanner & Summarizer")

        layout = QVBoxLayout()

        self.api_key_label = QLabel("OpenAI API Key:")
        layout.addWidget(self.api_key_label)

        self.api_key_edit = PasswordLineEdit()
        layout.addWidget(self.api_key_edit)
        
        self.org_label = QLabel("OpenAI Organization:")
        layout.addWidget(self.org_label)
        
        self.org_edit = PasswordLineEdit()
        layout.addWidget(self.org_edit)
        
        self.tesseract_label = QLabel("Tesseract Executable:")
        layout.addWidget(self.tesseract_label)

        self.tesseract_edit = QLineEdit()
        self.tesseract_edit.setReadOnly(True)
        layout.addWidget(self.tesseract_edit)

        self.tesseract_button = QPushButton("Browse")
        self.tesseract_button.clicked.connect(self.browse_tesseract)
        layout.addWidget(self.tesseract_button)

        self.image_scroll_area = QScrollArea()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_scroll_area.setWidget(self.image_label)
        self.image_scroll_area.setWidgetResizable(True)
        layout.addWidget(self.image_scroll_area)

        self.text_scroll_area = QScrollArea()
        self.text_edit = QTextEdit()
        self.text_scroll_area.setWidget(self.text_edit)
        self.text_scroll_area.setWidgetResizable(True)
        layout.addWidget(self.text_scroll_area)

        self.load_image_button = QPushButton("Load Image")
        self.load_image_button.clicked.connect(self.load_image)
        layout.addWidget(self.load_image_button)

        self.summarize_button = QPushButton("Summarize")
        self.summarize_button.clicked.connect(self.summarize)
        layout.addWidget(self.summarize_button)

        self.setLayout(layout)
        
    def browse_tesseract(self):
        if not hasattr(self, "file_dialog"):
            self.file_dialog = QFileDialog(self)

        options = QFileDialog.Option.ReadOnly
        file_name, _ = self.file_dialog.getOpenFileName(caption="Select Tesseract Executable", filter="Executable Files (*.exe);;All Files (*)", options=options)

        if file_name:
            self.tesseract_edit.setText(file_name)
            pytesseract.pytesseract.tesseract_cmd = file_name

    def load_image(self):
        if not hasattr(self, "file_dialog"):
            self.file_dialog = QFileDialog(self)

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
            # Wrap the existing summary generation process in a separate function
            self.worker = SummaryWorker(self.image_path, self.image_pages)
            self.worker.summary_ready.connect(self.display_summary)
            QThreadPool.globalInstance().start(self.worker.process_image_and_generate_summary)
        else:
            self.text_edit.setPlainText("Please load an image or PDF first.")
    
    def display_summary(self, text, summary):  # Add 'text' as an argument
        self.text_edit.setPlainText(summary)
        
        # Save OCR text to the openai_ocr folder with a timestamp ID
        ocr_filename = f"ocr_text_{self.worker.timestamp}.txt"
        ocr_folder = os.path.join(os.path.expanduser("~"), "Documents", "openai_ocr")
        os.makedirs(ocr_folder, exist_ok=True)
        ocr_filepath = os.path.join(ocr_folder, ocr_filename)
        with open(ocr_filepath, "w") as f:
            f.write(text)

        # Save OpenAI response to the openai_ocr folder with a timestamp ID
        openai_filename = f"openai_response_{self.worker.timestamp}.txt"
        openai_folder  = os.path.join(os.path.expanduser("~"), "Documents", "openai_ocr")
        os.makedirs(openai_folder , exist_ok=True)
        openai_filepath  = os.path.join(openai_folder , openai_filename)
        with open(openai_filepath , "w") as f:
            f.write(summary)
    
    def closeEvent(self, event):
        self.save_preferences()
        super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    window = OCRSummarizerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()