
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
import time
import argparse
import sys

# pip install PyDictionary opencv-python pytesseract pdf2jpg natsort

dictionary=PyDictionary()

PATH_TO_THIS_FOLDER: str = 'C:/Users/jared/Documents/Code/flashcard_generator'

NATSORT_KEY = natsort_keygen()

clear = lambda: os.system('cls')

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

def generate_cards(location, json_file):
    all_file_names = os.listdir(location)

    all_file_names.sort(key=NATSORT_KEY)
    all_file_names_full_path = [location + name for name in all_file_names]
    number: int = 0
    KEYWORDS = calendar.month_name[1:]
    KEYWORDS += ['PM', 'AM', '2021', '2022', '2023', '2024', '2025', '2026']
    KEYWORDS += [str(num) for num in range(32)]

    data = {}

    startRow = int(100) #x1
    startCol = int(0) #y1
    endRow = int(350) # we only go 350 pixels down, because the keywords never go furhter down than that.
    for i, file in enumerate(all_file_names_full_path):
        pytesseract.pytesseract.tesseract_cmd = "C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"
        img = cv2.imread(file)

        # we need to find the title/topic of the page, and the keywords (Month, date, time, year, etc.)
        # We first crop the image, this speeds up performance, and we are ONLY interested in
        # The first part of the page anyway, as this will always contain the title/topic, and keywords.
        _, width = img.shape[0:2]
        # _, width = [e for e in img.tile if e[1][2] < 1200 and e[1][3] < 1200]
        endCol = int(width) # We go to the width of the document because titles could be long.
        # print(f'{startRow}:{endRow}, {startCol}:{endCol}')
        croppedImage = img[startRow:endRow, startCol:endCol] # We crop the image accordingly to the values above.
        #  x1, y1, x2, y2
        # box = (startRow, startCol, endCol, endRow)
        # croppedImage = img.crop(box)
        # The proceeding process is confusing, and wacky, so I'll do my best to explain everything here.
        '''
        From the cropped image, we blur the image to its MAX. this way we can thresh the image on a very
        precise threshold, to find out WHERE exactly the title and keywords are. 
            The more precise we are with this, the better the OCR will be, and the quicker everyhing is
            processed.
        Once we have done the threshold process, we then REPEAT it again, why? 
            Because if we dont, sometimes the title AND keywords are spaced far apary, if they are spaced 
            far apart, the next process it has to do (which finds the biggest region of pixels) will
            sometimes pick the topic (if its long) as the biggest region, COMPLETLY ignoring the keywords.
            Thats a problem, because we want more precision, so by redoing the entire process again, we
            ensure that the region of text will ALWAYS be found, including all keywords and the title.
        Next we find the biggest contour, or biggest region of pixels. 
        We crop this region OUT from the orginal image, and USE this as the input for OCR.
            We could downscale the image for faster processing of OCR, while this could speed it up
            a bit, i'll just leave it as is, as it seems to work fairly well.
        '''
        dst = cv2.GaussianBlur(croppedImage,(59,59),0) # We blur the image.
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

        roi=croppedImage[y:y+h,x:x+w] # final output, and this the input for pytesseract
        try:
            title = pytesseract.image_to_string(roi) # feed the final processed image to tesseract
        except:
            os.remove(file)
            continue
        # Do some wored clean ups
        title = title.replace('|', 'l').replace('l\/l', 'M').replace('Rehab??????y','Reliability').replace('Deb???e???ng', 'Debriefing').replace('In e rtla','Inertia').replace('Nega???vefeedback', 'Negative feedback').replace('Con???guhy', 'Contiguity').replace('Vv','W')

        
        key_words = title.split('\n')[1:]
        original_title = title.split('\n')[0]
        # original_title += file.split('/')[-1].split('_')[0]
        title = slugify(title.split('\n')[0]) # Make our title safe for file names.
        print(f'{i+1}/{len(all_file_names_full_path)} Generating flashcards: {original_title}')
        # title += file.split('/')[-1].split('_')[0]
        data.update({original_title:[{'dictionary':[]},{'paths':[]}]}) # set up our dictionary for the orginizing stage.
        key_words = ' '.join(key_words)
        key_words = key_words.split(' ')
        key_words = [x for x in key_words if x != '']
        # If the page's keywords match up with the KEYWORDS that we defined, then we proceed in this statement.
        # Keywords from the document are found under the topic name
        # Such as the month name, year, and time. if ANY of those match the set specs.
        # Then it passes.
        # This is how we determin if its a 'continuing' page or a 'new' page.

        if list(set(key_words).intersection(KEYWORDS)): # This copares both lists, and lets us know: True, there are matching items. Or False, there are no matching items.
            number = 0
            try:
                os.rename(file, location + title + f'{number}.jpg')
            except FileExistsError:
                print(f'Specific File: {file}\nTopic: {original_title}\nFile Name: {title}{number}.jpg\nAlready exists')
                return
            previous_title = title
            data[original_title][1]['paths'].append(location + title + f'{number}.jpg') # Save stuff.
            meaning = dictionary.meaning(original_title.split('/')[0])
            if (meaning):
                try:
                    data[original_title][0]['dictionary'].append(meaning['Noun'][0])
                except KeyError:
                    try:
                        data[original_title][0]['dictionary'].append(meaning['Adjective'][0])
                    except KeyError:
                        pass
            previous_title = title
            previous_original_title = original_title
        else:
            # This is a continuing page, so we give it the same title as the starting page, but with an
            # incremented number.
            number += 1
            try:
                os.rename(file, location + previous_title + f'{number}.jpg')
                data[previous_original_title][1]['paths'].append(
                    location + previous_title + f'{number}.jpg'
                )
            except UnboundLocalError:
                previous_title = title
                previous_original_title = original_title
                os.rename(file, location + previous_title + f'{number}.jpg')
                data[previous_original_title][1]['paths'].append(
                    location + previous_title + f'{number}.jpg'
                )

    # Save our data so that it can be used by practice_flashcards.py for studying :P
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=True, indent=4)
        
    print('Finished!')
    time.sleep(3)
    sys.exit()

def main(file_name):
    pdf_path = os.getcwd() + '/' + file_name
    try:
        shutil.rmtree(PATH_TO_THIS_FOLDER + '/flashcards/' + file_name.replace('.pdf', '.pdf_dir/'))
    except FileNotFoundError: 
        pass
    
    print('Converting pdf to images.')

    convert_pdf_to_images(pdf_path, PATH_TO_THIS_FOLDER + '/flashcards')
    
    json_folder = PATH_TO_THIS_FOLDER + '/flashcards/' + 'JSON_DATA/'
    if not os.path.isdir(json_folder): 
        os.mkdir(json_folder)
        
    generate_cards(PATH_TO_THIS_FOLDER + '/flashcards/' + file_name.replace('.pdf', '.pdf_dir/'), json_folder + file_name.replace('.pdf', '.json'))


file_name = sys.argv[-1].split('\\')[-1]
main(file_name)
    