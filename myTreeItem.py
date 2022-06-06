"""
    File name: myTreeItem.py
    Author: Hynek Šabacký (xsabac02)
    Date created: 18/11/2021
    Date last modified: 5/12/2021
    Python Version: 3.9
"""

from PyQt5.QtWidgets import QProgressBar, QTreeWidgetItem

class myTreeItem(QTreeWidgetItem):
    def __init__(self, strings=[], model=None):
        """ Constructor of myTreeWidgetItem inheriting QTreeWidgetItem from Qt.
            Added functionality is property of name model, holding the model
            from database.
            
        Args:
            strings (list, optional): strings needed for inherited constructor. Defaults to [].
            model (orm class, optional): Model with data from database. Defaults to None.
        """
        super(myTreeItem, self).__init__(strings)
        self.model = model
        
    def initProgressBar(self, pbar):
        """Initialization of progressbar to be shown

        Args:
            pbar (QProgressBar): Created progress bar for task
        """
        self._pbar = pbar
    
    def setProgressBar(self, percentage):
        """Setting the percentage value in shown progressbar

        Args:
            percentage (int): percentage
        """        
        self._pbar.setValue(percentage)
        
    def create_progress_bar(self, treeWidget, est, done):
        """Creation of progress bar for the myTreeItem instance

        Args:
            treeWidget (QTreeWidgetItem): Class in which this myTreeItem instance is stored
            est (int): Estimated time of task
            done (int): Done time of task
        """        
        pbar = QProgressBar(treeWidget)
        pbar.move(5, 5)
        pbar.setMaximum(100)
        done = done/3600
        if est != 0:
            percentage = round(done*100/(est))
        else:
            percentage = 100
        
        if percentage > 100:
            pbar.setValue(100)  
        else:
            pbar.setValue(percentage)

        pbar.setMinimumSize(150, 0)
        pbar.setStyleSheet("""
                            QProgressBar::chunk {
                            background-color: #3add36;
                            width: 1px;
                        }

                        QProgressBar {
                            border: 1px solid grey;
                            border-radius: 0px;
                            text-align: center;
                            max-height: 30px;
                        }
                            """)
        treeWidget.setItemWidget(self, 3, pbar) 
