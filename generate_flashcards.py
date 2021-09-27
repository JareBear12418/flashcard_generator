
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

clear = lambda: os.system('cls')
# https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    # created function to clear terminal
    clear()
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()
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
    
    printProgressBar(0, len(all_file_names), prefix = 'Generating flashcards', suffix = 'Complete', length = 50)
    all_file_names.sort(key=NATSORT_KEY)
    all_file_names_full_path = [location + name for name in all_file_names]
    number: int = 0
    KEYWORDS = calendar.month_name[1:]
    KEYWORDS += ['PM', 'AM', '2021', '2022', '2023', '2024', '2025', '2026']
    KEYWORDS += [str(num) for num in range(0,32)]
    
    data = {}

    for i, file in enumerate(all_file_names_full_path):
        pytesseract.pytesseract.tesseract_cmd = "C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"
        img = cv2.imread(file)
        
        # we need to find the title/topic of the page, and the keywords (Month, date, time, year, etc.)
        # We first crop the image, this speeds up performance, and we are ONLY interested in
        # The first part of the page anyway, as this will always contain the title/topic, and keywords.
        printProgressBar(0, 10, prefix = 'Processing image', suffix = 'Complete', length = 50)
        _, width = img.shape[0:2]
        startRow = int(100)
        startCol = int(0)
        endRow = int(350) # we only go 350 pixels down, because the keywords never go furhter down than that.
        endCol = int(width) # We go to the width of the document because titles could be long.
        printProgressBar(1, 10, prefix = 'Cropping image', suffix = 'Complete', length = 50)
        croppedImage = img[startRow:endRow, startCol:endCol] # We crop the image accordingly to the values above.
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
        printProgressBar(2, 10, prefix = 'Blurring image', suffix = 'Complete', length = 50)
        dst = cv2.GaussianBlur(croppedImage,(59,59),0) # We blur the image.
        printProgressBar(3, 10, prefix = 'Threshing image', suffix = 'Complete', length = 50)
        gray = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY) # convert to grayscale
        # threshold to get just the signature (INVERTED)
        retval, thresh_gray = cv2.threshold(gray, thresh=254, maxval=255, \
                                        type=cv2.THRESH_BINARY_INV)
        printProgressBar(4, 10, prefix = 'Re-bluring image', suffix = 'Complete', length = 50)
        dst1 = cv2.GaussianBlur(thresh_gray,(59,59),0)
        printProgressBar(5, 10, prefix = 'Processing image', suffix = 'Complete', length = 50)
        invert = cv2.bitwise_not(dst1)
        printProgressBar(6, 10, prefix = 'Re-Threshing image', suffix = 'Complete', length = 50)
        retval1, thresh_gray1 = cv2.threshold(invert, thresh=254, maxval=255, \
                                        type=cv2.THRESH_BINARY_INV)

        printProgressBar(7, 10, prefix = 'Re-cropping image', suffix = 'Complete', length = 50)
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
        printProgressBar(8, 10, prefix = 'Getting text from image', suffix = 'Complete', length = 50)
        title = pytesseract.image_to_string(roi) # feed the final processed image to tesseract
        printProgressBar(9, 10, prefix = 'Cleaning up text', suffix = 'Complete', length = 50)
        # Do some wored clean ups
        title = title.replace('|', 'l')
        key_words = title.split('\n')[1:]
        original_title = title.split('\n')[0]
        title = slugify(title.split('\n')[0]) # Make our title safe for file names.
        data.update({original_title:[{'dictionary':[]},{'paths':[]}]}) # set up our dictionary for the orginizing stage.
        key_words = ' '.join(key_words)
        key_words = key_words.split(' ')
        key_words = [x for x in key_words if x != '']
        # If the page's keywords match up with the KEYWORDS that we defined, then we proceed in this statement.
        # Keywords from the document are found under the topic name
        # Such as the month name, year, and time. if ANY of those match the set specs.
        # Then it passes.
        # This is how we determin if its a 'continuing' page or a 'new' page.
        
        printProgressBar(10, 10, prefix = 'Saving data', suffix = 'Complete', length = 50)
        if list(set(key_words).intersection(KEYWORDS)): # This copares both lists, and lets us know: True, there are matching items. Or False, there are no matching items.
            os.rename(file, location + title + '.jpg')
            number = 0
            previous_title = title
            data[original_title][1]['paths'].append(location + title + f'{number}.jpg') # Save stuff.
            meaning = dictionary.meaning(original_title.split('/')[0])
            if (meaning):
                data[original_title][0]['dictionary'].append(meaning['Noun'][0])
            previous_title = title
            previous_original_title = original_title
        else:
            # This is a continuing page, so we give it the same title as the starting page, but with an
            # incremented number.
            number += 1
            os.rename(file, location + previous_title + f'{number}.jpg')
            data[previous_original_title][1]['paths'].append(location + previous_title + f'{str(number)}.jpg')
        time.sleep(0.5)
        printProgressBar(i+1, len(all_file_names), prefix = 'Generating flashcards', suffix = 'Complete', length = 50)
    # Save our data so that it can be used by practice_flashcards.py for studying :P
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=True, indent=4)
    clear()
    print('Finished!')

if __name__ == '__main__':
    # In case the program fails, and the file exists with contents, we want to delete it,
    # so that no further error occurs.
    try:
        shutil.rmtree(os.getcwd() + '/flashcards/')
    except FileNotFoundError: 
        pass
    file_name = 'test.pdf'
    printProgressBar(0, 1, prefix = 'Converting pdf to images.', suffix = 'Complete', length = 50)
    convert_pdf_to_images(file_name, 'flashcards')
    printProgressBar(1, 1, prefix = 'Converting pdf to images.', suffix = 'Complete', length = 50)
    time.sleep(0.5)
    printProgressBar(0, 1, prefix = 'Generating flashcards', suffix = 'Complete', length = 50)
    generate_cards(os.getcwd() + '/flashcards/' + file_name.replace('.pdf', '.pdf_dir/'))
    
