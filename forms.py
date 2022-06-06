"""
    File name: forms.py
    Author: David Lorenc (xloren16)
    Date created: 18/11/2021
    Date last modified: 5/12/2021
    Python Version: 3.9
"""

from PyQt5.QtGui import QIntValidator, QValidator
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QFormLayout, QMessageBox, QComboBox, QTimeEdit, QGroupBox, QRadioButton
from PyQt5.QtCore import QObject, QTime, pyqtSignal

class myTimeEdit(QTimeEdit):
    errorValue = pyqtSignal(int)
    def validate(self,input,pos):
        ret,input,pos = super().validate(input,pos)
        self.errorValue.emit(ret)
        return ret,input,pos


class myIntValidator(QIntValidator,QObject):
    """
    Description:
        Check input text in QLineEdit, aceppt only numbers.
    """
    errorValue = pyqtSignal(int)
    def validate(self,input,pos):
        ret,input,pos = super().validate(input,pos)
        self.errorValue.emit(ret)
        return ret,input,pos
        
class editForm(QDialog):
    """
    Description:
        Set layout for edit form.
    """
    def __init__(self, parent = None, action = None, Name = None, Time = 0):
        super(editForm, self).__init__(parent)
        # Create widgets
        self.setMaximumSize(100, 100)

        layout = QFormLayout()
        self.l1 = QLabel("Enter name")
        layout.addRow(self.l1)
        self.new_name = QLineEdit()
        layout.addRow(self.new_name)
        self.l2 = QLabel("Enter estimated time")
        layout.addRow(self.l2)
        self.estimated = QLineEdit()
        self.validator = myIntValidator()
        self.validator.errorValue.connect(self.setError)
        self.estimated.setValidator(self.validator)
        layout.addRow(self.estimated)
        self.errorLabel = QLabel("")
        self.errorLabel.setStyleSheet("color: red;")
        layout.addRow(self.errorLabel)
        secondLayout = QFormLayout()
        secondLayout.setContentsMargins(30, 0, 30, 0)
        self.btn1 = QPushButton("Submit")
        self.btn1.resize(100, 30)
        self.btn1.clicked.connect(self.checkOutputData)
        secondLayout.addRow(self.btn1)
        layout.addRow(secondLayout)

        layout.setContentsMargins(30, 20, 30, 20)
        self.setLayout(layout)
        self.setWindowTitle(f"{action}")

        if action == "Add Project" or action == "Add Task":
            self.new_name.setPlaceholderText("Name")
            self.estimated.setPlaceholderText("Time")
        elif action == "Edit Project" or action == "Edit Task":
            self.new_name.setText(Name)
            self.estimated.setText(str(Time)[0:-1])

    def setError(self,retval):
        """
        Description:
            Show error based on myIntValidator.
        """
        if retval != QValidator.Acceptable:
            self.errorLabel.setText("Valid are only numbers")
        else:
            self.errorLabel.setText("")

    def checkOutputData(self):
        """
        Description:
            Check output from this form.
        """
        if self.new_name.text():
            if not self.estimated.text():
                self.estimated.setText("0")
            self.accept()
        else:
            qe = QMessageBox()
            qe.setIcon(QMessageBox.Critical)
            qe.setWindowTitle("Error")
            qe.setText("Enter name")
            qe.exec()
            
class addForm(QDialog):
    """
        Description:
            Set layout for add form.
    """
    def __init__(self, parent = None, tasks = None):
        super(addForm, self).__init__(parent)
        # Create widgets
        self.setMaximumSize(100, 100)

        layout = QFormLayout()
        self.l1 = QLabel("Select task")
        layout.addRow(self.l1)
        self.cb = QComboBox()
        for task in tasks:
            if task.parent_id:
                self.cb.addItem(f"  {task.name}")
            else:
                self.cb.addItem(task.name)
        layout.addRow(self.cb)
        
        self.l2 = QLabel("Enter start time")
        layout.addRow(self.l2)
        self.teStart = myTimeEdit()
        self.teStart.setDisplayFormat('hh:mm')
        self.teStart.setTime(QTime.fromString('08:00'))
        layout.addRow(self.teStart)
        self.errorLabel1 = QLabel("")
        self.errorLabel1.setStyleSheet("color: red;")
        layout.addRow(self.errorLabel1)
        
        self.l3 = QLabel("Enter end time")
        layout.addRow(self.l3)
        self.teEnd = myTimeEdit()
        self.teEnd.setDisplayFormat('hh:mm')
        self.teEnd.setTime(QTime.fromString('16:00'))
        layout.addRow(self.teEnd)
        self.errorLabel2 = QLabel("")
        self.errorLabel2.setStyleSheet("color: red;")
        layout.addRow(self.errorLabel2)
        
        secondLayout = QFormLayout()
        secondLayout.setContentsMargins(30, 0, 30, 0)
        self.btn1 = QPushButton("Insert")
        self.btn1.resize(100, 30)
        self.btn1.clicked.connect(self.checkOutput)
        secondLayout.addRow(self.btn1)
        layout.addRow(secondLayout)
        self.errorLabel3 = QLabel("")
        self.errorLabel3.setStyleSheet("color: red;")
        layout.addRow(self.errorLabel3)
        layout.setContentsMargins(30, 20, 30, 20)
        self.setLayout(layout)
        self.setWindowTitle("Add activity")
        self.teStart.errorValue.connect(self.setErrorStart)
        self.teEnd.errorValue.connect(self.setErrorEnd)
        
    def checkOutput(self):
        """
        Description:
            It check if start is lower as end. 
        """
        hStart, mStart = self.teStart.text().split(":")
        hEnd, mEnd = self.teEnd.text().split(":")
        if hStart >= hEnd:
            if mStart >= mEnd:
                self.errorLabel3.setText("Invalid start and end time")
                return
        self.accept()

    def setErrorStart(self,retval):
        """
        Description:
            Show error based on QTimeEdit.Validator.
        """
        if retval != QValidator.Acceptable:
            self.errorLabel1.setText("Invalid input")
        else:
            self.errorLabel1.setText("")
    
    def setErrorEnd(self,retval):
        """
        Description:
            Show error based on QTimeEdit.Validator.
        """
        if retval != QValidator.Acceptable:
            self.errorLabel2.setText("Invalid input")
        else:
            self.errorLabel2.setText("")