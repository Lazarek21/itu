"""
    File name: windows.py
    Authors: Hynek Šabacký (xsabac02), David Lorenc (xloren16), Mikuláš Brázda (xbrazd21)
    Date created: 18/11/2021
    Date last modified: 5/12/2021
    Python Version: 3.9
"""

from PyQt5 import QtWidgets, QtCore
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import  QMenu, QLabel, QSizePolicy, QTabWidget, QWidgetAction, QAction, QMessageBox, QAbstractItemView, QDialog, QMainWindow, QFileDialog
from PyQt5.QtCore import QTimer, Qt, QDate
from PyQt5.QtGui import QColor, QIcon
from sqlalchemy.orm import  sessionmaker
from sqlalchemy import func, and_,extract, create_engine
from datetime import datetime, timedelta
import database as db
from forms import editForm
from myTreeItem import myTreeItem
from pandasModel import pandasData, createDatetime


engine = create_engine('sqlite:///db\\data.db', echo=False)

class mainView(QtWidgets.QMainWindow):
    def __init__(self):
        super(mainView, self).__init__()
        loadUi('mainView.ui', self)
        self.idx = 0
        self.selectedTask = None

        self.Session = sessionmaker(bind=engine)
        self.timer = QTimer()
        self.drawTreeTimer = QTimer()
        
        self._mainWindow = mainWindow(self)
        self._startWindow = startWindow(self)
        
        
            
        self.stackedWidget.addWidget(self._startWindow)
        self.stackedWidget.addWidget(self._mainWindow)
        
        self._mainWindow.pauseButton = self.pauseButton
        self._startWindow.start = self.pauseButton
        
        self._mainWindow.timeDisplay = self.timeDisplay
        self._startWindow.timeDisplay = self.timeDisplay
        
        self._mainWindow.stopButton = self.stopButton
        self._startWindow.stop = self.stopButton
        
        self._mainWindow.back = self.back
        self._startWindow.history = self.back
        
        self.initConnects()
        
        self.pauseButton.setEnabled(False)
        self.stopButton.hide()
        self.initTimer()
        
        self._startWindow.drawTree()
        self.show()
        
    def initConnects(self):
        self.back.clicked.connect(self.switchStack)    
        
    def switchStack(self):
        if self.idx == 1:
            self.back.setText("History")
            self.idx = -1
        else:
            self.back.setText("Timer")
        self.stackedWidget.currentWidget().hide()
        self.stackedWidget.setCurrentIndex(self.idx+1)
        self.idx += 1
        self.stackedWidget.currentWidget().show()
        
    def initTimer(self):
        """
        Author: 
            Mikuláš Brázda (xbrazd21)
        Description:
            Creates timers and check if user closed aplication without
            stopping activity. If there is running activity then
            timers are started. 
            self.timer updates time every second. 
            self.drawTreeTimer redraw tree every 36 seconds. 36 bcs 36/3600=0.01 and 
            display shows 2 decimal places
        """ 
        self.selectedTask = None
        with self.Session() as session:
            activity = session.query(db.Activity).filter_by(end=None).first()
            if activity:
                self._startWindow.treeWidget.setSelectionMode(QAbstractItemView.NoSelection)
                text = self.convertTimeDeltaToStr(activity.start,datetime.now())
                self.timeDisplay.setText(text)
                self.stopButton.show()
                self.pauseButton.setText("Pause")
                self.pauseButton.setEnabled(True)
                self.timer.start(1000)
                self.drawTreeTimer.start(36000)
                self.activity_id = activity.id
                self.selectedTask = session.query(db.Task).filter_by(id=activity.task_id).first()

    def convertTimeDeltaToStr(self, start,end):
        """
        Author: 
            Mikuláš Brázda (xbrazd21)
        Description: 
            Converts activity duration to string.
        Args:
            start (datetime): when activity started
            end (datetime): when activity ended
        Returns:
            string: string formated timedelta
        """ 
        td = end - start
        hours = td.seconds // 3600
        minutes = (td.seconds // 60) - (hours * 60)
        seconds = td.seconds - (minutes * 60) - (hours * 3600)
        hours += (td.days * 24)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def showTime(self):
        """
        Author: 
            Mikuláš Brázda (xbrazd21)
        Description:
            Reacts to self.timer.timeout() signal.
            Updates time on display time line edit.
        """ 
        display_time = self.timeDisplay.text().split(":")
        seconds = int(display_time[2])
        minutes = int(display_time[1])
        hours = int(display_time[0])
        seconds+=1
        if seconds > 59:
            minutes += 1
            seconds = 0
            if minutes > 59:
                hours += 1
                minutes = 0
        
        self.timeDisplay.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def startStopTimer(self):
        """
        Author: 
            Mikuláš Brázda (xbrazd21)
        Description:
            Reacts to start or pause button clicked
            When timer starts selected task is stored in parametr.
            
        """
        if not self.timer.isActive():
            self.timer.start(1000)
            self.drawTreeTimer.start(36000)
            self.pauseButton.setText("Pause")
            self.stopButton.show()
            self.selectedTask = self._startWindow.treeWidget.selectedItems()[0].model
            self._startWindow.treeWidget.setSelectionMode(QAbstractItemView.NoSelection)
            activity = db.Activity(start=datetime.now(),end=None,task_id=self.selectedTask.id)
            with self.Session() as session:
                session.add(activity)
                session.commit()
                session.refresh(activity)

            self.activity_id = activity.id
        else:
            with self.Session() as session:
                activity = session.query(db.Activity).filter_by(id=self.activity_id).first()
                activity.end = datetime.now()
                if activity.end - activity.start < timedelta(seconds=5):
                    session.delete(activity)
                else:
                    task = session.query(db.Task).filter_by(id=activity.task_id).first()
                session.commit()
            
            self._startWindow.drawTree()
            self.selectedTask = None
            self.activity = None
            self.pauseButton.setText("Continue")
            self.timer.stop()
            self.drawTreeTimer.stop()
            self._mainWindow.updateData()
            
            
    def resetTimer(self):
        """
        Author: 
            Mikuláš Brázda (xbrazd21)
        Description:
            Reacts to stop button clicked
        """  
        if self.timer.isActive():    
            with self.Session() as session:
                activity = session.query(db.Activity).filter_by(id=self.activity_id).first()
                activity.end = datetime.now()
                if activity.end - activity.start < timedelta(seconds=5):
                    session.delete(activity)
                elif self.timer.isActive():
                    task = session.query(db.Task).filter_by(id=activity.task_id).first()
                session.commit()
            self.selectedTask = None
            self.activity = None
            self.pauseButton.setText("Start")
            self.timer.stop()
            self.drawTreeTimer.stop()
            
        self._startWindow.drawTree()
        self.selectedTask = None
        self._mainWindow.timeDisplay.setText("00:00:00")
        self.timeDisplay.setText("00:00:00")
        self._startWindow.treeWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.stopButton.hide()
        self.pauseButton.setEnabled(False)
        self.pauseButton.setText("Start")
        self._mainWindow.updateData()

class startWindow(QtWidgets.QDialog):
    def __init__(self, main=None):
        """ 
        Author: 
            Hynek Šabacký (xsabac02)
        Description:
            constructor for start window, in which tasks can be viewed and edited 
            and timer can be started. Initialization of all components needed.
        Args:
            mainWindow (class mainWindow, optional): instance of mainWindow to 
            switch to when needed. Defaults to None.
        """        
        super(startWindow, self).__init__()
        loadUi('startWindow.ui', self) 
        self.Session = sessionmaker(bind=engine)
        self._main = main
        self.activity_id = None
        self.initTree()
        self.initConnects()
        
    def initConnects(self):
        """ 
        Author: 
            Hynek Šabacký (xsabac02)
        Description:
            Initialization of all buttons, timers and signals in startWindow
        """        
        self.treeWidget.itemSelectionChanged.connect(self.display_button)

        self._main.timer.timeout.connect(self._main.showTime)
        self._main.pauseButton.clicked.connect(self._main.startStopTimer)
        self._main.drawTreeTimer.timeout.connect(self.drawTree)
        self._main.stopButton.clicked.connect(self._main.resetTimer)  
        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.openMenu)
        self.treeWidget.itemExpanded.connect(self.changeToExpanded)
        self.treeWidget.itemCollapsed.connect(self.changeToCollapsed)
    
    def initTree(self):
        """ 
        Author: 
            Hynek Šabacký (xsabac02)
        Description:
            Initialization of QTreeWidget UI
        """        
        self.treeWidget.setColumnWidth(0, 750)
        self.treeWidget.setColumnWidth(2, 300)
        self.treeWidget.setToolTip("Right click to edit")
        self.drawTree()
    
    def display_button(self):
        """ 
        author: 
            Mikuláš Brázda (xbrazd21)
        Description:
            Start is enabled only if some task is selected. 
        """   
        if not self._main.selectedTask:
            self._main.pauseButton.setEnabled(self.treeWidget.selectedItems() != [])
        
    def openMenu(self, position):
        """ 
        Author: 
            Hynek Šabacký (xsabac02)
        Description:
            UI of context menu for task editing. Connecting QAction signals
            for action triggers.
        Args:
            position (QPoint): [description]
        """        
        item = self.treeWidget.itemAt(position)
        
        menu = QMenu()
        name =""
        if item:
            name = item.text(0)
            fbtl = QLabel(name)
            fbtl.setStyleSheet("font-weight: bold;")
            fbtl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            fbtl.setAlignment(Qt.AlignCenter)
            fbtlAction = QWidgetAction(fbtl)
            fbtlAction.setDefaultWidget(fbtl)
            menu.addAction(fbtlAction)
            menu.addSeparator()
        
        if item:
            if item.parent():
                addTask = menu.addAction("Add Task")
                addTask.setIcon(QIcon("resources\plus.png"))
                addTask.setData(item.parent())
                addTask.triggered.connect(self.addToTree)
                
                removeTask = menu.addAction("Remove Task")
                removeTask.setIcon(QIcon("resources\minus.png"))
                removeTask.setData(item)
                removeTask.triggered.connect(self.removeNode)

                editTask = menu.addAction("Edit Task")
                editTask.setIcon(QIcon("resources\edit.png"))
                editTask.triggered.connect(self.editNode)
                editTask.setData(item)

                menu.addSeparator()
                
                addProject = menu.addAction("Add Project")
                addProject.setIcon(QIcon("resources\plus.png"))
                addProject.triggered.connect(self.addToTree)
                addProject.setData(None)
                
                removeProject = menu.addAction("Remove Project")
                removeProject.setIcon(QIcon("resources\minus.png"))
                removeProject.triggered.connect(self.removeNode)
                removeProject.setData(item.parent())

                editProject = menu.addAction("Edit Project")
                editProject.setIcon(QIcon("resources\edit.png"))
                editProject.triggered.connect(self.editNode)
                editProject.setData(item.parent())
                
            else:
                addProject = menu.addAction("Add Project")
                addProject.setIcon(QIcon("resources\plus.png"))
                addProject.triggered.connect(self.addToTree)
                addProject.setData(None)
                
                removeProject = menu.addAction("Remove Project")
                removeProject.setIcon(QIcon("resources\minus.png"))
                removeProject.triggered.connect(self.removeNode)
                removeProject.setData(item)

                editProject = menu.addAction("Edit Project")
                editProject.setIcon(QIcon("resources\edit.png"))
                editProject.triggered.connect(self.editNode)
                editProject.setData(item)

                menu.addSeparator()

                addTask = menu.addAction("Add Task")
                addTask.setIcon(QIcon("resources\plus.png"))
                addTask.triggered.connect(self.addToTree)
                addTask.setData(item)
            
            menu.addSeparator()
               
            if item.background(0).color().getRgb() == (0, 255, 0, 60):
                completeTask = menu.addAction("Set as incomplete")
                completeTask.setIcon(QIcon("resources\incomplete.png"))
            else:
                completeTask = menu.addAction("Set as complete")
                completeTask.setIcon(QIcon("resources\complete.png"))
            completeTask.triggered.connect(self.completeNode)
            completeTask.setData(item)
        else:
            addProject = menu.addAction("Add Project")
            addProject.setIcon(QIcon("resources\plus.png"))
            addProject.triggered.connect(self.addToTree)
            addProject.setData(None)

        menu.exec(self.treeWidget.mapToGlobal(position))

    def keyPressEvent(self, event):
        """ 
        Author: 
            Hynek Šabacký (xsabac02)
        Description:
            Connecting delete button to deletion of task
        Args:
            event (QEvent): Triggered key event
        """        
        if event.key() == QtCore.Qt.Key_Delete:
            action = QAction()
            if self.treeWidget.selectedItems():
                action.setData(self.treeWidget.selectedItems()[0])
                action.triggered.connect(self.removeNode)
                action.trigger()
            
        event.accept()
    
    @QtCore.pyqtSlot()
    def addToTree(self):
        """
        Author:
            David Lorenc (xloren16)
        Description:
            It get data from Edit form and insert then to database.
        Args:
        """        
        action = self.sender()
        form = editForm(self,action="Add")
        parent_id = action.data().model.id if action.data() else None 
        if form.exec() == QDialog.Accepted:
            with self.Session() as session:
                session.add(db.Task(name=form.new_name.text(),estimated=form.estimated.text(),parent_id=parent_id))
                session.commit()
            self.drawTree()
    
    @QtCore.pyqtSlot()
    def removeNode(self):
        """
        Author:
            David Lorenc (xloren16)
        Description:
            It remove selected item.
        Args:
        """      
        action = self.sender()
        msg = QMessageBox()
        if self._main.selectedTask:
            if action.data().model.id == self._main.selectedTask.id or action.data().model.id == self._main.selectedTask.parent_id:
                msg.critical(self,"Remove","Cannot be deleted because you have work in progress here",QMessageBox.Ok) 
                return               
        ret = msg.question(self,"Remove",f"Do you really want to remove \"{action.data().text(0)}\"?",QMessageBox.Ok | QMessageBox.Cancel)
        if ret == QMessageBox.Ok:
            with self.Session() as session:
                task = session.query(db.Task).filter_by(id=action.data().model.id).first()
                session.delete(task)
                session.commit()
            self.drawTree()

    @QtCore.pyqtSlot()
    def editNode(self):
        """
        Author:
            David Lorenc (xloren16)
        Description:
            It edit selected item with data from edit form.
        Args:
        """        
        action = self.sender()
        form = editForm(self, action.text(), action.data().text(0), action.data().text(1))
        if form.exec() == QDialog.Accepted:
            with self.Session() as session:
                task = session.query(db.Task).filter_by(id=action.data().model.id).first()
                task.name = form.new_name.text()
                task.estimated = form.estimated.text()
                session.commit()
            self.drawTree()
            
    @QtCore.pyqtSlot()
    def completeNode(self):
        """
        Author:
            David Lorenc (xloren16)
        Description:
            It set selected node on completed and set background for it.
        """        
        action = self.sender()
        with self.Session() as session:
            task = session.query(db.Task).filter_by(id=action.data().model.id).first()
            if task.completed:
                task.completed = False
            else:
                task.completed = True
            session.commit()
        self.drawTree()           
            
    def changeToExpanded(self,item):
        """
        Author: 
            Mikuláš Brázda (xbrazd21)
        Description:
            Store to database that item is expanded.
        Args:
            item myTreeItem: item which was expanded
        """     
        with self.Session() as session:
            task = session.query(db.Task).filter_by(id=item.model.id).first()
            task.expanded = True
            session.commit()
            
    def changeToCollapsed(self,item):
        """
        Author: 
            Mikuláš Brázda (xbrazd21)
        Description:
            Store to database that item is collapsed.
        Args:
            item myTreeItem: item which was collapsed
        """     
        with self.Session() as session:
            task = session.query(db.Task).filter_by(id=item.model.id).first()
            task.expanded = False
            session.commit()
            
    def drawTree(self):
        """
        Author:
            David Lorenc (xloren16)
        Description:
            It select all task without parent from database, write they as project and insert all child from attribute children as project task.
        """        
        task_sum = 0
        self.treeWidget.clear()
        task_id = self._main.selectedTask.id if self._main.selectedTask else None
        color = QColor()
        color.setRgb(0, 255, 0, 60)
        with self.Session() as session:
            tasks = session.query(db.Task).filter_by(parent_id=None).all()
            for task in tasks:
                res = session.query(func.sum(extract('epoch', db.Activity.end) - extract('epoch', db.Activity.start)).label("duration")).filter(and_(db.Activity.end != None,db.Activity.task_id ==task.id)).group_by(db.Activity.task_id).first()
                running_activity = session.query(db.Activity).filter(and_(db.Activity.end==None,db.Activity.task_id==task.id)).first()
                if running_activity:
                    task_sum += (datetime.now() - running_activity.start).seconds
                task_sum = res.duration if res else 0
                topItem = myTreeItem([task.name,f"{task.estimated}h", '0'],task)
                self.treeWidget.addTopLevelItem(topItem) 
                if task.expanded:
                    self.treeWidget.expandItem(topItem)
                for child in task.children:
                    child_sum = session.query(func.sum(extract('epoch', db.Activity.end) - extract('epoch', db.Activity.start)).label("duration")).filter(and_(db.Activity.end != None,db.Activity.task_id==child.id)).group_by(db.Activity.task_id).first()
                    child_sum = child_sum.duration if child_sum else 0
                    running_activity = session.query(db.Activity).filter(and_(db.Activity.end==None,db.Activity.task_id==child.id)).first()
                    if running_activity:
                        child_sum += (datetime.now() - running_activity.start).seconds
                    task_sum += child_sum
                    
                    taskChild = myTreeItem([child.name,f"{child.estimated}h", '{:0.2f} h'.format(child_sum / 3600)],child)
                    topItem.addChild(taskChild)
                    if child.expanded:
                        self.treeWidget.expandItem(child)
                    taskChild.create_progress_bar(self.treeWidget, child.estimated, child_sum)
                    if task.completed or child.completed:
                        for i in range(4):
                            taskChild.setBackground(i, color)
                    if child.id == task_id:
                        taskChild.setSelected(True)
                topItem.setText(2,'{:0.2f} h'.format(task_sum / 3600))
                topItem.create_progress_bar(self.treeWidget, task.estimated, task_sum)
                if task.completed:
                        for i in range(4):
                            topItem.setBackground(i, color)
                if task.id == task_id:
                    topItem.setSelected(True)

class mainWindow(QtWidgets.QDialog):
    def __init__(self, main=None):
        """
        Author:
            Hynek Šabacký (xsabac02)
        Description:
            Constructor of main window where history and day + month summaries can be viewed.
            Initialization of ui and signal connects.
        Args:
            startWindow (class startWindow, optional): instance of class startWindow
        """ 
        super(mainWindow, self).__init__()
        loadUi('mainWindow.ui', self) 
        
        self._main = main
        self.splitter.setSizes([600, 530, 270])
        self.pandasData = pandasData(datetime.now())
        self.dayTableView.setModel(self.pandasData.pandasDayModel)
        self.monthTableView.setModel(self.pandasData.pandasMonthModel)
        self.dayTableView.setToolTip("Right click to edit")
        self.initConnects()
        
    def initConnects(self):
        """
        Author:
            Hynek Šabacký (xsabac02)
        Description:
            Initialization of signals and slots
        """ 
        self.today.clicked.connect(self.setToday)
        self.calendarWidget.selectionChanged.connect(self.updateModels)
        self.calendarWidget.currentPageChanged.connect(self.updateModels)
        self.export.clicked.connect(self.file_save)
        self.dayTableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dayTableView.customContextMenuRequested.connect(self.openMenu)

    def updateModels(self, year=None, month=None): 
        """
        Author:
            Hynek Šabacký (xsabac02)
        Description:
            Updates models to view actual current data
        Args:
            year (int, optional): selected year
            month (int, optional): selected month
        """ 
        date = self.getDate()
        if month and year:
            date = createDatetime(date, year=year, month=month)
        
        self.pandasData.date = date
        self.pandasData.fillModels()
        
    def getDate(self):
        """
        Author:
            Hynek Šabacký (xsabac02)
        Description:
            Get current date from QCalendarWidget
        """ 
        date = createDatetime(self.calendarWidget.selectedDate().toPyDate(), hour=1, minute=1, second=1)
        return date
    
    def updateData(self):
        """
        Author:
            Hynek Šabacký (xsabac02)
        Description:
            Update data in models
        """ 
        self.pandasData.date = self.getDate()
        self.pandasData.loadData()
        
    def setToday(self):
        """
        Author:
            Hynek Šabacký (xsabac02)
        Description:
            Set todays date as selected in QCalendarWidget
        """ 
        date = QDate()
        todayDate = datetime.now()
        date.setDate(todayDate.year, todayDate.month, todayDate.day)
        self.calendarWidget.setSelectedDate(date)
        
    def file_save(self):
        """
        Author:
            Hynek Šabacký (xsabac02)
        Description:
            Export month data as csv
        """ 
        fileDialog = QFileDialog()
        fileDialog.setDefaultSuffix("csv")
        name, _ = fileDialog.getSaveFileName(self, 'Save File', f'{self.calendarWidget.monthShown()}-{self.calendarWidget.yearShown()}.csv')
        if name != '':
            file = open(name,'w')
            file.write(self.pandasData.pandasMonthModel._data.to_csv(line_terminator="\n",sep=';'))
            file.close()
    
    def openMenu(self,position):
        """
        Author:
            Hynek Šabacký (xsabac02)
        Description:
            Open extension menu on right click
        Args:
            position (QPoint, optional): Position of right click
        """ 
        contextMenu = QMenu()
        index = self.dayTableView.indexAt(position)
        addActivity = contextMenu.addAction("Add Activity")
        addActivity.setIcon(QIcon("resources\plus.png"))
        addActivity.triggered.connect(self.addActivity)
        if index.isValid():
            removeActivity = contextMenu.addAction("Remove Activity")
            removeActivity.setIcon(QIcon("resources\minus.png"))
            removeActivity.triggered.connect(self.removeActivity)
            removeActivity.setData(index)
        contextMenu.exec(self.dayTableView.viewport().mapToGlobal(position))

    def removeActivity(self):
        """
        Author:
            Hynek Šabacký (xsabac02)
        Description:
            Removes activity from database
        """ 
        index = self.sender().data()   
        self.pandasData.removeActivity(index)
        self._main._startWindow.drawTree()
        
    def addActivity(self):
        """
        Author:
            Hynek Šabacký (xsabac02)
        Description:
            Add activity to database
        """  
        self.pandasData.addActivity()
        self._main._startWindow.drawTree()
        

