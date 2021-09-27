
from pdf2jpg import pdf2jpg
import os
import shutil
import cv2
import pytesseract
import re
import unicodedata
import calendar
from natsort import natsort_keygen
import json
from PyDictionary import PyDictionary
from googlesearch import search
import numpy as np
import time
dictionary=PyDictionary()
# pip install PyDictionary opencv-python pytesseract pdf2jpg natsort
NATSORT_KEY = natsort_keygen()

def convert_pdf_to_images(pdf_path: str, output_path: str):
    pdf2jpg.convert_pdf2jpg(pdf_path, output_path, pages="ALL")

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

def generate_cards(location):
    all_file_names = os.listdir(location)
    all_file_names.sort(key=NATSORT_KEY)
    all_file_names_full_path = [location + name for name in all_file_names]
    number: int = 0
    previous_title: str = ''
    KEYWORDS = calendar.month_name[1:]
    KEYWORDS += ['PM', 'AM', '2021', '2022', '2023', '2024', '2025', '2026']
    KEYWORDS += [str(num) for num in range(0,32)]
    
    data = {}

    for i, file in enumerate(all_file_names_full_path):
        pytesseract.pytesseract.tesseract_cmd = "C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"
        img = cv2.imread(file)
        
        _, width = img.shape[0:2]
        startRow = int(100)
        startCol = int(0)
        endRow = int(350)
        endCol = int(width)
        croppedImage = img[startRow:endRow, startCol:endCol]
        dst = cv2.GaussianBlur(croppedImage,(59,59),0)
        gray = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY) # convert to grayscale
        # threshold to get just the signature (INVERTED)
        retval, thresh_gray = cv2.threshold(gray, thresh=254, maxval=255, \
                                        type=cv2.THRESH_BINARY_INV)
        dst1 = cv2.GaussianBlur(thresh_gray,(59,59),0)
        invert = cv2.bitwise_not(dst1)
        retval1, thresh_gray1 = cv2.threshold(invert, thresh=254, maxval=255, \
                                        type=cv2.THRESH_BINARY_INV)

        contours, hierarchy = cv2.findContours(thresh_gray1,cv2.RETR_LIST, \
                                        cv2.CHAIN_APPROX_SIMPLE)

        # Find object with the biggest bounding box
        mx = (0,0,0,0)      # biggest bounding box so far
        mx_area = 0
        for cont in contours:
            x,y,w,h = cv2.boundingRect(cont)
            area = w*h
            if area > mx_area:
                mx = x,y,w,h
                mx_area = area
        x,y,w,h = mx

        # Output to files
        roi=croppedImage[y:y+h,x:x+w]
        title = pytesseract.image_to_string(roi)
        title = title.replace('|', 'l')
        key_words = title.split('\n')[1:]
        original_title = title.split('\n')[0]
        title = slugify(title.split('\n')[0])
        data.update({original_title:[{'dictionary':[]},{'paths':[]}]})
        key_words = ' '.join(key_words)
        key_words = key_words.split(' ')
        key_words = [x for x in key_words if x != '']
        try:
            if list(set(key_words).intersection(KEYWORDS)):
                os.rename(file, location + title + '.jpg')
                number = 0
                previous_title = title
                data[original_title][1]['paths'].append(location + title + '.jpg')
                meaning = dictionary.meaning(original_title.split('/')[0])
                if (meaning):
                    data[original_title][0]['dictionary'].append(meaning['Noun'][0])
                previous_title = title
                previous_original_title = original_title
            else:
                number += 1
                os.rename(file, location + previous_title + f'{str(number)}.jpg')
                data[previous_original_title][1]['paths'].append(location + previous_title + f'{str(number)}.jpg')
        except UnboundLocalError:
            previous_title = title
            previous_original_title = original_title
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=True, indent=4)

if __name__ == '__main__':
    try:
        shutil.rmtree(os.getcwd() + '/flashcards/')
    except FileNotFoundError: 
        pass
    file_name = 'test.pdf'
    convert_pdf_to_images(file_name, 'flashcards')
    generate_cards(os.getcwd() + '/flashcards/' + file_name.replace('.pdf', '.pdf_dir/'))
    
