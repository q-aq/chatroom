import sys
from PyQt5 import QtCore,QtGui,QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QWidget
from Ui_client import Ui_MainWindow
import Ui_file
import Ui_emoji
import logging
import threading
import socket
import os
import csv

# logging.basicConfig(filename="client.log",level=logging.DEBUG)

class client(QMainWindow,Ui_MainWindow):
    update = QtCore.pyqtSignal(bytes)
    def __init__(self,name,parent=None):
        super(client,self).__init__(parent)
        self.isRun = True
        logging.info("Successfully logged in to the client")
        self.setupUi(self)
        self.path = os.getcwd()+"\\client_recv_file\\"#设置默认文件存放地址
        self.update.connect(self.recv_information)#接收到信息后触发该信号，是的对GUI界面的更新不在接收线程中
        self.btn_exit.clicked.connect(self.client_close)
        self.btn_sent.clicked.connect(self.sent_information)
        self.btn_sent.clicked.connect(self.sent_information)
        self.btn_file.clicked.connect(self.open_file)
        self.btn_emoij.clicked.connect(self.show_emoji)
        self.btn_color.clicked.connect(self.open_color)
        self.btn_echo.clicked.connect(self.show_filerecv)
        self.pushButton.clicked.connect(self.open_user)
        self.btn_sent.setShortcut("Return")
        self.user.setText("用户名:"+name)
        self.color = QtGui.QColor("#87CEFA")
        self.color_string = self.color.name()
        self.names = name
        self.Login()
        self.show()
    def Exit(self):#结束进程，退出
        try:
            self.SendStr("prom"+self.color_string+f"用户:{self.names}退出聊天")
            self.isRun = False
            if self.server:
                self.server.shutdown(socket.SHUT_RDWR)
                self.server.close()
            if self.recv_thread.is_alive():
                self.recv_thread.join()
            sys.exit()
        except Exception as e:
            logging.error(f"Error closing client:{e}")
    def Login(self):#连接到服务端
        self.open_file_recv()
        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        host = socket.gethostname()
        port = 50500
        try:
            self.server.connect((host,port))
            self.MaxSize = 10240
            self.recv_thread = threading.Thread(target=self.recv)#启用线程接受信息
            self.recv_thread.start()
            self.show_information("连接成功")
            self.SendStr("name"+self.color_string+f"用户:{self.names}连接成功")
        except Exception as e:
            logging.error(f"Unable to connect to serverr:{e}")
        self.isRun = True
    def SendStr(self,text):#发送字符串类型信息
        if text != "info":
            try:
                self.server.sendall(text.encode("utf-8"))
            except Exception as e:
                logging.error(f"Client sending information error:{e}")
    def SendByte(self,byte):#发送字节流信息
        if byte is not None:
            try:
                self.server.sendall(byte)
            except Exception as e:
                logging.error(f"Client sending information error:{e}")
    def recv(self):#循环监听接受信息
        while self.isRun:
            try:
                data = self.server.recv(self.MaxSize)
                if not data:
                    break
                else:
                    '''定义三种格式的信息 info::普通信息,meoj::表情信息,prom::提示信息'''
                    '''文件发送格式info+#FFFFFF+message'''
                    self.update.emit(data)
            except Exception as e:
                logging.error(f"Client receiving information error:{e}")
                break
    def recv_information(self,data):#当收到信息后会出发update信号，从而调用此函数，对信息解码，分析
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
        logging.info(f"Client successfully received informatioin:{message}")
        if type_mseeage == "info":
            self.other_sent(message,color=self.colors)
        elif type_mseeage == "emoj":
            self.other_sent_emoj(message)
        elif type_mseeage == "prom":
            self.show_information(message)
        elif type_mseeage == "file":
            length = len(type_mseeage.encode("utf-8"))+len(type_color.encode("utf-8"))
            filedata = data[length:]
            self.recv_file(filedata)
        elif type_mseeage == "fina":
            self.recv_file_name(message)
            '''此处可能报错，导致程序崩溃'''
            # self.event.clear()
            # self.event.wait()
        else:
            logging.error("")
    def getlist(self):#获取用户列表
        with open("userlist.csv",'r',newline='',encoding='utf-8') as f:
            if len(f.read()) != 0:
                f.seek(0)
                t = csv.reader(f)
                l = list(t)
                return l[0]
            else:
                return []
    def recv_file_name(self,message):#接受文件名
        self.file_name = message
        self.uis.file_name.append(self.file_name)
        self.uis.file_save_path.append(self.path)
    def recv_file(self,message):#接受文件数据
        if message !="":
            with open(self.path+self.file_name,'ab') as file:
                file.write(message)
    def sent_file(self,name,path):
        if not os.path.isfile(path):#发送文件
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
    def client_close(self):#退出聊天
        username = self.user.text()
        self.names = username[4:]
        chose = QMessageBox.question(None,"提示","您确定要退出聊天吗？",QMessageBox.Yes|QMessageBox.No)
        if chose==QMessageBox.Yes:
            color = QtGui.QColor("white")
            cursor = self.information.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            back_format = QtGui.QTextBlockFormat()
            back_format.setAlignment(QtCore.Qt.AlignCenter)
            cursor.mergeBlockFormat(back_format)
            cursor.insertText("===用户"+self.names+"退出聊天===")
            format = cursor.charFormat()
            format.setBackground(color)
            cursor.setPosition(cursor.position()-len(username)-8,QtGui.QTextCursor.KeepAnchor)
            cursor.setCharFormat(format)
            self.information.setTextCursor(cursor)
            '''当用户登出后获取用户列表，并删除该用户，同时更新文件'''
            self.list = self.getlist()
            if self.names in self.list:
                index = self.list.index(self.names)
                del self.list[index]
            '''更新文件'''
            with open("userlist.csv","w",newline='',encoding='utf-8') as t:
                t.write("")
                t.seek(0)
                for user in self.list:
                    if user !="":
                        t.write(user+',')
            self.Exit()
            QtCore.QTimer.singleShot(2000,sys.exit)
        else:
            return 0
    def sent_with_background(self,text,color=QtGui.QColor("#87CEFA")):#在send_information函数中调用，用来给文本设置背景
        username = self.user.text()
        self.color = color
        self.names = username[4:]
        cursor = self.information.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        back_format = QtGui.QTextBlockFormat()
        back_format.setAlignment(QtCore.Qt.AlignRight)
        cursor.mergeBlockFormat(back_format)
        if text !="":
            cursor.insertText(text+" :"+self.names+"\n")
            format = cursor.charFormat()
            format.setBackground(self.color)
            cursor.setPosition(cursor.position()-len(self.names)-3-len(text),QtGui.QTextCursor.KeepAnchor)
            cursor.setCharFormat(format)
        self.information.setTextCursor(cursor)
    def sent_information(self,who="all"):#发送函数，用于向自己窗口显示数据，同时需要将信息发送过去,默认向所有人发送
        text = self.input.text()
        self.input.clear()
        self.sent_with_background(text,self.color)
        self.SendStr("info"+self.color_string+text)
    def other_sent(self,text,username="admin",color=QtGui.QColor("#A2e322")):#获取对方发送的信息,送到聊天框，左对齐
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
    def other_sent_emoj(self,text,color=QtGui.QColor("#87CEFA")):#获取对方发送表情，左对齐
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
    def open_file(self):#打开文件选择框
        file_dialog = QFileDialog
        file_path ,_ = file_dialog.getOpenFileName()
        if file_path:
            file_name = os.path.basename(file_path)
            self.sent_file(file_name,file_path)
    def show_emoji(self):#打开表情托盘
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
    def open_color(self):#打开颜色选择器
        co = QColorDialog.getColor()
        self.color = QtGui.QColor(co.name())
        self.color_string = self.color.name()
    def open_user(self):#显示在线用户
        li = self.getlist()
        str = " ".join(li)
        self.show_information("在线用户")
        self.show_information(str)
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
