import os
import sys
import textwrap
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
# python translator.py <input_pdf_file_path> <google_cloud_project_id> (optional)<target_language_code> (optional)<source_language_code>
# Will output translated text to a file called "translated_text" in same directory
# Defaults to English if no target language code is provided
# Uses ISO 639-1 Language Codes

IMAGE_FOLDER = "translator_images"

def pdf_to_pics(infile: str) -> list:
    dpi = 500
    pages = convert_from_path(infile, dpi)

    for count, page in enumerate(pages):
        file_path = os.path.join(IMAGE_FOLDER, f"page_{count}.jpg")
        page.save(file_path, 'JPEG')

    return len(pages)


def pic_to_text(infile: str) -> str:
    client = vision.ImageAnnotatorClient()

    with open(infile, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    # For dense text, use document_text_detection
    # For less dense text, use text_detection
    response = client.document_text_detection(image=image)
    text = response.full_text_annotation.text

    return text

def translate_text(
    text: str,
    project_id: str,
    target_language_code: str,
    source_language_code: str = None,
) -> str:
    client = translate.TranslationServiceClient()

    parent = f"projects/{project_id}"

    request={
        "parent": parent,
        "contents": [text],
        "mime_type": "text/plain",
        "target_language_code": target_language_code,
    }
    if source_language_code:
        request["source_language_code"] = source_language_code

    result = client.translate_text(request=request)

    return result.translations[0].translated_text


# Command line options
infile = sys.argv[1]
google_cloud_project_id = sys.argv[2]
target_language_code = sys.argv[3] if len(sys.argv) > 3 else "en"
source_language_code = sys.argv[4] if len(sys.argv) > 4 else None


if not os.path.isdir(IMAGE_FOLDER):
    print ("Creating image folder...")
    os.mkdir(IMAGE_FOLDER)
else:
    print("Clearing image folder...")
    for entry in os.scandir(IMAGE_FOLDER):
        os.remove(entry.path)

print("Converting PDF to images...")
num_pics = pdf_to_pics(infile)

output_file = "translated_text.txt"

print("Clearing output file...")
with open(output_file, 'w'):
    pass

print("Translating text...")
current_pic = 0
f = open(output_file, "a", encoding="utf-8")
for entry in os.scandir(IMAGE_FOLDER):
    current_pic += 1
    print(f"Translating image {current_pic}/{num_pics}")
    text_to_translate = pic_to_text(entry.path)
    translated_text = translate_text(
        text_to_translate, google_cloud_project_id, target_language_code, source_language_code
    )
    # Remove "Machine Translated by Google"
    stripped_text = translated_text[30:]
    f.write(textwrap.fill(stripped_text, width=100) + "\n\n")

f.close()