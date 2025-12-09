import openpyxl
from openpyxl import Workbook

class ExcelUtil:

    def __init__(self, file_path=None):
        if file_path:
            wb = openpyxl.load_workbook(file_path)
        else:
            # 创建一个Workbook对象，这相当于创建一个Excel文件
            wb = Workbook()
        # 激活当前工作表
        self.ws = wb.active
        self.wb = wb

    def save_excel(self,path_name):
        # 保存Excel文件
        self.wb.save(path_name)


    def append_excel(self,data):
        self.ws.append(data)



