import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import random
import json
from functools import partial
from PyQt5.QtGui import QImage, QPixmap
import cv2
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import breeze_resources


PATH_TO_THIS_FOLDER: str = 'C:/Users/jared/Documents/Code/flashcard_generator'
UNCHANGED_STUDYING_TOPICS: list[str] = []

class TimerMessageBox(QMessageBox):
    def __init__(self, message: str, color:str, timeout: int = 3, parent=None):
        super(TimerMessageBox, self).__init__(parent)
        self.setWindowTitle("Feedback message")
        self.setWindowIcon(QIcon('icon.png'))
        self.time_to_wait = timeout
        self.message = message
        self.color = color
        self.setStyleSheet("QLabel{ color: " + self.color + "}");
        self.setText(f"{self.message}\n\nclosing in {timeout} seconds.")
        # self.setStandardButtons(QMessageBox.NoButton)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.changeContent)
        self.timer.start()

    def changeContent(self):
        self.time_to_wait -= 1
        self.setText(f"{self.message}\n\nclosing in {self.time_to_wait} seconds.")
        if self.time_to_wait <= 0:
            self.close()

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)
        self.stackedWidget.setCurrentIndex(1)
        self.setWindowTitle('Flashcards')
        self.setStyleSheet(open("style.qss", "r").read())
        self.setWindowIcon(QIcon('icon.png'))
        
        # Studying variables
        self.current_index: int = 0
        self.completed_topics: int = 0
        self.correct_topics: int = 0
        self.selected_topic: str = ''
        self.wrong_guesses: list[str] = []
        self.slow_guesses: list[str] = []
        self.NUMBER_OF_MULTIPLE_CHOICES: int = 5
        
        self.screen = app.primaryScreen()


        self.checkBoxModules = []
        self.module_names: list[str] = []
        self.chapter_sorted_json = {}
        self.final_compiled_json = {}
        self.answer_and_possible_answers: list[str] = []
        self.formatted_time: str = '0 minutes 0 seconds'
        self.refresh_subjects()

        self.setMinimumSize(1400,1000)

        self.checkBoxMultipleChoice.clicked.connect(self.toggle_multiple_choice_clicked)
        self.action_Quit.triggered.connect(self.close)
        self.actionRemove.triggered.connect(self.delete_flashcards)
        self.actionGenerate.triggered.connect(self.generate_flashcards)
        self.menuStudying.triggered.connect(self.reset_game)
        self.subjects.currentTextChanged.connect(self.on_combobox_changed)
        
        self.topicList.itemClicked.connect(lambda it, rowId=777 : self.listWidgetClicked(it, 777))
        self.listOfTopics.itemClicked.connect(lambda it, rowId=100 : self.listWidgetClicked(it, 100))
        self.btnStart.clicked.connect(self.start_studying)
        self.btnStart.setFixedWidth(200)
        self.btnStart.setFixedHeight(80)
        
        self.btnSubmit.clicked.connect(self.submit_button_clicked)
        self.btnSubmit.setFixedWidth(200)
        self.btnSubmit.setFixedHeight(80)
        
        self.showMaximized()
        self.show()

    def refresh_subjects(self):
        self.json_file_location = PATH_TO_THIS_FOLDER + '/flashcards/JSON_DATA/'
        all_file_names = os.listdir(self.json_file_location)
        all_file_names = [file.replace('.json', '') for file in all_file_names]
        

        self.subjects.clear()
        self.subjects.addItems(all_file_names)
        try:
            self.on_combobox_changed(all_file_names[0])
        except IndexError: # No study material
            # self.refresh_topics_list()
            self.topicList.clear()
            self.btnStart.setEnabled(False)
            return
        
        
    
    def reset_game(self):
        self.current_index: int = 0
        self.completed_topics: int = 0
        self.correct_topics: int = 0
        self.selected_topic: str = ''
        self.wrong_guesses.clear()
        self.slow_guesses.clear()
        self.stackedWidget.setCurrentIndex(1)
        self.refresh_topics_list()
        self.btnStart.setEnabled(False)
    
    def generate_flashcards(self):
        home_dir = str(Path.home())
        file_name = QFileDialog.getOpenFileName(self, 'Open file', home_dir)[0]

        if file_name:
            with open(file_name) as f:
                print(f)

    def delete_flashcards(self):
        all_file_names = os.listdir(self.json_file_location)
        all_file_names = [file.replace('.json', '') for file in all_file_names]
        item, okPressed = QInputDialog.getItem(self, "Which flashcards do you want to delete?","Flashcards:", all_file_names, 0, False)
        if okPressed and item:
            try:
                os.remove(self.json_file_location + f'{item}.json')
                shutil.rmtree(PATH_TO_THIS_FOLDER + f'/flashcards/{item}.pdf_dir')
            except Exception as e:
                error_dialog = QErrorMessage()
                error_dialog.setWindowTitle('Error Message')
                error_dialog.showMessage(e)
                error_dialog.exec_()
        self.refresh_subjects()

    def on_combobox_changed(self, value):
        try:
            with open(self.json_file_location + value + '.json') as f:
                d = json.load(f) 
        except FileNotFoundError:
            return
        self.clearLayout(self.modulesList)
        self.chapter_sorted_json.clear()
        try:
            for key in d.keys():
                try: 
                    key = int(key)
                except:
                    try:
                        key = float(key)
                    except:
                        continue
                if key > 20:
                    continue
                self.chapter_sorted_json.update({str(key):{}})
            last_key = list(self.chapter_sorted_json.keys())[0]
            
            for i, key in enumerate(d.keys()):
                try: 
                    key = int(key)
                    if key < 20: # Not a pointless if statement
                        last_key = key
                except:
                    try:
                        key = float(key)
                        if key < 20: # Not a pointless if statement
                            last_key = key
                    except:
                        pass
                # addying the dictionarys to the module organized dictionary.
                if key == 50: # No idea why, but just something ya gotta do. 
                    continue
                self.chapter_sorted_json[str(last_key)].update({str(key):[]})
                self.chapter_sorted_json[str(last_key)][str(key)].append(d[str(key)][0])
                self.chapter_sorted_json[str(last_key)][str(key)].append(d[str(key)][1])
            self.update_modules_list(self.chapter_sorted_json)
            self.refresh_topics_list()
        except Exception as e: #No idea
            error_dialog = QErrorMessage()
            error_dialog.setWindowTitle('Error Message')
            error_dialog.showMessage(e)
            error_dialog.exec_()
            self.update_modules_list([])
            self.chapter_sorted_json = d
            self.refresh_topics_list()
        # do your code
    
    def update_modules_list(self, l):
        self.checkBoxModules.clear()
        self.module_names.clear()
        try:
            self.topicList.clear()
            self.clearLayout(self.modulesList)
            modules = list(l.keys())
            self.toggle_all = QPushButton('Toggle all modules')
            self.toggle_all.setFixedWidth(200)
            self.toggle_all.setFixedHeight(80)
            self.toggle_all.setCheckable(True)
            self.toggle_all.clicked.connect(self.toggle_all_checkboxes)
            # self.modulesList.addWidget(self.toggle_all)
            for module_index, module in enumerate(modules, start=1):
                checkBox = QCheckBox(str(f'{module_index} - {module}'))
                checkBox.clicked.connect(self.refresh_topics_list)
                self.checkBoxModules.append(checkBox)
                # self.modulesList.addWidget(checkBox)
                self.modulesList.addWidget(checkBox, module_index, 0, alignment=Qt.AlignLeft)
                self.module_names.append(module)
            self.modulesList.addWidget(self.toggle_all, module_index+1, 0, alignment=Qt.AlignCenter)
            self.label_4.setText(f'({len(modules)}) Modules:')
            self.topicList.setRowMininumHeight(100)
        except:
            pass
    @pyqtSlot()
    def refresh_topics_list(self):
        self.topicList.clear()
        try:
            self.module_select = [
                checkbox.text().split(' - ')[0]
                for checkbox in self.checkBoxModules
                if checkbox.isChecked()
            ]
            if not self.module_select:
                if not self.checkBoxModules:
                    self.final_compiled_json = self.chapter_sorted_json
                    self.all_studying_topics = [list(self.chapter_sorted_json.keys())][0]
                    self.btnStart.setEnabled(True)
                else:
                    self.final_compiled_json = []
                    self.all_studying_topics = []
                    self.btnStart.setEnabled(False)
                self.label_3.setText(f'({len(self.all_studying_topics)}) Topics:')
                self.topicList.addItems(self.all_studying_topics)
                return
            self.btnStart.setEnabled(True)

            temp_module_select = {}
            for i, module_index in enumerate(self.module_select):
                for key in list(self.chapter_sorted_json.keys()):
                    try:
                        if list(self.chapter_sorted_json.keys())[int(module_index)-1] == str(key):
                            temp_module_select[key] = []
                            temp_module_select[key] = self.chapter_sorted_json[key]
                    except Exception as e:
                        error_dialog = QErrorMessage()
                        error_dialog.setWindowTitle('Error Message')
                        error_dialog.showMessage(e)
                        error_dialog.exec_()
            # Recompile back to standard simplified format using only the selected modules.
            chapter_sorted_json = temp_module_select
            final_compiled_json = {}
            total_topics: int = 0
            for i, key in enumerate(list(chapter_sorted_json.keys())):
                for topic in chapter_sorted_json[key]:
                    total_topics += 1
                    final_compiled_json[topic] = [{'dictionary':[]},{'paths':[]}]
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
            self.final_compiled_json = final_compiled_json
            self.all_studying_topics = list(final_compiled_json.keys())
            self.label_3.setText(f'({len(self.all_studying_topics)}) Topics:')
            self.topicList.addItems(self.all_studying_topics)
        except IndexError:
            self.all_studying_topics = list(self.chapter_sorted_json.keys())
            self.label_3.setText(f'({len(self.all_studying_topics)}) Topics:')
            self.topicList.addItems(self.all_studying_topics)  
    @pyqtSlot() 
    def listWidgetClicked(self, item, rowId: int):
        if rowId == 100:
            self.txtInput.setText(item.text()) 
    @pyqtSlot()
    def toggle_all_checkboxes(self):
        for checkbox in self.checkBoxModules:
            checkbox.setChecked(self.toggle_all.isChecked())
        self.refresh_topics_list()
    @pyqtSlot()
    def toggle_multiple_choice_clicked(self):
        self.checkBoxShowListOfWords.setEnabled(not self.checkBoxMultipleChoice.isChecked())
        self.checkBoxShowListOfWords.setChecked(False) 
    
    def start_timer(self):
        self.curr_time = QTime(00,00,00)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)
    
    def update_timer(self):    
        self.curr_time = self.curr_time.addSecs(1)
        # self.upTime.setTime(self.curr_time)
        
        if self.curr_time.minute() > 1 and self.curr_time.second() > 1:
            self.formatted_time = f'{self.curr_time.minute()} minutes {self.curr_time.second()} seconds'
        elif self.curr_time.minute() == 1 and self.curr_time.second() == 1:
            self.formatted_time = f'{self.curr_time.minute()} minute {self.curr_time.second()} second'
        elif self.curr_time.minute() == 1 and self.curr_time.second() > 1:
            self.formatted_time = f'{self.curr_time.minute()} minute {self.curr_time.second()} seconds'
        elif self.curr_time.minute() > 1 and self.curr_time.second() == 1:
            self.formatted_time = f'{self.curr_time.minute()} minutes {self.curr_time.second()} second'
        elif self.curr_time.minute() < 1 and self.curr_time.second() == 1:
            self.formatted_time = f'{self.curr_time.second()} second'
        elif self.curr_time.minute() < 1 and self.curr_time.second() > 1:
            self.formatted_time = f'{self.curr_time.second()} seconds'
        self.update_stats()

    def update_stats(self):
        modules_indexes = self.module_select
        modules = ''.join(', ' + self.module_names[int(module_index)-1] for module_index in modules_indexes)[2:]
        
        try:
            if modules == '':
                self.lblStats.setText(f'Studying: {self.subjects.currentText()}    Topics: {self.TOTAL_NUMBER_OF_TOPICS}    Score: {(self.correct_topics)}/{(self.completed_topics)} - {round(((self.correct_topics)/(self.completed_topics)*100),2)}%    Time: {self.formatted_time}')
            else:
                self.lblStats.setText(f'Studying: {self.subjects.currentText()}    Modules: {modules}    Topics: {self.TOTAL_NUMBER_OF_TOPICS}    Score: {(self.correct_topics)}/{(self.completed_topics)} - {round(((self.correct_topics)/(self.completed_topics)*100),2)}%    Time: {self.formatted_time}')
        except ZeroDivisionError:
            if modules == '':
                self.lblStats.setText(f'Studying: {self.subjects.currentText()}    Topics: {self.TOTAL_NUMBER_OF_TOPICS}    Score: 0/0 - 0%    Time: {self.formatted_time}')
            else:
                self.lblStats.setText(f'Studying: {self.subjects.currentText()}    Modules: {modules}    Topics: {self.TOTAL_NUMBER_OF_TOPICS}    Score: 0/0 - 0%    Time: {self.formatted_time}')

    def stop_timer(self):
        self.timer.stop()
        self.timer.deleteLater()
    
    def start_studying(self):
        global UNCHANGED_STUDYING_TOPICS
        UNCHANGED_STUDYING_TOPICS = self.all_studying_topics
        self.START_TIME = datetime.now()
        self.stackedWidget.setCurrentIndex(0)
        self.TOTAL_NUMBER_OF_TOPICS: int = len(self.all_studying_topics)
        self.listOfTopics.clear()
        self.listOfTopics.setVisible(self.checkBoxShowListOfWords.isChecked())
        if self.checkBoxShowListOfWords.isChecked():
            self.listOfTopics.addItems(self.all_studying_topics)
        self.update_stats()

        self.start_timer()
        self.select_next_topic()
        self.number_of_topics: int = len(self.all_studying_topics)
    
    def select_next_topic(self):
        self.START_TOPIC_TIME = datetime.now()
        self.update_stats()
        
        topics_left = self.all_studying_topics
        random.shuffle(topics_left)
        try:
            self.selected_topic = topics_left[0]
        except IndexError:
            self.show_results()
            return
        self.show_images(self.selected_topic)
        if self.checkBoxMultipleChoice.isChecked():
            self.answer_and_possible_answers = self.find_similar_topics(topic=self.selected_topic)
            self.add_buttons_to_grid(self.answer_and_possible_answers)
    
    def show_images(self, topic: str):
        path_to_notes = self.final_compiled_json[topic][1]['paths']
        startCol = int(0) # Deal with it!
        
        for index, path in enumerate(path_to_notes):
            try:
                img = cv2.imread(path)
            except TypeError:
                self.check_answer(self.selected_topic, True)
                break
            
            height, width = img.shape[0:2]
            startRow = int(350 if index == 0 else 0)
            endRow = int(height)
            endCol = int(width) # We go to the width of the document because titles could be long.
            croppedImage = img[startRow:endRow, startCol:endCol] # We crop the image accordingly to the values above.

            rgbImage = cv2.cvtColor(croppedImage, cv2.COLOR_BGR2RGB)
            h, w, ch = rgbImage.shape
            bytesPerLine = ch * w
            convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
            p = convertToQtFormat.scaled(int(self.scrollArea.width()), int(self.scrollArea.height()), Qt.KeepAspectRatio)
            self.lblNotes1.clear()
            self.lblNotes2.clear()
            self.lblNotes3.clear()
            self.lblNotes4.clear()
            if index == 0:
                self.lblNotes1.setPixmap(QPixmap.fromImage(p))
            elif index == 1:
                self.lblNotes2.setPixmap(QPixmap.fromImage(p))
            elif index == 2:
                self.lblNotes3.setPixmap(QPixmap.fromImage(p))
            else:
                self.lblNotes4.setPixmap(QPixmap.fromImage(p))
    
    def feedback_message(self, message: str, color: str):
        messagebox = TimerMessageBox(message=message, color=color, timeout=3, parent=self)
        messagebox.exec_()

    def show_results(self):
        self.stop_timer()
        modules_indexes = self.module_select
        modules = ''.join(
            ', ' + self.module_names[int(module_index)-1]
            for module_index in modules_indexes
        )[2:]
        slow_guesses_text: str = ''
        wrong_guesses_text: str = ''
        temp_text: str = ''
        if len(self.slow_guesses) > 0:
            for i, guesses in enumerate(self.slow_guesses, start=1):
                temp_text += f'\n{i}. {guesses},'
            slow_guesses_text = f'Topics that were correct, but took longer than 30 seconds: {temp_text}\n'
        if len(self.wrong_guesses) > 0:
            for i, guesses in enumerate(self.wrong_guesses, start=1):
                temp_text += f'\n{i}. {guesses},'
            wrong_guesses_text = f'Topics that were guessed incorrectly: {temp_text}\n'
        text = f"""Studied: {self.subjects.currentText()}
Modules: {modules}
Topics: {self.TOTAL_NUMBER_OF_TOPICS}
Time: {self.formatted_time}
Score: {(self.correct_topics)}/{(self.completed_topics)} - {round(((self.correct_topics+1)/(self.completed_topics+1)*100),2)}%

{slow_guesses_text}{wrong_guesses_text}
"""

        messageBox = QMessageBox(self)
        # messageBox.setWindowIcon(QIcon("Ok.png"))
        messageBox.setIcon(QMessageBox.Information)
        messageBox.setWindowTitle(f"Studied: {self.subjects.currentText()}")
        messageBox.setInformativeText(text)

        btnOk = messageBox.addButton("Ok", QMessageBox.YesRole)
        messageBox.setDefaultButton(btnOk)

        messageBox.exec_()
        
        self.reset_game()
        
    
    def add_buttons_to_grid(self, topics: list[str]):
        self.clearLayout(self.selectionGridLayout)
        cols: int = 2
        rows: int = 1
        number_of_items: int = 0
        for index, topic in enumerate(topics, start=1):
            row = int(number_of_items / cols)
            col = number_of_items & rows
            button = QPushButton(f'{index}. {topic}')
            button.clicked.connect(partial(self.check_answer, topic))
            # button.btnSubmit.setFixedWidth(200)
            button.setFixedHeight(80)
            self.selectionGridLayout.addWidget(button, row, col)
            number_of_items += 1
    @pyqtSlot()
    def submit_button_clicked(self):
        self.check_answer(topic=self.txtInput.text())
         
    def check_answer(self, topic: str, skip_dialog: bool = False):
        topic = topic.replace(' ', '')
        selected_topic = self.selected_topic.replace(' ', '')
        elapsed = datetime.now() - self.START_TOPIC_TIME
        self.completed_topics += 1
        if self.compare_words(topic.lower(), selected_topic.lower()) <= (len(selected_topic)/4):
            if self.checkBoxTimed.isChecked() and elapsed > timedelta(seconds=30):
                self.all_studying_topics.pop(0)
                self.slow_guesses.append(self.selected_topic)
                self.feedback_message(message="That is correct, but not completed within 30 seconds!", color='blue')
            else:
                self.all_studying_topics.pop(0)
                self.correct_topics += 1
                if not skip_dialog:
                    self.feedback_message(message="That is correct!", color='green')
        else:
            self.feedback_message(message=f"That is incorrect!\n\nThe answer was: {self.selected_topic}", color='red')
            self.wrong_guesses.append(self.selected_topic)
            self.all_studying_topics.pop(0)
        self.txtInput.setText('')
        self.select_next_topic()

    def find_similar_topics(self, topic: str) -> list[str]:
        global UNCHANGED_STUDYING_TOPICS
        similarity_score = {
            t: int(self.compare_words(topic, t))
            for t in UNCHANGED_STUDYING_TOPICS
            if t != topic
        }

        # Sort from highest to lowest score
        similarity_score = dict(sorted(similarity_score.items(), key=lambda item: item[1]))
        # We just want the topics, the scores are now useless.
        words_sorted_by_similarity = list(similarity_score.keys())
        # we take the first N amount of possible options or topics.
        options = words_sorted_by_similarity[:self.NUMBER_OF_MULTIPLE_CHOICES]
        options.append(topic)
        random.shuffle(options)
        return options
    
    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())
                    
    def compare_words(self, u1: str, u2: str):
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
            return self.compare_words(u2, u1)
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
    def keyPressEvent(self, event):
        if self.stackedWidget.currentIndex() == 0: # If we have actually started studying
            if self.checkBoxMultipleChoice.isChecked():
                if event.key() == Qt.Key_1:
                    self.check_answer(self.answer_and_possible_answers[0])
                elif event.key() == Qt.Key_2:
                    self.check_answer(self.answer_and_possible_answers[1])
                elif event.key() == Qt.Key_3:
                    self.check_answer(self.answer_and_possible_answers[2])
                elif event.key() == Qt.Key_4:
                    self.check_answer(self.answer_and_possible_answers[3])
                elif event.key() == Qt.Key_5:
                    self.check_answer(self.answer_and_possible_answers[4])
                elif event.key() == Qt.Key_6:
                    self.check_answer(self.answer_and_possible_answers[5])
            if event.key() == 16777220:
                self.check_answer(self.txtInput.text())
        event.accept()

    def resizeEvent(self, event):
        self.listOfTopics.setFixedHeight(self.height()-325)
        QMainWindow.resizeEvent(self, event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Window()
    app.exec_()