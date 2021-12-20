import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import *
import os
import yaml
import shutil
from random import shuffle
from functools import partial
import string
import qdarktheme # pip install pyqtdarktheme
import zipfile
import time
import subprocess
import platform

class TimerMessageBox(QMessageBox):
    def __init__(self, message: str, color:str, timeout: int = 15, parent=None):
        super(TimerMessageBox, self).__init__(parent)
        self.setWindowIcon(QIcon('icon1.png'))
        self.setWindowTitle("Feedback message")
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

class App(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.setStyleSheet(qdarktheme.load_stylesheet())

    def initUI(self):
        self.setWindowTitle("Quest___")
        self.setWindowIcon(QIcon('icon1.png'))
        
        # STUDYING MENU
        self.lblQuestion = QLabel('Test: ', self)
        
        self.grid = QGridLayout()
        self.questions = []
        self.answer = ''

        self.btnSubmit = QPushButton(self)
        self.btnSubmit.clicked.connect(self.checkGuess)     
        pixmapi = getattr(QStyle, 'SP_DialogOkButton')
        icon = self.style().standardIcon(pixmapi)
        self.btnSubmit.setIcon(icon)
        self.btnSubmit.setFixedSize(60,60)
        
        self.txtInput = QTextEdit(self)
        # self.txtInput.setStyleSheet("font: 20pt")
        
        self.mainWidget = QWidget()
        self.mainLayout = QVBoxLayout()

        self.layout = QVBoxLayout() 
        self.layout.addWidget(self.lblQuestion)
        self.layout2 = QHBoxLayout()
        self.layout2.addWidget(self.txtInput)
        self.layout2.addWidget(self.btnSubmit)
        
        self.mainLayout.addLayout(self.layout)
        self.mainLayout.addLayout(self.layout2)
        self.mainLayout.addLayout(self.grid)

        self.mainWidget.setLayout(self.mainLayout)

        # SLECTION MENU
        
        self.layout4 = QVBoxLayout()
        self.courseToStudy = QComboBox(self)
        self.courseToStudy.currentTextChanged.connect(self.course_changed)
        
        self.btnStartStudying = QPushButton('Start', self)
        self.btnStartStudying.clicked.connect(self.start_studying)
        
        self.layout4.addWidget(self.courseToStudy)
        self.layout4.addWidget(self.btnStartStudying)
        self.mainLayout.addLayout(self.layout4)
        
        self.setCentralWidget(self.mainWidget)
        
        
        # File menu
        bar = self.menuBar()
        file_menu = bar.addMenu('File')
        import_file = QAction('Import Questions', self)
        import_file.triggered.connect(self.import_files)
        export_file = QAction('Export Questions', self)
        export_file.triggered.connect(self.export_files)
        file_menu.addAction(import_file)
        file_menu.addAction(export_file)
        question_menu = bar.addMenu('Edit')
        # adding actions to file menu
        create_questions = QAction('Edit Questions', self)
        create_questions.triggered.connect(self.create_questions_dialog)
        question_menu.addAction(create_questions)
        
        studying_menu = bar.addMenu('Studying')
        stop_studying = QAction('Stop', self)
        stop_studying.triggered.connect(partial(self.selection_menu, True))
        studying_menu.addAction(stop_studying)
        
        self.selection_menu(True)
        self.refresh_course_list()
        self.resize(1000,600)
    
    def import_files(self):
        fileName, _ = QFileDialog.getOpenFileName(self,"Import", "","Zip Files (*.zip)")
        if fileName:
            with zipfile.ZipFile(fileName, 'r') as zip_ref:
                zip_ref.extractall(os.getcwd())
        self.refresh_course_list()
        self.feedback_message(message='Finished!', color='green')
    
    def export_files(self):
        path = 'questions/'
        timestr = time.strftime("%Y%m%d-%H%M%S")
        zipf = zipfile.ZipFile(f'Questions_{timestr}.zip', 'w', zipfile.ZIP_DEFLATED)
        # ziph is zipfile handle
        for root, dirs, files in os.walk(path):
            for file in files:
                zipf.write(os.path.join(root, file), 
                        os.path.relpath(os.path.join(root, file), 
                                        os.path.join(path, '..')))
        zipf.close()
        self.explore(os.getcwd() + f'/Questions_{timestr}.zip')
    
    def explore(self, path):
        FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')
        # explorer would choke on forward slashes
        path = os.path.normpath(path)

        if os.path.isdir(path):
            subprocess.run([FILEBROWSER_PATH, path])
        elif os.path.isfile(path):
            subprocess.run([FILEBROWSER_PATH, '/select,', path])
            
    def studying_menu(self, enable: bool):
        self.lblQuestion.setText("")
        self.txtInput.setVisible(enable)
        self.btnStartStudying.setVisible(not enable)
        self.courseToStudy.setVisible(not enable)
        self.lblQuestion.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    def selection_menu(self, enable: bool):
        self.clearLayout(self.grid) 
        self.btnSubmit.setVisible(False)
        self.txtInput.setVisible(not enable)
        self.btnStartStudying.setVisible(enable)
        self.courseToStudy.setVisible(enable)
        self.lblQuestion.setText("Courses: ")
        self.lblQuestion.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

    def start_studying(self):
        self.studying_menu(True)
        self.txtInput.setPlainText('')
        f = 'questions/' + self.courseToStudy.currentText()
        with open(f, "r") as file:
            content = yaml.safe_load(file)
            self.questions = list(content.keys())
            shuffle(self.questions)
        self.next_question()

    def next_question(self):
        self.clearLayout(self.grid)
        f = 'questions/' + self.courseToStudy.currentText()
        with open(f, "r") as file:
            content = yaml.safe_load(file)
        try:
            question = self.questions[0]
        except IndexError:
            print('yeaa you win')
            self.selection_menu(True)
            return
        self.lblQuestion.setText(question)
        try:
            answers = content[question].split('; ')
        except AttributeError:
            answers = str(content[question])
            self.answer = answers
        question = question.lower()
        self.txtInput.setVisible(False)
        self.btnSubmit.setVisible(False)
        cols: int = 2
        rows: int = 1
        number_of_items: int = 0
        answers = [i for i in answers if i != '']
        print(answers)
        if answers in ['True', 'False', 'true', 'false', ['True'], ['False'], ['true'], ['false']]:
            self.answer = answers[0]
            shuffle(answers)
            for answer in ['True', 'False']:
                row = int(number_of_items / cols)
                col = number_of_items & rows
                btn = QPushButton(answer)
                btn.setFixedHeight(60)
                btn.clicked.connect(partial(self.checkGuess, answer))
                self.grid.addWidget(btn, row, col)
                number_of_items += 1
        elif (
            len(answers) >= 3
            and len(answers) != 1
            and 'multiple choice' in question
            or 'mc' in question
        ):
            self.answer = answers[0]
            shuffle(answers)
            for answer in answers:
                row = int(number_of_items / cols)
                col = number_of_items & rows
                btn = QPushButton(answer)
                btn.setFixedHeight(60)
                btn.clicked.connect(partial(self.checkGuess, answer))
                self.grid.addWidget(btn, row, col)
                number_of_items += 1
        else:
            self.answer = answers
            self.txtInput.setVisible(True)
            self.btnSubmit.setVisible(True)
            self.lblQuestion.setText(self.lblQuestion.text() + '\n\nSeperate answers with new lines.')
    
    def refresh_course_list(self):
        self.courseToStudy.clear()
        courses = [f for f in os.listdir('questions') if os.path.isfile(os.path.join('questions', f))]
        self.courseToStudy.addItems(courses)
        self.course_changed()
    
    def course_changed(self):
        try:
            courses = [f for f in os.listdir('questions') if os.path.isfile(os.path.join('questions', f))]
            f = 'questions/' + self.courseToStudy.currentText()
            if f == 'questions/':
                f = 'questions/' + courses[0]
            with open(f, "r") as file:
                content = yaml.safe_load(file)
                try:
                    self.setWindowTitle(f'{len(content)} - Quest___')
                except (AttributeError, TypeError):
                    pass
        except IndexError:
            pass
    @pyqtSlot()
    def checkGuess(self, guess: str = ''):
        translator = str.maketrans('', '', string.punctuation)
        if guess == '':
            guess = self.txtInput.toPlainText()
            guesses = guess.split('\n')
            guesses = [i for i in guesses if i != '']
            print(guesses)
            correct_guesses = []
            for g in guesses:
                for a in self.answer:
                    g = g.lower()
                    a = a.lower()
                    # remove puncutation
                    a = a.translate(translator)
                    g = g.translate(translator)
                    
                    if g == a:
                        correct_guesses.append(a)
            if len(correct_guesses) == len(self.answer) or len(correct_guesses) >= 3:
                self.feedback_message(message='That is correct!', color='green')
            else:
                ans = '\n'.join(self.answer)
                self.feedback_message(message='That is wrong! The correct answer is:\n' + ans, color='red')
            self.questions.pop(0)
            shuffle(self.questions)
            self.next_question()
            self.txtInput.setPlainText('')
            return
        guess = guess.lower()
        self.answer = self.answer.lower()
        if self.answer == guess:
            self.feedback_message(message='That is correct!', color='green')
        else:
            # ans = '\n'.join(self.answer)
            self.feedback_message(message='That is wrong! The correct answer is:\n' + self.answer, color='red')
        self.questions.pop(0)
        shuffle(self.questions)
        self.next_question()
        self.txtInput.setPlainText('')
    def create_questions_dialog(self):
        self.hide()
        cqDialog = EditQuestions(self, self)
        cqDialog.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.checkGuess(self.txtInput.toPlainText())
    
    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())
    
    def feedback_message(self, message: str, color: str):
        messagebox = TimerMessageBox(message=message, color=color, timeout=15, parent=self)
        messagebox.exec_()

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
class EditQuestions(QMainWindow):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.initUI()
        self.setWindowTitle('Edit Questions')
        self.setWindowIcon(QIcon('icon1.png'))
        self.app = app
        self.resize(1000,500)
    
    def closeEvent(self, event):
        self.app.refresh_course_list()
        self.app.show()

    def initUI(self):
        self.mainWidget = QWidget()
        
        self.mainLayout = QHBoxLayout()
        
        if not os.path.exists('questions'):
            os.makedirs('questions')
            
        self.questionsList = QListWidget(self)
        self.questionsList.itemClicked.connect(lambda it, rowId=100 : self.listWidgetClicked(it, 100))

        self.layout2 = QVBoxLayout()
        self.layout1 = QHBoxLayout()
        self.courseSelection = QComboBox(self)
        self.btnAddCourse = QPushButton(self)
        pixmapi = getattr(QStyle, 'SP_FileDialogNewFolder')
        icon = self.style().standardIcon(pixmapi)
        self.btnAddCourse.setIcon(icon)
        self.btnAddCourse.setFixedSize(32,32)
        self.btnAddCourse.clicked.connect(self.create_course)
        
        self.btnDeleteCourse = QPushButton(self)
        pixmapi = getattr(QStyle, 'SP_TrashIcon')
        icon = self.style().standardIcon(pixmapi)
        self.btnDeleteCourse.setIcon(icon)
        self.btnDeleteCourse.setFixedSize(32,32)
        self.btnDeleteCourse.clicked.connect(self.delete_course)

        self.layout1.addWidget(self.courseSelection)
        self.layout1.addWidget(self.btnAddCourse)
        self.layout1.addWidget(self.btnDeleteCourse)
        
        self.layout2.addLayout(self.layout1)
        
        l1 = QLabel('Question:', self)
        self.txtInputQuestion = QTextEdit(self)
        self.txtInputQuestion.textChanged.connect(self.verify_question_exists)
        l2 = QLabel('Answer:', self)
        self.txtInputAnswer = QTextEdit(self)
        self.txtInputAnswer.setToolTip('The answer should be written first, followed by other entries seperated by commas.')
        self.btnSubmit = QPushButton('Add', self)
        self.btnSubmit.clicked.connect(self.add_question)
        self.btnDeleteQuestion = QPushButton('Delete', self)
        self.btnDeleteQuestion.clicked.connect(self.delete_question)
        
        self.layout2.addWidget(l1)
        self.layout2.addWidget(self.txtInputQuestion)
        self.layout2.addWidget(l2)
        self.layout2.addWidget(self.txtInputAnswer)
        
        self.layout3 = QHBoxLayout()
        self.layout3.addWidget(self.btnSubmit)
        self.layout3.addWidget(self.btnDeleteQuestion)
        self.layout2.addLayout(self.layout3)
        
        # File menu
        bar = self.menuBar()
        question_menu = bar.addMenu('Help')
        # adding actions to file menu
        read_me_dialog = QAction('Read me', self)
        read_me_dialog.triggered.connect(self.show_help_dialog)
        question_menu.addAction(read_me_dialog)
        
        
        self.mainLayout.addLayout(self.layout2)
        self.mainLayout.addWidget(self.questionsList)
        
        self.mainWidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainWidget)
        
        self.courseSelection.currentTextChanged.connect(self.load_questions)
        self.refresh_course_list()
        self.load_questions()
        self.verify_question_exists()
        
    def show_help_dialog(self):
        info: str = '''Multiple Choice questions (MC):
    - The first entry should be the answer.
    - Each answer should be on new lines.
    - Answers will be saved with semicolons automatically.
    - Semicolons indicate seperate answers for multiple choice questions.
    
True/False Questions (T/F):
    - The answer should ONLY include True or False.
    
"Define", "give example", "what is" type questions:
    - These questions are NOT Multiple Choice questions, so the user 
    will be prompted a text box to get as close as possible as to getting 
    the asnwer correct.
    - These are very hard to determine if the user guessed the answer correctly, so try and make the answer as practical as possible.
        '''
        messageBox = QMessageBox(self)
        messageBox.setIcon(QMessageBox.Information)
        messageBox.setWindowTitle("Information")
        messageBox.setTextInteractionFlags(Qt.TextSelectableByMouse)
        messageBox.setInformativeText(info)
        btnOk = messageBox.addButton("Ok", QMessageBox.YesRole)
        messageBox.setDefaultButton(btnOk)
        messageBox.exec_()

    def create_course(self):
        text, okPressed = QInputDialog.getText(self, "Add Course", "Name of course:", QLineEdit.Normal, "")
        if okPressed and not os.path.exists('questions/' + text + '.yaml'):
            with open('questions/' + text + '.yaml', 'w+') as f:
                f.write('')
        self.refresh_course_list()
            
    def delete_course(self):
        # self.refresh_course_list()
        selection, okPressed = QInputDialog.getItem(self, "Delete Course", "Which courses would you want to delete?", self.courses, 0, False)
        if okPressed:
            os.remove('questions/' + selection) 
        self.refresh_course_list()
    
    def add_question(self):
        f = 'questions/' + self.courseSelection.currentText()
        with open(f, "r") as file:
            content = yaml.safe_load(file)
        if '(Multiple Choice)' not in self.txtInputQuestion.toPlainText() and 'MC' not in self.txtInputQuestion.toPlainText() and 'True' not in self.txtInputAnswer.toPlainText() and  'False' not in self.txtInputAnswer.toPlainText() and 'false' not in self.txtInputAnswer.toPlainText() and 'true' not in self.txtInputAnswer.toPlainText() and 'TF' not in self.txtInputQuestion.toPlainText() and 'T/F' not in self.txtInputQuestion.toPlainText():
            dialog = QMessageBox.question(self, "Multiple choice question",
                "Is this question supposed to be a multiple choice question?",
                buttons=QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                defaultButton=QMessageBox.Cancel)
            if dialog == QMessageBox.Yes:
                self.txtInputQuestion.setText(self.txtInputQuestion.toPlainText() + ' (Multiple Choice)')
            elif dialog == QMessageBox.Cancel:
                return
        try:
            content[self.txtInputQuestion.toPlainText()] = self.txtInputAnswer.toPlainText().replace('\n', '; ')
        except TypeError:
            content = {self.txtInputQuestion.toPlainText(): self.txtInputAnswer.toPlainText().replace('\n', '; ')}
        with open(f, 'w') as outfile:
            yaml.dump(content, outfile, default_flow_style=False)
        self.load_questions()
        
    def verify_question_exists(self):
        self.btnDeleteQuestion.setEnabled(False)
        self.btnSubmit.setText('Add')
        f = 'questions/' + self.courseSelection.currentText()
        if f == 'questions/':
            f = 'questions/' + self.courses[0]
        with open(f, "r") as file:
            content = yaml.safe_load(file)
            try:
                for key in content.keys():
                    if key == self.txtInputQuestion.toPlainText():
                        self.btnDeleteQuestion.setEnabled(True)
                        self.btnSubmit.setText('Replace')
            except AttributeError:
                pass
            
    def delete_question(self):
        f = 'questions/' + self.courseSelection.currentText()
        with open(f, "r") as file:
            content = yaml.safe_load(file)
        content.pop(self.txtInputQuestion.toPlainText(), None)
        with open(f, 'w') as outfile:
            yaml.dump(content, outfile, default_flow_style=False)
        self.load_questions()
        
    def load_questions(self):
        self.questionsList.clear()
        f = 'questions/' + self.courseSelection.currentText()
        if f == 'questions/':
            f = 'questions/' + self.courses[0]
        with open(f, "r") as file:
            content = yaml.safe_load(file)
            try:
                for key in content.keys():
                    self.questionsList.addItem(f'{key}: {content[key]}')
            except AttributeError:
                pass
        self.verify_question_exists()
    
    @pyqtSlot() 
    def listWidgetClicked(self, item, rowId: int):
        if rowId == 100:
            self.txtInputQuestion.setText(item.text().split(': ')[0]) 
            self.txtInputAnswer.setText(item.text().split(': ')[1].replace('; ', '\n')) 
            
    def refresh_course_list(self):
        self.courses = [f for f in os.listdir('questions') if os.path.isfile(os.path.join('questions', f))]
        self.btnDeleteCourse.setEnabled(len(self. courses) != 0)
        self.txtInputAnswer.setEnabled(len(self. courses) != 0)
        self.txtInputQuestion.setEnabled(len(self. courses) != 0)
        self.btnSubmit.setEnabled(len(self. courses) != 0)
        self.courseSelection.setEnabled(len(self. courses) != 0)

        self.courseSelection.clear()
        self.courseSelection.addItems(self.courses)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.add_question()
if __name__ == '__main__': 
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())