import cv2
import pytesseract
import openai
from pdf2image import convert_from_path

def set_tesseract_path(path):
    pytesseract.pytesseract.tesseract_cmd = path

def get_tesseract_path():
    return pytesseract.pytesseract.tesseract_cmd

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