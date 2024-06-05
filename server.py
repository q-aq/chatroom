import sys
from PyQt5 import QtCore,QtGui,QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from Ui_server import Ui_Dialog
import Ui_file
import Ui_emoji
import threading
import logging
import socket
import os
import csv

logging.basicConfig(filename="server.log",level=logging.DEBUG)

class server(QMainWindow,Ui_Dialog):
    update = QtCore.pyqtSignal(bytes)
    def __init__(self,parent=None):
        super(server, self).__init__(parent)
        self.isRun = True
        logging.info("Successfully logged in to the server")
        self.setupUi(self)
        self.path = os.getcwd()+"\\server_recv_file\\"
        self.update.connect(self.recv_information)
        self.btn_close.clicked.connect(self.server_close)#关闭按钮
        self.btn_file.clicked.connect(self.open_file)#选择文件按钮
        self.btn_sent.clicked.connect(self.sent_information)#发送按钮
        self.btn_sent.clicked.connect(self.sent_information)
        self.btn_emoji.clicked.connect(self.show_emoji)
        self.btn_color.clicked.connect(self.open_color)
        self.btn_echo.clicked.connect(self.show_filerecv)
        self.btn_del.clicked.connect(self.setUserList)
        self.btn_sent.setShortcut("Return")
        self.color = QtGui.QColor("#87CEFA")
        self.color_string = self.color.name()
        self.Login()
        self.show() 
    '''连接用函数，可以用于向另一端发送或者接受信息'''
    def Exit(self):
        self.isRun = False
        self.SendStr("prom"+self.color_string+"聊天室将于3秒后关闭")
        try:
            self.client_socket.close()
        except Exception as e:
            logging.error(f"Error closing client:{e}")
        try:
            self.server_socket.close()
        except Exception as e:
            logging.error(f"Error closing server:{e}")
    def Login(self):
        self.isRun = True
        self.open_file_recv()
        self.server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        port = 50500
        host = socket.gethostname()
        self.server_socket.bind((host,port))
        self.server_socket.listen(5)
        self.clients = []
        # print(self.clients)
        self.MaxSize = 10240
        self.accept = threading.Thread(target=self.acceptconnection)
        self.accept.start()
    def SendStr(self,text):
        '''定义三种格式的信息 info::普通信息,meoj::表情信息,prom::提示信息'''
        '''文件发送格式info+#FFFFFF+message'''
        try:
            if text != "info" and len(text) != 4:
                text = text.encode("utf-8")
                self.client_socket.send(text)
        except Exception as e:
            logging.error(f"Server sending information error{e}")
            self.client_socket.close()
    def SendByte(self,byte):
        if byte is not None:
            try:
                self.client_socket.sendall(byte)
            except Exception as e:
                logging.error(f"Server sending information error:{e}")
    def acceptconnection(self):
        while True:
            try:
                self.client_socket,addr = self.server_socket.accept()#等待并接受一个连接请求
                logging.info(f"welcome{addr}link")
                self.SendStr("prom"+self.color_string+"欢迎")
                self.btn_del.click()
                clien_thread = threading.Thread(target=self.recv)
                clien_thread.start()
            except Exception as e:
                logging.error(f"Connection client error:{e}")
                break
    def recv(self):
        while True:
            try:
                data = self.client_socket.recv(self.MaxSize)
                if not data:
                    break
                self.update.emit(data)
            except Exception as e:
                logging.error(f"Server receiving information error:{e}")
                break
        self.client_socket.close()
    def recv_information(self,data):
        self.setUserList()
        try:
            message = data.decode("utf-8")
            type_mseeage = message[:4]
            type_color = message[4:11]
            self.colors = QtGui.QColor(type_color)
            message = message[11:]
        except UnicodeDecodeError:
            message = data[:11].decode("utf-8")
            type_mseeage = message[:4]
            type_color = message[4:11]
        # print("message:"+message)
        # print("type:"+type_mseeage)
        # print("color:"+type_color)
        # print("==========")
        logging.info(f"Server successfully received information:{message}")
        if type_mseeage=="info":
            self.other_sent(message,self.clients_name,self.colors)
        if type_mseeage=="emoj":
            self.other_sent_emoj(message)
        if type_mseeage=="prom":
            self.show_information(message)
        if type_mseeage == "name":
            self.show_information(message)
            message = message[3:]
            message = message[:-4]
            self.clients_name = message
        elif type_mseeage == "file":
            length = len(type_mseeage.encode("utf-8"))+len(type_color.encode("utf-8"))
            filedata = data[length:]
            self.recv_file(filedata)
        elif type_mseeage == "fina":
            self.recv_file_name(message)
    def getUserList(self):#获取用户列表
        with open("userlist.csv",'r',newline='',encoding='utf-8') as s:
            if len(s.read()) != 0:
                s.seek(0)
                t = csv.reader(s)
                l = list(t)
                return l[0]
            else:
                return []
    def setUserList(self):
        list = self.getUserList()
        self.userlist.clear()
        for us in list:
            self.userlist.append(us)
    def recv_file_name(self,message):
        self.file_name = message
        self.uis.file_name.append(self.file_name)
        self.uis.file_save_path.append(self.path)
    def recv_file(self,message):
        if message !="":
            with open(self.path+self.file_name,'ab') as file:
                file.write(message)
    def sent_file(self,name,path):
        if not os.path.isfile(path):
            logging.error(f"File {path} does not exist")
            return
        self.SendStr("fina#FFFFFF"+name)#首先发送文件名
        # self.SendStr("info"+self.color_string+"文件:"+name+"已发送")
        try:
            with open(path,'rb') as file:#发送文件字节流
                header = "file#FFFFFF"
                headers = header.encode("Utf-8")
                while True:
                    byte_read = file.read(10240 - len(headers))
                    if not byte_read:
                        break
                    sentdata = headers+byte_read#这里为字节流数据
                    self.SendByte(sentdata)
        except Exception as e:
            logging.error(f"Client file sending failed:{e}")
    def server_close(self):#关闭界面按钮，需要
        chose = QMessageBox.question(None,"提示","您确定要退出吗！",QMessageBox.Yes|QMessageBox.No)
        if chose == QMessageBox.Yes:
            '''以下语句块可用于当用户登录后显示某某用户登录'''
            color=QtGui.QColor("white")
            cursor = self.information.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            back_format = QtGui.QTextBlockFormat()#创建一个QTextBlockFormat的对象，用来设置文本块的格式
            back_format.setAlignment(QtCore.Qt.AlignCenter)#设置文本块的对齐方式为右对齐
            cursor.mergeBlockFormat(back_format)
            cursor.insertText("===聊天室将在3秒后关闭!===")
            format = cursor.charFormat()
            format.setBackground(color)
            cursor.setPosition(cursor.position() - 17, QtGui.QTextCursor.KeepAnchor)
            cursor.setCharFormat(format)
            self.information.setTextCursor(cursor)
            self.Exit()
            QtCore.QTimer.singleShot(3000,sys.exit)
        else:
            return 0
    def open_file(self):#文件传送，后期需要重点解决文件传送问题
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName()
        if file_path:
            file_name = os.path.basename(file_path)
            self.sent_file(file_name,file_path)
    def show_information(self,text,color=QtGui.QColor("white")):#用来显示各种信息
        # color = QtGui.QColor("white")
        cursor = self.information.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        back_format = QtGui.QTextBlockFormat()
        back_format.setAlignment(QtCore.Qt.AlignCenter)
        cursor.mergeBlockFormat(back_format)
        cursor.insertText("==="+text+"===\n")
        format = cursor.charFormat()
        format.setBackground(color)
        cursor.setPosition(cursor.position()-len(text)-7,QtGui.QTextCursor.KeepAnchor)
        cursor.setCharFormat(format)
        self.information.setTextCursor(cursor)
    def sent_information(self):#获取输入框中的信息，然后，调用函数送入聊天框
        text = self.lineEdit.text()
        self.lineEdit.clear()
        self.sent_with_background(text,self.color)
        self.color_string = self.color.name()
        self.SendStr("info"+self.color_string+text)
    def sent_with_background(self,text,color=QtGui.QColor("#87CEFA")):#设置文字背景颜色，并将文字送入聊天框
        self.color = color
        cursor = self.information.textCursor()#获取当前textEdit的文本光标
        cursor.movePosition(QtGui.QTextCursor.End)#将光标移动到文本的尾部
        back_format = QtGui.QTextBlockFormat()#创建一个QTextBlockFormat的对象，用来设置文本块的格式
        back_format.setAlignment(QtCore.Qt.AlignRight)#设置文本块的对齐方式为右对齐
        cursor.mergeBlockFormat(back_format)#将新的文本块格式应用到当前光标所在的文本块
        if text !="":
                format = cursor.charFormat()#获取当前字符串格式
                format.setBackground(self.color)#设置文本背景颜色
                cursor.setCharFormat(format)#将新的字符格式应用到当前选定的文本上
                cursor.insertText(text+" :admin"+"\n")#再当前光标位置插入文本
                # 计算光标需要移动的位置，从当前位置向前移动文本的长度加上额外的 ":admin" 字符和一个换行符的长度。
                cursor.setPosition(cursor.position() - len(text) - 8, QtGui.QTextCursor.KeepAnchor)
        self.information.setTextCursor(cursor)#更新光标的位置
    def other_sent(self,text,username="text",color=QtGui.QColor("#A2e322")):#获取对方发送的信息,送到聊天框
        self.colors = color
        cursor = self.information.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        back_format = QtGui.QTextBlockFormat()
        back_format.setAlignment(QtCore.Qt.AlignLeft)
        cursor.mergeBlockFormat(back_format)
        if text !="":
                cursor.insertText(username+": "+text+"\n")
                format = cursor.charFormat()
                format.setBackground(self.colors)
                cursor.setPosition(cursor.position() - len(text) - len(username)-3, QtGui.QTextCursor.KeepAnchor)
                cursor.setCharFormat(format)
        self.information.setTextCursor(cursor)
    def other_sent_emoj(self,text,color=QtGui.QColor("#87CEFA")):
        cursor = self.information.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        back_format = QtGui.QTextBlockFormat()
        back_format.setAlignment(QtCore.Qt.AlignLeft)
        cursor.mergeBlockFormat(back_format)
        if text !="":
            cursor.insertText("\n")
            self.information.insertHtml(text)
            cursor.insertText("\n")
        self.information.setTextCursor(cursor)
    def show_emoji(self):
        self.emoji = QtWidgets.QMainWindow()
        self.ui = Ui_emoji.Ui_Form()
        self.ui.setupUi(self.emoji,self)
        xy = self.geometry()
        x = xy.x()
        y = xy.y()
        emoji_x = x - self.emoji.width()
        emoji_y = y
        self.emoji.move(emoji_x,emoji_y)
        self.emoji.show()
    def open_color(self):
        co = QColorDialog.getColor()
        self.color = QtGui.QColor(co.name())
        self.color_string = self.color.name()
    def open_file_recv(self):
        self.filerecv = QtWidgets.QMainWindow()
        self.uis = Ui_file.Ui_MainWindow()
        self.uis.setupUi(self.filerecv,self)
        xy = self.geometry()
        x = xy.x()
        y = xy.y()
        file_x = x+self.filerecv.width()
        file_y = y
        self.filerecv.move(file_x,file_y)
    def show_filerecv(self):
        self.filerecv.show()