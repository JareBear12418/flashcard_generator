from __future__ import division
import json
import os
from googlesearch import search
import cv2
import numpy as np
from random import shuffle
clear = lambda: os.system('cls')

with open('data.json') as f:
    d = json.load(f)
i: int = 0
topics = list(d.keys())
shuffle(topics)
while True:
    # for i, topic in enumerate(d):
    try:
        topic = topics[i]
    except IndexError:
        break
    if len(d[topic][1]['paths']) == 0 or topic == 'Useful notes':
        i+=1
        continue
    clear()
    paths_to_notes = d[topic][1]['paths']
    description = d[topic][0]['dictionary']
    if description:
        print(f'type "next" for next topic\t"d" - description\t"s" - view sources (wiki)\t"notes" - view notes\t"exit" - exit\n')
    else:
        print(f'type "next" for next topic\t"s" - view sources (wiki)\t"notes" - view notes\t"exit" - exit\n')
    print(f'What is {topic}?')
    input_call = input('')
    if input_call == 'd' and description:
        print(f'The descripion for {topic} is: "{description[0]}"')
        input_call = input('')
    elif input_call == 's':
        print('Looking up sources. Please wait.')
        sources = search(f"\"defination\" of \"{topic}\" \"wikipedia\"", num_results=5)
        print(f'Found {len(sources)} sources!')
        for source in sources:
            print(source)
            
        input_call = input('')
    elif input_call == 'n':
        for path in paths_to_notes:
            
            img = cv2.imread(path)

            screen_res = 1380, 920
            scale_width = screen_res[0] / img.shape[1]
            scale_height = screen_res[1] / img.shape[0]
            scale = min(scale_width, scale_height)
            window_width = int(img.shape[1] * scale)
            window_height = int(img.shape[0] * scale)

            cv2.namedWindow(topic, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(topic, window_width, window_height)

            cv2.imshow(topic, img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        input_call = input('')
    elif input_call == 'next':
        i+=1
    elif input_call == 'exit':
        break