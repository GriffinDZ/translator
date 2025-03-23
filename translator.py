import os
import sys
from google.cloud import translate_v3beta1 as translate
from google.cloud import vision
from pdf2image import convert_from_path

# Followed tutorial here: https://cloud.google.com/translate/docs/hybrid-glossaries-tutorial#windows

# MAKE SURE TO HAVE BILLING AND BUDGET ALERTS SET UP FOR YOUR GOOGLE CLOUD PROJECT
# THESE APIS ARE CHEAP BUT CAN GO NUTS IF YOU AREN'T CAREFUL

# Necessary resources:
# Google Cloud Vision API & Translation API in a Google Cloud Project
# Poppler for pdf2image
# pip install google-cloud-vision google-cloud-translate pdf2image

# Per terminal session, set environment variables:
# Set environment variable for Google Application Credentials (JSON key)
#    WINDOWS: export GOOGLE_APPLICATION_CREDENTIALS="path_to_key"

# Usage:
# python translator.py <input_pdf_file_path> <google_cloud_project_id>
# Will output translated text to a file called "translated_text" in same directory

IMAGE_FOLDER = "translator_images"

def pdf_to_pics(infile: str) -> list:
    dir = IMAGE_FOLDER
    if not os.path.isdir(IMAGE_FOLDER):
        os.mkdir(IMAGE_FOLDER)

    dpi = 500
    pages = convert_from_path(infile, dpi)

    for count, page in enumerate(pages):
        file_path = os.path.join(dir, f"page_{count}.jpg")
        page.save(file_path, 'JPEG')


def pic_to_text(infile: str) -> str:
    client = vision.ImageAnnotatorClient()

    with open(infile, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    # For dense text, use document_text_detection
    # For less dense text, use text_detection
    response = client.document_text_detection(image=image)
    text = response.full_text_annotation.text
    print(f"Detected text: {text}")

    return text

def translate_text(
    text: str,
    target_language_code: str,
    project_id: str,
) -> str:
    client = translate.TranslationServiceClient()

    parent = f"projects/{project_id}"

    result = client.translate_text(
        request={
            "parent": parent,
            "contents": [text],
            "mime_type": "text/plain",  # mime types: text/plain, text/html
            "target_language_code": target_language_code,
        }
    )

    # Extract translated text from API response
    return result.translations[0].translated_text

infile = sys.argv[1]
google_cloud_project_id = sys.argv[2]

pdf_to_pics(infile)

f = open("translated_text.txt", "a")
for entry in os.scandir(IMAGE_FOLDER):
    text_to_translate = pic_to_text(entry.path)
    translated_text = translate_text(
        text_to_translate, "en", google_cloud_project_id
    )
    f.write(translated_text)
    f.close()
