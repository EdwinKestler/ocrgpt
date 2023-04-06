from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from utils import extract_text_from_image, generate_summary
import time
import os

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
