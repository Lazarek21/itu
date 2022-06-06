"""
   File name: tmt.py
   Author: Hynek Šabacký (xsabac02)
   Date created: 18/11/2021
   Date last modified: 5/12/2021
   Python Version: 3.9
"""

import sys
from PyQt5.QtWidgets import QApplication
from windows import mainView

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window2 = mainView()
    
    window2.move(400, 100)
    window2.show()
    # window2.handleButton()

    sys.exit(app.exec_())