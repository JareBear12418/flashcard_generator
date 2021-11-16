from functools import total_ordering
import json
import os
from typing import final
from googlesearch import search
import cv2
import sys
from random import shuffle
import time
import msvcrt
from time import strptime
from numbers import Number
import cmd
from prettytable import PrettyTable
from datetime import datetime, timedelta
import string
import random
# pip install prettytable
clear = lambda: os.system('cls')
START_STUDYING_TIME: datetime.now() = datetime.now()
'''
This variable (WORK_FROM_DEFINATION) has a questionable name, took me to long do even decide with this one
so I decided ill just name it this and suffer writing an explanation what its responsible for.

If this variable is set to True.
The program will start with the defination of the topic (if available) and show you the notes you 
have for it. and from those notes, you type into the console what that topic is. (your notes shouldn't contain
the answer, that defeats the purpose of flashcards, although small hints are okay) If you get it right, you go to the next question.

If this variable is set to False.
The program will show you the topic, and you have to explain to yourself or others what it means, theres no
legit, to type in the answer and check if its right, but youll have to be honest with your self. You can view a 
defination (if available) or notes by using the provided commands. This doesn't track points, as theres no way
to do that.
'''
WORK_FROM_DEFINATION: bool = True

PATH_TO_THIS_FOLDER: str = 'C:/Users/jared/Documents/Code/flashcard_generator'

# Delay between getting the answer correc/incorrect and the next flashcard
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
number_and_ordered_topics = []
completed_topics = []
sum_of_time: int = 0
def print_commands_list(description, topics, show_topics: bool = False, progress = "", show_words_list: bool = True, show_times: bool = False):
    global completed_topics, number_and_ordered_topics, sum_of_time
    number_and_ordered_topics.clear()
    if description:
        print(
            f'type "next" for next topic\t"d" - description\t"s" - view sources (wiki)\t"notes" - view notes\t"exit" - exit {progress if progress != "" else ""}\n'
        )

    else:
        print(
            f'type "next" for next topic\t"s" - view sources (wiki)\t"notes" - view notes\t"exit" - exit {progress if progress != "" else ""}\n'
        )
    if show_topics:
        topics = sorted(topics)
        completed_topics = sorted(completed_topics)
        # for i, topic in enumerate(topics):
        #     for ctopic in completed_topics:
        #         if topic in ctopic:
        #             topics.pop(i)
        # topics.extend(completed_topics)
        alphabets = list(string.ascii_lowercase)
        alphabet_indexes: dict = {} # this variable name doesnt make sense
        alphabet_indexes.update({'other':[{'index': 0},{'topics':[]}]})
        for alphabet in alphabets:
            alphabet_indexes.update({alphabet:[{'index': 0},{'topics':[]}]})

        for i, topic in enumerate(topics, start=1):
            try:
                first_letter = topic[0].lower()
            except IndexError:
                alphabet_indexes['other'][0]['index'] += 1
                alphabet_indexes['other'][1]['topics'].append(f'{topic}')
                continue
            try:
                alphabet_indexes[first_letter][0]['index'] += 1
                alphabet_indexes[first_letter][1]['topics'].append(f'{topic}')
            except KeyError:
                alphabet_indexes['other'][0]['index'] += 1
                alphabet_indexes['other'][1]['topics'].append(f'{topic}')
        # for topic in topics:
        alphabet_keys = list(alphabet_indexes.keys())
        new_list = []
        overall_count: int = 1
        for key in alphabet_keys:
            # print(t for t in )
            index = alphabet_indexes[key][0]['index']
            if index != 0:
                new_list.append(f'{key.upper()} - {index}')
                for t in alphabet_indexes[key][1]['topics']:
                    new_list.append(f'  {overall_count}) {t}')
                    number_and_ordered_topics.append(t)
                    overall_count += 1
            # new_list.append(t for t in alphabet_indexes[key][1]['topics'])
        # topics = [f'{i}) {topic}' for i, topic in enumerate(topics, start=1)]
        new_list.extend(completed_topics)
        cli = cmd.Cmd()
        cli.columnize(new_list, displaywidth=200)
        print('\n')
'''
    No idea how this function works, I just snatched it from SO, and it worked.
    https://stackoverflow.com/questions/11563615/matching-incorrectly-spelt-words-with-correct-ones-in-python
'''
def compare_words(u1: str, u2: str):
    '''
    Checks to see how similar the words are.
    It returns how many mistakes have been made in spelling.
    I have set the mininum number of mistakes to be 5.
    
    If the answer is "Theory", and you guessed: "thoery"
    This would still be correct as there is only one mistake.
    
    If the answer is "Population" and you guessed: "pupolation"
    This would still be correct as there are only 2 mistakes.
    
    So a maxinum of 6 mistakes, is pretty close to the real deal...
    '''
    try:
        s1 = unicode(u1)    
        s2 = unicode(u2)
    except:
        s1 = u1
        s2 = u2        
    if len(s1) < len(s2):
        return compare_words(u2, u1)
    if not s1:
        return len(s2)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def differnce_in_time(date: str) -> datetime:
    now = datetime.now()
    date = date.replace('  ', ' ')
    split_date = date.split(' ')
    year = int(split_date[-1])
    month_number = strptime(split_date[1], '%b').tm_mon
    day = int(split_date[2])
    hour = int(split_date[3].split(':')[0])
    minute = int(split_date[3].split(':')[1])
    second = int(split_date[3].split(':')[-1])
    new_date = datetime(year, month_number, day, hour, minute, second) #yr, mo, day, hr, min, sec
    return now-new_date

def show_notes(paths_to_notes, topic):
    startCol = int(0)
    for index, path in enumerate(paths_to_notes):
        try:
            img = cv2.imread(path)
        except: continue
        height, width = img.shape[0:2]
        startRow = int(350 if index == 0 else 0)
        endRow = int(height)
        endCol = int(width) # We go to the width of the document because titles could be long.
        croppedImage = img[startRow:endRow, startCol:endCol] # We crop the image accordingly to the values above.

        # Rescale the image so it fits to the screen.
        screen_res = 1380, 920
        scale_width = screen_res[0] / croppedImage.shape[1]
        scale_height = screen_res[1] / croppedImage.shape[0]
        scale = min(scale_width, scale_height)
        window_width = int(croppedImage.shape[1] * scale)
        window_height = int(croppedImage.shape[0] * scale)

        cv2.namedWindow("_" * len(topic), cv2.WINDOW_NORMAL)
        cv2.resizeWindow("_" * len(topic), window_width, window_height)

        cv2.imshow("_" * len(topic), croppedImage)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

def main(json_file, isTimed: bool = False, show_list_of_topics:bool=True, multiple_choices:bool=False):
    global completed_topics, START_STUDYING_TIME, number_and_ordered_topics, sum_of_time
    # with open(json_file) as f:
    #     d = json.load(f)
    d = json_file
    CONSTANT_UNCHANGED_TOPICS = list(d.keys())
    topics = list(d.keys())
    for num, t in enumerate(topics):
        if len(t) > 40 or len(t) <= 3:
            topics.pop(num)
    i: int = 0
    showed_notes = False
    number_of_correct: int = 0
    number_of_completed: int = -1 # Because im to lazy to actually fix this.
    seconds_in_day = 24 * 60 * 60
    
    # Untill we have went through all topics.
    while True:
        number_of_completed += 1
        START_TOPIC_TIME = datetime.now()
        try:
            topic = topics[i]
            answer = topic.replace(' ', '')
            paths_to_notes = d[topic][1]['paths']
            description = d[topic][0]['dictionary']
            
            '''
            Instead of choosing random WRONG topics, we can look for topics that are similar to the 
            originally selected topic, this makes it harder to guess some topics and adds a level
            of difficultiy.
            '''
            similarity_score = {}
            for t in CONSTANT_UNCHANGED_TOPICS:
                if t != topic:
                    similarity_score.update({t:int(compare_words(topic, t))})
                
            similarity_score = dict(sorted(similarity_score.items(), key=lambda item: item[1]))
            words_sorted_by_similarity = list(similarity_score.keys())
            options = words_sorted_by_similarity[:5] # Just grabbing the first 5.
            answer_and_possible_answers = []
            for index_of_option, same_index in enumerate(options):
                answer_and_possible_answers.append(same_index)
            answer_and_possible_answers.append(topic)
            shuffle(answer_and_possible_answers)
        except Exception as e:
            print(e)
            clear()
            print_commands_list(
                description=description,
                topics=topics,
                show_topics=True,
                progress=f'\tCorrect: {number_of_correct}/{number_of_completed}\tTopics left: {len(topics)}\tPercentage: {round((number_of_correct/number_of_completed)*100, 1)}%',
            )
            
            difference = datetime.now()-START_STUDYING_TIME
            minutes, seconds = divmod(difference.days * seconds_in_day + difference.seconds, 60) 
            
            print(f"It took: {minutes} minutes and {seconds} seconds to finish {(len(completed_topics))} topics, with an agerage of {round(sum_of_time/len(completed_topics),2)} seconds per topic! You can review your finals results.")
            break
        # We skip these
        if len(d[topic][1]['paths']) == 0 or topic == 'Useful notes' or topic == "" or topic == " ":
            topics.pop(i)
            continue
        clear()
        if WORK_FROM_DEFINATION:
            try:
                print_commands_list(
                    description=description,
                    topics=topics,
                    show_topics=show_list_of_topics,
                    progress=f'\tCorrect: {number_of_correct}/{number_of_completed}\tTopics left: {len(topics)}\tPercentage: {round((number_of_correct/number_of_completed)*100, 1)}%',
                )
            except ZeroDivisionError:
                print_commands_list(
                    description=description,
                    topics=topics,
                    show_topics=show_list_of_topics,
                    progress=f'\tCorrect: {number_of_correct}/{number_of_completed}\tTopics left: {len(topics)}\tPercentage: 0%',
                )
            
                
            if multiple_choices:
                for count, answere_or_not in enumerate(answer_and_possible_answers,start=1):
                    print(f'{count}. {answere_or_not}')
                # {"_" * len(topic)}
            input_call = ''
            console_input = []

            if not showed_notes:
                show_notes(paths_to_notes=paths_to_notes, topic=topics)
                showed_notes = True
            # Get user input
            # while True:
            #     x = msvcrt.getch()
            #     if x == b'\r': # Enter breaks the loop and heads onward with the input.
            #         break
            #     elif x == b'\x08': # Backspace
            #         try:
            #             console_input.pop(-1)
            #         except:
            #             console_input = []
            #     else:
            #         try:
            #             console_input.append(x.decode("utf-8"))
            #         except UnicodeDecodeError:
            #             pass
            #     input_call = ''.join(console_input)
            #     clear()
            #     try:
            #         print_commands_list(
            #             description=description,
            #             topics=topics,
            #             show_topics=show_list_of_topics,
            #             progress=f'\tCorrect: {number_of_correct}/{number_of_completed}\tTopics left: {len(topics)}\tPercentage: {round((number_of_correct/number_of_completed)*100, 1)}%',
            #         )
            #     except ZeroDivisionError:
            #         print_commands_list(
            #             description=description,
            #             topics=topics,
            #             show_topics=show_list_of_topics,
            #             progress=f'\tCorrect: {number_of_correct}/{number_of_completed}\tTopics left: {len(topics)}\tPercentage: 0%',
            #         )
                
            #     if multiple_choices:
            #         for count, answere_or_not in enumerate(answer_and_possible_answers,start=1):
            #             print(f'{count}. {answere_or_not}')
            #     if len(input_call) > len(topic):
            #         CURSOR: str = bcolors.FAIL + "█" + bcolors.ENDC
            #     elif len(input_call) == len(topic):
            #         CURSOR: str = bcolors.OKGREEN + "█" + bcolors.ENDC
            #     else:
            #         CURSOR: str = bcolors.OKBLUE + "█" + bcolors.ENDC
            #     CURSOR: str = "█"
            #         # {"_" * (len(topic)-len(console_input)-1)}
                # print(f'This topic is? {input_call}{CURSOR}')

            input_call = input("This topic is?\nAnswer: ")
            
            try:
                if multiple_choices:
                    input_call = answer_and_possible_answers[(int(input_call)-1)]
                input_call = number_and_ordered_topics[(int(input_call)-1)]
            except:
                pass
            input_call = input_call.replace(' ', '')
            if input_call == 'exit':
                break
            elif compare_words(input_call.lower(), answer.lower()) <= (len(answer)/4) and input_call.lower() != 'd' and input_call.lower() != 's'  and input_call.lower() != 'notes' and input_call != '' and input_call != '\n':
                END_TOPIC_TIME = datetime.now()
                elapsed = END_TOPIC_TIME - START_TOPIC_TIME
                minutes, seconds = divmod(elapsed.days * seconds_in_day + elapsed.seconds, 60) 
                seconds += minutes*60
                sum_of_time += seconds
                if (isTimed):
                    if elapsed > timedelta(seconds=30):
                        print(f'{bcolors.OKBLUE}That is correct! But you didn\'t complete it within 30 seconds.{bcolors.ENDC}')
                        completed_topics.append(bcolors.OKBLUE + topics[i] + ' - ' + str(seconds) + 's' + bcolors.ENDC)
                    else:
                        print(f'{bcolors.OKGREEN}That is correct!\n\nThe answer was indeed {topic}.{bcolors.ENDC}')
                        completed_topics.append(bcolors.OKGREEN + topics[i] + ' - ' + str(seconds) + 's' + bcolors.ENDC)
                        number_of_correct+=1
                else:
                    print(f'{bcolors.OKGREEN}That is correct!\n\nThe answer was indeed {topic}.{bcolors.ENDC}')
                    completed_topics.append(bcolors.OKGREEN + topics[i] + ' - ' + str(seconds) + 's' + bcolors.ENDC)
                    number_of_correct+=1
                topics.pop(i)
                showed_notes = False
                shuffle(topics)
                input_call = input('Press ENTER to proceed...')
            elif input_call == 'd':
                if description:
                    print(f'The descripion for {"_" * len(topic)} is: "{description[0]}"')
                else:
                    print('No description available.')
                input_call = input('Press ENTER to proceed...')
            elif input_call == 's':
                print('Looking up sources. Please wait.')
                sources = search(f"\"defination\" of \"{topic}\" \"wikipedia\"", num_results=5)
                print(f'Found {len(sources)} sources!')
                for source in sources:
                    print(source)
                input_call = input('Press ENTER to proceed...')
            elif input_call == 'notes':
                show_notes(paths_to_notes=paths_to_notes, topic=topic)
            elif input_call in ['', 'next', 'idk', '\n', '\r']:
                END_TOPIC_TIME = datetime.now()
                elapsed = END_TOPIC_TIME - START_TOPIC_TIME
                minutes, seconds = divmod(elapsed.days * seconds_in_day + elapsed.seconds, 60) 
                seconds += minutes*60
                sum_of_time += seconds

                print(f'{bcolors.FAIL}The answer was: {topic}{bcolors.ENDC}')
                completed_topics.append(bcolors.WARNING + topics[i] + ' - ' + str(seconds) + 's' + bcolors.ENDC)
                topics.pop(i)
                showed_notes = False
                shuffle(topics)
                input_call = input('Press ENTER to proceed...')
            else:
                END_TOPIC_TIME = datetime.now()
                elapsed = END_TOPIC_TIME - START_TOPIC_TIME
                minutes, seconds = divmod(elapsed.days * seconds_in_day + elapsed.seconds, 60) 
                seconds += minutes*60
                sum_of_time += seconds
                
                print(f'{bcolors.FAIL}That is incorrect!\nThe correct answer is: {topic}{bcolors.ENDC}')
                completed_topics.append(bcolors.FAIL  + topics[i] + ' - ' + str(seconds) + 's' + bcolors.ENDC)
                topics.pop(i)
                showed_notes = False
                shuffle(topics)
                input_call = input('Press ENTER to proceed...')
        else:
            print_commands_list(description=description, topics=topics)
            print(f'What is {topic}?')
            input_call = input('Command: ')
            if input_call == 'd':
                if description:
                    print(f'The descripion for {topic} is: "{description[0]}"')
                else:
                    print('No description available.')
                input_call = input('Press ENTER to proceed...')
            elif input_call == 's':
                print('Looking up sources. Please wait.')
                sources = search(f"\"defination\" of \"{topic}\" \"wikipedia\"", num_results=5)
                print(f'Found {len(sources)} sources!')
                for source in sources:
                    print(source)

                input_call = input('Press ENTER to proceed...')
            elif input_call == 'notes':
                for path in paths_to_notes:

                    img = cv2.imread(path)

                    # Rescale the image so it fits to the screen.
                    screen_res = 1280, 920
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
                input_call = input('Press ENTER to proceed...')
            elif input_call in ['next', 'idk', '']:
                END_TOPIC_TIME = datetime.now()
                elapsed = END_TOPIC_TIME - START_TOPIC_TIME
                completed_topics.append(bcolors.OKGREEN + topics[i] + ' - ' + elapsed + bcolors.ENDC)
                topics.pop(i)
                shuffle(topics)
            elif input_call == 'exit':
                break

def start_up():
    global WORK_FROM_DEFINATION, START_STUDYING_TIME
    clear()
    table = PrettyTable()
    json_file_location = PATH_TO_THIS_FOLDER + '/flashcards/JSON_DATA/'
    all_file_names = os.listdir(json_file_location)
    all_file_names = [json_file_location + file for file in all_file_names]
    creation_date = []
    for file in all_file_names:
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file)
        creation_date.append(time.ctime(mtime))
    print('Please select what you want to study by typing its index.')
    table.field_names = ['Index', 'Study topics', 'Last edited', 'Date created']
    for i, cdate in enumerate(creation_date, start=1):
        file_name = all_file_names[i-1].split('/')[-1].replace('.json', '')
        table.add_row([i,file_name,str(differnce_in_time(cdate)) + ' ago', cdate])
    print(table)
    while True:
        index = input('Index: ')
        if index == 'exit':
            sys.exit()
        try:
            index = int(index)
            break
        except ValueError:
            print('That\'s not a number. Try again.')
    selected_json = all_file_names[index-1]
    t = selected_json.split('/')[-1]
    
    with open(selected_json) as f:
        d = json.load(f) 
    '''
    This mess of code is responsible for selecting different modules, if they are available.
    The way it works is complicated and not well documented, but it works, (just bearly)
    and its a really hacky solution.
    
    The reason it's so complicated, is because I didn't want to change the `generate_flashcards.py` script
    because I would have to recompile it to exe on my system, and change how it compiles the json files.
    
    I would still have to do some re-compiling and what not to get the desired result, but I chose to do this,
    it like this, because it was the first idea I had in mind, and seemed a good one untill I actually tried
    to implment it.
    '''
    try:
        chapter_sorted_json = {}
        # We get all the modules from the json file.
        '''
        This is hacky, because modules are denoted as just a NUMBER. an empty page, with a title
        as a number. So what were looking for here, is for those titles that are just numbers or floats.
        '''
        for key in d.keys():
            try: 
                key = int(key)
            except ValueError:
                try:
                    key = float(key)
                except:
                    continue
            '''
            This if statement might seem pointless, and thats right, it seems pointless.
            
            But due to the nature of OCR and how wrong it can be sometimes, we have to set this boundry.
            '''
            if key > 20:
                continue
            chapter_sorted_json.update({str(key):{}})
        '''
        We need to set the last key as the first one we found if there are any.
        If there are NO numbers in the json file. the program breaks right here, and
        skips to the exception
        '''
        last_key = list(chapter_sorted_json.keys())[0]
    
        '''
        What were doing here is were creating a new dictionary, but sorting the topics 'MODULE' wise.
        
        The way it does that is, if were at module 1, were going to add everything from module 1, until 
        we hit the next number, or module, say 2, then we will switch over to using module 2, and addying 
        everything to module 2, and so on.
        
        It's hard to explain but were addying everything to the module from the original dictionary, untill
        we hit the next module number.
        '''
        for i, key in enumerate(d.keys()):
            try: 
                key = int(key)
                if key < 20: # Not a pointless if statement
                    last_key = key
            except ValueError:
                try:
                    key = float(key)
                    if key < 20: # Not a pointless if statement
                        last_key = key
                except:
                    pass
            # addying the dictionarys to the module organized dictionary.
            chapter_sorted_json[str(last_key)].update({str(key):[]})
            chapter_sorted_json[str(last_key)][str(key)].append(d[str(key)][0])
            chapter_sorted_json[str(last_key)][str(key)].append(d[str(key)][1])
            
        # We show the user how many modules there are, and how many topics each one has. and were wating for user input.
        clear()
        table = PrettyTable()
        table.field_names = ['Module Index', 'Module', '# of topics']
        for i, module in enumerate(list(chapter_sorted_json.keys())):
            table.add_row([i+1,module,len(chapter_sorted_json[module])])
        print(table)
        module_select = str(input(f"Studying: {t.replace('.json','')}\nPlease type the modules index you want to study.\nType 'all' for all.\nType '1,2,3' for module's 1 through 3.\n\nInput: "))
        
        # If we select 'all', we want to generate the list of index for all of those indexes.
        if 'a' in module_select.lower():
            module_select = list(range(1,len(list(chapter_sorted_json.keys()))+1))
            module_select = ','.join(str(x) for x in module_select)
        # If we want to go through modules 2-6, its not fun to type, 2,3,4,5,6. So this option is great
        # It basically generatess the string 2,3,4,5,6 for later processing because thats what its based on
        elif '-' in module_select:
            starting_module = int(module_select.split('-')[0])
            ending_module = int(module_select.split('-')[-1])
            module_select = str(starting_module)
            for i in range((ending_module-1)-starting_module):
                module_select += f",{i+starting_module+1}"
            module_select += ',' + str(ending_module)
        '''
        So what were doing here is were creating a temporary dictionary to ONLY add
        the selected module indexes that were inputed. By default ALL modules are selected.
        
        If you only want module 2 and 6, we add those to this temporary dictionary and head onward.
        '''
        module_select = module_select.split(',')
        temp_module_select = {}
        for i, module_index in enumerate(module_select):
            for key in list(chapter_sorted_json.keys()):
                try:
                    if list(chapter_sorted_json.keys())[int(module_index)-1] == str(key):
                        temp_module_select.update({key:[]})
                        temp_module_select[key] = chapter_sorted_json[key]
                except IndexError:
                    pass
        # Recompile back to standard simplified format using only the selected modules.
        chapter_sorted_json = temp_module_select
        final_compiled_json = {}

        '''
        This is mess
        
        I'm not sure if there is a better way to do this, but what were doing is, re-parsing
        the json file back to its orginal form.
        
        What this means is, we just want ALL the topics, and there information, we dont want
        the module, and what topics it includes.
        
        Essentially were just taking everything from each module and compiling it into one whole.
        
        for example. If we have module 1 and 2. Module 1 and 2 have different topics, we just merge
        everything from module 1 and 2, into one whole dictionary with no module index or chapters.
        
        So its basiclly just like it was in the orignal json format, except with less topics.
        '''
        total_topics: int = 0
        for i, key in enumerate(list(chapter_sorted_json.keys())):
            for topic in chapter_sorted_json[key]:
                total_topics += 1
                final_compiled_json.update({topic:[{'dictionary':[]},{'paths':[]}]})
                try:
                    description = (chapter_sorted_json[key][topic][0]['dictionary'][0])
                except IndexError:
                    description = []
                try:
                    path = chapter_sorted_json[key][topic][1]['paths'][0]
                except IndexError:
                    path = []
                final_compiled_json[topic][0]['dictionary'].append(description)
                final_compiled_json[topic][1]['paths'].append(path)
        studying_modules: list(str) = list(chapter_sorted_json.keys())
        if len(studying_modules) == 1:
            studying_modules = studying_modules[0]
        else:
            studying_modules = ', '.join(studying_modules)
        minutes_to_complete = int(total_topics/(0.0751*60))
        seconds_to_complete = int(((total_topics/(0.0751*60)) - minutes_to_complete)*100)
        yes_or_no = input(f"Studying: {t.replace('.json','')}\nModule(s): {studying_modules}\nTotal topics: {total_topics}\nApproximately will take: {minutes_to_complete} minutes and {seconds_to_complete} seconds to compelte.\nWould you like to work from definitions to find the keyword?\nyes or no?)")
    # This is because sometimes the study material doesnt have modules.
    except IndexError:
        # Set it back to the original json file.
        final_compiled_json = d
        yes_or_no = input(f"Studying: {t.replace('.json','')}\nWould you like to work from definitions to find the keyword?\nyes or no?)")
    if 'y' in yes_or_no.lower():
        WORK_FROM_DEFINATION = True
    elif 'n' in yes_or_no.lower():
        WORK_FROM_DEFINATION = False
        isTimed = False
    elif 'exit' in yes_or_no.lower():
        sys.exit()
    # I have decided that this will be a default setting.
    # if WORK_FROM_DEFINATION:
    #     isTimed = input(f"\nDo you want to be timed?\nyes or no?")
    #     if 'y' in isTimed.lower():
    #         isTimed = True
    #         print('\nYou will have 30 seconds to complete each topic.\n')
    #     elif 'n' in isTimed.lower():
    #         isTimed = False
    #     elif 'exit' in isTimed.lower():
    #         sys.exit()
    show_topics = input(f"\nDo you want to see the list of all the topics?\nyes or no?")
    if 'y' in show_topics.lower():
        show_topics = True
    elif 'n' in show_topics.lower():
        show_topics = False
    elif 'exit' in show_topics.lower():
        sys.exit()
    show_multiple_choices = input(f"\nDo you want to be shown multiple choices?\nyes or no?")
    if 'y' in show_multiple_choices.lower():
        show_multiple_choices = True
    elif 'n' in show_multiple_choices.lower():
        show_multiple_choices = False
    elif 'exit' in show_multiple_choices.lower():
        sys.exit()
    print(f'\n\nLoading {t}')
    START_STUDYING_TIME = datetime.now()
    main(final_compiled_json, True, show_topics, show_multiple_choices)
start_up()