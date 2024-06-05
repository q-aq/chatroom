from login import login
import sys
from PyQt5.QtWidgets import *
def run_app():
    app = QApplication(sys.argv)
    s = login()
    sys.exit(app.exec_())
run_app()