from PyQt5 import QtCore,QtGui,QtWidgets
from Ui_login import Ui_MainWindow
from PyQt5.QtWidgets import *
from server import server
from client import client
import csv

class login(QMainWindow,Ui_MainWindow):
    def __init__(self,parent=None):
        super(login,self).__init__(parent)
        self.setupUi(self)
        self.userlist = []
        self.found = False
        self.username.setFocus()
        self.username.returnPressed.connect(self.password.setFocus)#按下回车转到下一行
        self.password.returnPressed.connect(self.btn_login.click)
        self.btn_login.clicked.connect(self.open_server)#为登录按钮设置槽函数
        self.btn_exit.clicked.connect(self.close)#为退出按钮设置槽函数
        self.show()

    def getlist(self):#获取用户列表
        with open("userlist.csv",'r',newline='',encoding='utf-8') as s:
            if len(s.read()) != 0:
                s.seek(0)
                t = csv.reader(s)
                l = list(t)
                return l[0]
            else:
                return []
    def open_server(self):
        self.userlist = []
        username = self.username.text()
        password = self.password.text()
        self.found = False
        with open('date.csv', 'r', newline='', encoding='utf-8') as f:
            rows = csv.reader(f)
            for row in rows:
                if row[0] == username and row[1] == password and row[2] == 'admin':
                    self.found = True
                    self.server = server()
                    self.btn_exit.click()
                    break
                elif row[0] == username and row[1] == password and row[2] == 'user':
                    self.found = True
                    ls = self.getlist()
                    if username not in ls:#判断该用户是否在用户列表中
                        with open("userlist.csv","a") as f:
                            f.write(str(row[0])+",")
                            name = str(row[0])
                            self.client = client(name)
                        self.btn_exit.click()
                        break
                    else:
                        self.info = QMessageBox()
                        self.info.setText("该用户已登录，请勿重复登录")
                        self.info.setWindowTitle("提示")
                        self.info.setIcon(QMessageBox.Critical)
                        self.info.show()
                        self.username.clear()
                        self.password.clear()
                        self.username.setFocus()
                        return 0
                continue
            if not self.found:
                self.mgs = QMessageBox()
                self.mgs.setText("用户名或密码错误!")
                self.mgs.setWindowTitle("Warn")
                self.mgs.setIcon(QMessageBox.Critical)
                self.mgs.show()
                self.username.clear()
                self.password.clear()
                self.username.setFocus()
            self.found = False

