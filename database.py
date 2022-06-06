"""
    File name: database.py
    Author: Mikuláš Brázda (xbrazd21)
    Date created: 18/11/2021
    Date last modified: 5/12/2021
    Python Version: 3.9
"""
from sqlalchemy import create_engine,Column, Integer, String, Sequence, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.expression import false, true
from sqlalchemy.sql.sqltypes import  Boolean, DateTime
import os
import argparse
from datetime import datetime, timedelta
Base = declarative_base()
import random

class Activity(Base):
    """Activity database entity
    Columns:
        id = identifier of each record
        start = datetime when did activity start
        end = datetime when did activty end
        task_id = id of task for which was activity started
    Args:
        Base(declarative_base()): base for ORM mapper  
    """    
    __tablename__ = 'Activity'
    id = Column(Integer,Sequence('activity_id_seq'), primary_key=True)
    start = Column(DateTime)
    end = Column(DateTime)
    task_id = Column(Integer, ForeignKey('Task.id',ondelete="CASCADE"),nullable=True)
    task = relationship('Task', back_populates='activities')

class Task(Base):
    """Task database entity.
    columns:
        id = identifier of each record
        name = name of the task
        estimated = estimated time for whole task
        completed = true if task is marked as done else false
        expanded = keeps information about expansion of task in tree view
        parent_id = subtask must have a parent task
    Args:
        Base(declarative_base()): base for ORM mapper  
    """    
    __tablename__ = 'Task'
    id = Column(Integer,Sequence('task_id_seq'), primary_key=True)
    name = Column(String)
    estimated = Column(Integer,default=0)
    done = Column(Integer,default=0)
    completed = Column(Boolean, default=False)
    expanded = Column(Boolean,default=False)
    parent_id = Column(Integer, ForeignKey('Task.id',ondelete="CASCADE"),nullable=True)
    children = relationship('Task',cascade='all,delete')
    activities = relationship('Activity', back_populates='task',cascade='all,delete')
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="TODO Database manupulation")
    parser.add_argument('-r', dest="reset", help="Clean database", action="store_true")
    parser.add_argument('-p', dest="printer", help="Print database table (all lowercase)", nargs=1)
    parser.add_argument('-d', dest="delete", help="Delete from db (PK, name of table)", nargs=2)
    parser.add_argument('-i', dest="init", help="initialize database", action="store_true")
    parser.add_argument('-c', dest="reinit", help="Clean and initialize database", action="store_true")
    parser.add_argument('-a', dest="adder", metavar='N', type=str , nargs='*', help="Add database table TBD.", default=[])
    args = parser.parse_args()
    
    database_found = os.path.exists('db\\data.db')
    if database_found and (args.reset or args.reinit):
        os.remove('.\\db\\data.db')
        os.rmdir('.\\db')
        database_found = None
    if not database_found:
        os.makedirs(os.path.dirname('db\\data.db'))
           
    engine = create_engine('sqlite:///db\\data.db', echo=False)
    if not database_found:
        Base.metadata.create_all(engine)


    Session = sessionmaker(bind=engine)
    session = Session()
    if args.init or args.reinit:
        task1 = Task(name='ITU',estimated=200)
        task2 = Task(name='backend',estimated=125,parent_id=1)
        task3 = Task(name='frontend',estimated=75,parent_id=1)
        task4 = Task(name='IIS',estimated=500, parent_id=None)
        task5 = Task(name='frontend',estimated=75,parent_id=4)
        task6 = Task(name='backend',estimated=75,parent_id=4)
        task7 = Task(name='database',estimated=75,parent_id=4)
        task8 = Task(name='rest',estimated=75,parent_id=4)
        activities = []
        lastdays = [31,28,31,30,31,30,31,31,30,31,30,31]
        for year in range(2021,2023):
            for month in range(1,13):
                start_datetime = f"1/{month}/{year}"
                end_datetime = f"{lastdays[month-1]}/{month}/{year}"
                datetime_format = "%d/%m/%Y" 
                for i in range(20):
                    dt_start = datetime.strptime(start_datetime,datetime_format)
                    dt_end = datetime.strptime(end_datetime,datetime_format)
                    random_date_start = datetime(
                        year=random.randint(dt_start.year,dt_end.year),
                        month=random.randint(dt_start.month,dt_end.month),
                        day=random.randint(dt_start.day,dt_end.day),
                        hour=random.randint(0,23),
                        minute=random.randint(0,59),
                        second=random.randint(0,59))
                    random_date_end = random_date_start + timedelta(seconds=random.randint(0,10000))
                    act = Activity(start=random_date_start, end=random_date_end, task_id=random.randint(1,8))
                    activities.append(act)

        session.add_all([task1,task2,task3,task4,task5,task6,task7,task8])
        session.add_all(activities)
        session.flush()
        
    if args.delete:
        if args.delete[1] == "activity":    
            session.query.filter(Activity.id == args.delete[0]).delete()
        if args.delete[1] == "task":  
            session.query.filter(Task.id == args.delete[0]).delete()

    if args.printer:
        print("")
        if args.printer[0] == "activity":
            print("----ACTIVITIES-----")
            for res in session.query(Activity).all():
                print("ID        = ", res.id)
                print("start     = ", res.start)
                print("end       = ", res.end)
                if res.end:
                    print("(Duration = ", res.end-res.start, ")")
                print("task_id   = ", res.task_id)
                print("")
        elif args.printer[0] == "task":
            print("-------TASKS-------")
            for res in session.query(Task).all():
                print("ID        = ", res.id)
                print("name      = ", res.name)
                print("estimated = ", res.estimated)
                print("done      = ", res.done)
                print("parent_id = ", res.parent_id)
                print("")
    session.commit()  
    