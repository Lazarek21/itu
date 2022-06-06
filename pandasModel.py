"""
    File name: pandasModel.py
    Author: Mikuláš Brázda (xbrazd21)
    Date created: 18/11/2021
    Date last modified: 5/12/2021
    Python Version: 3.9
"""

from PyQt5.QtCore import QAbstractTableModel, QObject, Qt
from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QValidator
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql.expression import true
import database as db
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import re
from forms import addForm

class pandasData():
    """
    PandasData class stores data from activities and convert them into 
    pandasDayModela and pandasMonthModel.
    """
    def __init__(self,date):    
        """
        Description:
            Constructor of pandasData object. 
        Args:
            date datetime: date for which should be pandasDayModel and pandasMonthModel generated
        """
        engine = create_engine('sqlite:///db\\data.db', echo=False)
        self.Session = sessionmaker(bind=engine)
        self.pandasDayModel = pandasDayModel()
        self.pandasMonthModel = pandasMonthModel()
        self.date = date
        self.loadData()
        self.pandasDayModel.dataChanged.connect(self.dayModeldataChanged)
        
    def loadData(self):
        """
        Description:
            loads data from database and stores them into models. 
        """
        project = []
        with self.Session() as session:
            query = str(session.query(db.Activity,db.Task).filter(db.Activity.end != None, db.Activity.task_id==db.Task.id).with_entities(db.Task.parent_id.label('project'),db.Task.name.label('task'), db.Activity.start.label('start'),db.Activity.end.label('end'),db.Activity.id,db.Task.id))
            self._data = pd.read_sql_query(query, 'sqlite:///db\\data.db',parse_dates={'start':'','end':'' })
            for idx,project_id in enumerate(self._data['project']):
                if np.isnan(project_id):
                    project.append(self._data['task'][idx])
                    self._data.at[idx,'task'] = '-'
                else:
                    project.append(session.query(db.Task).filter_by(id=project_id).first().name)
        self._data['project'] = pd.Series(project) 
        self._data['start'] = pd.to_datetime(self._data['start'].dt.strftime("%m/%d/%Y, %H:%M:%S"))
        self._data['end'] = pd.to_datetime(self._data['end'].dt.strftime("%m/%d/%Y, %H:%M:%S"))
        self._data.insert(len(self._data.columns)-2,'duration', self._data.end - self._data.start)
        self.fillModels()

    def fillModels(self):
        """
        Description:
            stores data into models. 
        """
        self.pandasDayModel._data = self._data.loc[self._data['start'].dt.day == self.date.day]
        self.pandasDayModel._data = self.pandasDayModel._data.loc[self.pandasDayModel._data['start'].dt.month == self.date.month]
        self.pandasDayModel._data = self.pandasDayModel._data.loc[self.pandasDayModel._data['start'].dt.year == self.date.year]
        self.pandasDayModel._data.index = np.arange(0,len(self.pandasDayModel._data))
        df_month = self._data.loc[self._data['start'].dt.month == self.date.month]
        df_month = df_month.loc[df_month['start'].dt.year == self.date.year]
        self.pandasMonthModel._data = df_month.groupby(pd.Grouper(freq='D', key='start')).agg({'duration': 'sum'}).reset_index()
        self.pandasMonthModel._data = self.pandasMonthModel._data.append(pd.DataFrame([["SUMMARY", self.pandasMonthModel._data['duration'].sum()]], columns=['start','duration']))
        self.pandasDayModel.layoutChanged.emit()
        self.pandasMonthModel.layoutChanged.emit()
    
    def dayModeldataChanged(self,index):
        """
        Description:
            is called when dataChanged signal in pandas day model is emitted. Updates
            database by user inserted data.
        Args:
            index (QModelIndex): index what column and row in table view were changed 
        """        
        activity_id = self.pandasDayModel._data['Activity_id'][index.row()]
        column = self.pandasDayModel._data.columns[index.column()]
        with self.Session() as session:
            activity = session.query(db.Activity).filter_by(id=int(activity_id)).first()
            if column == 'start':
                activity.start = self.pandasDayModel._data['start'][index.row()]
            elif column == 'end':
                activity.end = self.pandasDayModel._data['end'][index.row()]
            elif column == 'duration':
                activity.end = self.pandasDayModel._data['start'][index.row()] + self.pandasDayModel._data['duration'][index.row()]
            session.commit()
        self.loadData()
        
    def removeActivity(self,index):
        """
        Description:
            is called when removeActivity signal from context menu is emitted. Removes
            item on index from database.
        Args:
            index (QModelIndex): index what column and row in table view were removed 
        """             
        activity_id = self.pandasDayModel._data['Activity_id'][index.row()]
        with self.Session() as session:
            activity = session.query(db.Activity).filter(db.Activity.id==int(activity_id)).first()
            session.delete(activity)
            session.commit() 
        self.loadData()
        
    def addActivity(self):
        with self.Session() as session:
            tasks = session.query(db.Task).all()
        form = addForm(tasks = tasks)
        if form.exec() == QDialog.Accepted:
            hours, minutes = form.teStart.text().split(":")
            start = datetime(self.date.year,self.date.month,self.date.day, int(hours), int(minutes), 0)
            hours, minutes = form.teEnd.text().split(":")
            end = datetime(self.date.year,self.date.month,self.date.day, int(hours), int(minutes), 0)

            with self.Session() as session:
               session.add(db.Activity(task_id=tasks[form.cb.currentIndex()].id,start=start,end=end))
               session.commit()
        self.loadData()
    
class pandasDayModel(QAbstractTableModel,QObject):
    """
    Description:
        PandasDayModel class stores data for specific day.
        Model is editable.
    """
    def __init__(self):
        """
        Description:
            Constructor of pandasDayModel class. Sets Validators
            for users input.
        """        
        super().__init__() 
        self._data = None
        self.durationValidator = durationValidator()
        self.timeValidator = timeValidator() 
        
    def rowCount(self, index):
        """Return number of rows."""
        return len(self._data)

    def columnCount(self, index):
        """
        Return number of columns. Two columns are hidden bcs
        they contain only identifiers.
        ."""
        if not self._data.empty:
            return len(self._data.iloc[0])-2
        else:
            return 0

    def data(self, index, role=Qt.DisplayRole):
        """
        Description:
            view calls this function when it needs data.
        Args:
            index (QModelIndex): row and column where should be data inserted
            role (QRole): Specifies what role is asked. Defaults to Qt.DisplayRole.

        Returns:
            formatted data in string.
        """        
        if index.isValid():
            if role == Qt.DisplayRole or role == Qt.EditRole:
                value = self._data.iloc[index.row(),index.column()]
                if isinstance(value,datetime):
                    value = value.strftime("%H:%M:%S")
                elif isinstance(value,timedelta):
                    hours = value.seconds // 3600
                    minutes = (value.seconds // 60) - (hours * 60)
                    seconds = value.seconds - (minutes * 60) - (hours * 3600)
                    hours += (value.days * 24)
                    value = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                return str(value)

    def setData(self, index, value, role): 
        """
        Description:
            view calls this function when user completed editing.
        Args:
            index (QModelIndex): row and column where should be data inserted
            role (QRole): Specifies what role is asked. Defaults to Qt.DisplayRole.

        Returns:
            formatted True when data are well formatted else False.
        """        
        if role == Qt.EditRole or role == Qt.DisplayRole:
            if index.column() == 4:
                ret,value,_ = self.durationValidator.validate(value,0)
            else:
                ret,value,_ = self.timeValidator.validate(value,0)
            if ret != QValidator.Acceptable:
                return False
            date = self._data.iloc[index.row(),index.column()]
            if type(date) == datetime:
                dateValue = value.split(":")
                dateValue = createDatetime(date, hour=int(dateValue[0]), minute=int(dateValue[1]), second=int(dateValue[2]))
                value = dateValue
            self._data.iloc[index.row(),index.column()] = value
            self.dataChanged.emit(index,index)
            return True
        return False

    def flags(self, index):
        """
        Description:
            view calls this function when it needs metadata about cell on index.
        Args:
            index (QModelIndex): row and column where should be flags inserted
        Returns:
            flags for cell on index
        """        
        if index.column() > 1:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable   
        else:            
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def headerData(self, section, orientation, role):    
        """
        Description:
            view calls this function when it needs header's data.
        Args:
            section (int): column where should be data inserted
            role (QRole): Specifies what role is asked.
        Returns:
            data of header.
        """        
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._data.columns[section]

class pandasMonthModel(QAbstractTableModel):
    """
    Description:
        PandasMonthModel class stores data for specific month.
        Model is not editable.
    """
    def __init__(self):
        """
        Description:
            Constructor of pandasDayModel class. Sets Validators
            for users input.
        """        
        super().__init__() 
        self._data = None
    
    def rowCount(self, index):
        """Return number of rows."""

        return len(self._data)

    def columnCount(self, index):
        """Return number of columns."""
        if not self._data.empty:
            return len(self._data.iloc[0])
        else:
            return 0

    def data(self, index, role=Qt.DisplayRole):
        """
        Description:
            view calls this function when it needs data.
        Args:
            index (QModelIndex): row and column where should be data inserted
            role (QRole): Specifies what role is asked. Defaults to Qt.DisplayRole.

        Returns:
            formatted data in string.
        """        
        if index.isValid():
            if role == Qt.DisplayRole:
                if index.row() < len(self._data)-1 or index.column() == 1:
                    value = self._data.iloc[index.row(),index.column()]
                else:
                    value = "SUMMARY"
                if isinstance(value,datetime):
                    value = value.strftime("%d.%m.%Y")
                if isinstance(value,timedelta):
                    hours = value.seconds // 3600
                    minutes = (value.seconds // 60) - (hours * 60)
                    seconds = value.seconds - (minutes * 60) - (hours * 3600)
                    hours += (value.days * 24)
                    value = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                return str(value)
               

    def headerData(self, section, orientation, role): 
        """
        Description:
            view calls this function when it needs header's data.
        Args:
            section (int): column where should be data inserted
            role (QRole): Specifies what role is asked.
        Returns:
            data of header.
        """           
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._data.columns[section]
            
def createDatetime(date=None, year=0, month=0, day=0, hour=0, minute=0, second=0):
    """Combinates two datetimes into one. One is represented by datetime class and second
    is represented by integers year,month,day,hour,minute,second
    Args:
        date (datetime,optional): [description]. Defaults to None.
        year (int, optional): [description]. Defaults to 0.
        month (int, optional): [description]. Defaults to 0.
        day (int, optional): [description]. Defaults to 0.
        hour (int, optional): [description]. Defaults to 0.
        minute (int, optional): [description]. Defaults to 0.
        second (int, optional): [description]. Defaults to 0.

    Returns:
        [type]: [description]"""    
    if date:
        year = year or date.year
        month = month or date.month
        day = day or date.day
        hour = hour or date.hour
        minute = minute or date.minute
        second = second or date.second
        return datetime(year, month, day, hour, minute, second)
        
        
class durationValidator(QValidator):
    """
    validator for duration user input

    Args:
        QValidator : QT class for validating strings
    """    
    def __init__(self, parent=None):
        """Constructor"""
        super(durationValidator, self).__init__(parent)
    
    
    def validate(self, string, pos):
        """
        Validation process
        Args:
            string (str): string to validate
            pos (int): position of users input
        Returns:
            tuple (status, string,pos): QValidator.Acceptable/Invalid, newvalue,pos
        """        
        if string[0] == "0" and len(string)>1 and string[1] != ":":
            string = string[1:]
            pos = pos-1
        ps = re.search("^[:]", string)
        if ps:
            string = "0"+string
            return QValidator.Acceptable , string, pos+1
        ps = re.search("[:][0-9][:]", string)
        if ps:
            string = string[0:ps.start()+1]+"0"+string[ps.start()+1:]
            return QValidator.Acceptable , string, pos+1
        ps = re.search("[:]{1}[0-9]{1}$", string)
        if ps:
            string = string[:-1]+"0"+string[-1]
            return QValidator.Acceptable , string, pos+1
        ps = re.search("[:][0-9][0-5][0-9][:]", string)
        if ps:
            string = string[0:ps.start()+1]+string[ps.start()+2:]
            return QValidator.Acceptable , string, pos-1
        ps = re.search("[:][0-9][0-5][0-9]$", string)
        if ps:
            string = string[:-3]+string[-2:]
            return QValidator.Acceptable , string, pos+1
        if re.search("^[0-9]+[:][0-5][0-9][:][0-5][0-9]$", string):
            return QValidator.Acceptable, string, pos
        return QValidator.Invalid, string, pos
    
class timeValidator(QValidator):
    """
    validator for duration user input

    Args:
        QValidator : QT class for validating strings
    """    
    def __init__(self, parent=None):
        """Constructor"""
        super(timeValidator, self).__init__(parent)
        
    def validate(self, string, pos):
        """
        Validation process
        Args:
            string (str): string to validate
            pos (int): position of users input
        Returns:
            tuple (status, string,pos): QValidator.Acceptable/Invalid, newvalue,pos
        """        
        if string[0] == "0" and len(string)>1 and string[1] != ":":
            string = string[1:]
            pos = pos-1
        ps = re.search(r"^[:]", string)
        if ps:
            string = "0"+string
            return QValidator.Acceptable , string, pos+1
        ps = re.search(r"[:][0-9][:]", string)
        if ps:
            string = string[0:ps.start()+1]+"0"+string[ps.start()+1:]
            return QValidator.Acceptable , string, pos+1
        ps = re.search(r"[:]{1}[0-9]{1}$", string)
        if ps:
            string = string[:-1]+"0"+string[-1]
            return QValidator.Acceptable , string, pos+1
        ps = re.search(r"[:][0-9][0-5][0-9][:]", string)
        if ps:
            string = string[0:ps.start()+1]+string[ps.start()+2:]
            return QValidator.Acceptable , string, pos-1
        ps = re.search(r"[:][0-9][0-5][0-9]$", string)
        if ps:
            string = string[:-3]+string[-2:]
            return QValidator.Acceptable , string, pos+1
        if re.search(r"^(([0-1]?[0-9])|^([2][1-3]))[:][0-5][0-9][:][0-5][0-9]$", string):# or re.search("^[2][1-4][:][0-5][0-9][:][0-5][0-9]$", string):
            return QValidator.Acceptable, string, pos
        return QValidator.Invalid, string, pos

if __name__ == "__main__":
    pass
