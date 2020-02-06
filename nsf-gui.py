import os
import re
import sys
import tkinter
from tkinter import messagebox, ttk

import xlwings as xl

VERSION = "v1.0"

# 检查环境
if getattr(sys, 'frozen', False):  # 运行于 |PyInstaller| 二进制环境
    basedir = sys._MEIPASS # pylint: disable=no-member
else:  # 运行于一般Python 环境
    basedir = os.path.dirname(__file__)

#TODO: 检测当前打开的工作簿:app.selection


#Tools Function
def name_formatter(nameList: list, number=2):
    """
    在两个字的名字中间加两个空格，返回经过处理的列表。列表中三个字的名字不会被处理。

    nameList: 一个包含待处理名字的列表

    示例：
    IN: ['张三', '李四', '王老五']
    OUT: ['张三', '李  四', '王老五']
    """
    r = []
    for i in nameList:
        if isinstance(i, str) and len(i) == 2:
            i = i[0] + ' ' * number + i[1]
        r.append(i)
    return r


#TODO: A Function to remove all space
def remove_all_space(nameList: list):
    "Return a list without any space"
    r = []
    for i in nameList:
        if isinstance(i, str):
            i = i.replace(' ', '')
        r.append(i)
    return r


class Application(tkinter.Frame):
    def __init__(self, master=None):
        #init vars
        self.rangeText = tkinter.StringVar()
        self.currentBook = tkinter.StringVar()
        self.currentSheet = tkinter.StringVar()
        #init settings vars
        self.transposeBool = tkinter.BooleanVar(value=True)
        self.bypassRegExCheck = tkinter.BooleanVar(value=False)

        #INIT FUNCTIONS
        super().__init__(master)
        self.master = master
        self.grid()
        self.createWidget()
        self.refreshExcelState()

    def createWidget(self):
        #Fathers
        self.pW = ttk.PanedWindow(orient=tkinter.VERTICAL)
        self.statusLF = ttk.LabelFrame(self.pW, text='状态')
        self.settingsLF = ttk.LabelFrame(self.pW, text='参数设置')
        self.pW.add(self.statusLF)
        self.pW.add(self.settingsLF)
        self.pW.grid(column=0, row=0, columnspan=3)
        #CurrentBook
        self.l2 = ttk.Label(self.statusLF, text='当前工作簿：')
        self.l2.grid(column=0, columnspan=1, row=0)
        self.bookLabel = ttk.Label(self.statusLF,
                                   textvariable=self.currentBook)
        self.bookLabel.grid(column=1, columnspan=3, row=0, sticky='w')
        #CurrentSheet
        self.l3 = ttk.Label(self.statusLF, text='当前工作表：')
        self.l3.grid(column=0, columnspan=1, row=1)
        self.sheetLabel = ttk.Label(self.statusLF,
                                    textvariable=self.currentSheet)
        self.sheetLabel.grid(column=1, columnspan=3, row=1, sticky='w')

        #Settings
        self.descriptionLabel = ttk.Label(self.settingsLF,
                                          text='高级设置，建议保持默认，谨慎修改。')
        self.descriptionLabel.grid(column=0, row=0, columnspan=2)
        self.transposeCBox = ttk.Checkbutton(self.settingsLF,
                                             text='垂直写入（Transpose）',
                                             variable=self.transposeBool)
        self.transposeCBox.grid(row=1)
        self.bypassRegExCheckBtn = ttk.Checkbutton(
            self.settingsLF, text='跳过正则表达式检查', variable=self.bypassRegExCheck)
        self.bypassRegExCheckBtn.grid(column=1, row=1)

        #Command
        self.l1 = ttk.Label(text="输入待处理单元格范围（例：A1:A10）:")
        self.l1.grid(column=0, columnspan=1, row=1, padx=5, sticky=tkinter.E)
        self.e1 = ttk.Entry(textvariable=self.rangeText)
        self.e1.grid(column=1, columnspan=2, row=1, pady=5, sticky=tkinter.W)
        self.refreshBtn = ttk.Button(text='刷新', command=self.refreshExcelState)
        self.refreshBtn.grid(column=0, row=2, padx=5, sticky='w')
        self.btn1 = ttk.Button(text='人名添加空格', command=self.doFormatJobs)
        self.btn1.grid(column=2, row=2, padx=3, pady=5)
        self.removeSpaceBtn = ttk.Button(text='删除空格',
                                         command=self.removeAllSpace)
        self.removeSpaceBtn.grid(column=1, row=2, sticky='e')

    @staticmethod
    def checkRangeText(rText):
        "Check the Range text as A1:A10, return bool"
        regex = re.compile('[A-Z][0-9]*:[A-Z][0-9]*')
        result = regex.match(rText)
        if result:
            return True
        else:
            return False

    def getExcelRange(self):
        "Get current range, return None if have problem"
        rT = self.rangeText.get()
        if not self.bypassRegExCheck.get() and not self.checkRangeText(rT):
            messagebox.showerror('rangeText Error', '单元格范围格式不正确')
            return None
        try:
            sR = xl.Range(rT).options(transpose=self.transposeBool.get())
        except AttributeError:
            messagebox.showerror('AttributeError', '无法获取当前工作簿，请检查Excel是否正在运行？')
            raise
        return sR

    def replaceRangeValue(self, target: xl.Range, out):
        origin = target.value
        exeBool = messagebox.askyesno(
            '执行确认', f'IN: {origin}\nOUT: {out}\n是否写入？此操作无法撤销', icon='question')
        if exeBool:
            target.value = out
            messagebox.showinfo('Successful?', '写入完成，请至Excel中查看效果。')
            xl.apps.active.activate(steal_focus=True)

    def doFormatJobs(self):
        targetRange = self.getExcelRange()
        if targetRange == None:
            return
        rST = name_formatter(targetRange.value)
        self.replaceRangeValue(targetRange, rST)

    def removeAllSpace(self):
        targetRange = self.getExcelRange()
        if targetRange == None:
            return
        nL = targetRange.value
        result = remove_all_space(nL)
        self.replaceRangeValue(targetRange, result)

    def refreshExcelState(self):
        try:
            self.currentBook.set(xl.books.active.name)
            self.currentSheet.set(xl.books.active.sheets.active.name)
        except AttributeError:
            messagebox.showerror('ERROR', '无法检测到打开的工作簿，请检查Excel是否正在运行？')


#INIT
root = tkinter.Tk()

# set ICON
root.iconbitmap(os.path.join(basedir, 'icon.ico'))

root.title(F"Excel 单元格人名空格补齐实用程序 {VERSION}")
root.resizable(False, False)
app = Application(root)
app.mainloop()
