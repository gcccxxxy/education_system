from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QTreeWidgetItem

from analyse_function import *
from main import Ui_Form as Main_Window
from tab1 import Ui_Form as Tab1_Window
from tab2 import Ui_Form as Tab2_Window

# 在主函数入口之前加入上面的设置即可解决
QGuiApplication.setAttribute(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

database = 'data.db'
sql_label_list = ['label_1_name', 'label_2_name', 'label_3_name', 'label_4_name', 'label_5_name', 'label_6_name']
diff_list = ['所有', '难度1', '难度2', '难度3', '难度4', '难度5', '难度6', '难度7', '难度8', '难度9', '难度10']
topic_type = ['选择题', '填空题', '解答题', '积累与运用', '阅读理解', '写作', '听力', '完形填空', '情景交际',
              '看图写话', '短文填词', '书面表达', '作图题', '简答题', '实验题', '计算题', '应用题', '材料分析题',
              '判断题', '论述题']


def is_strict_integer(s):
    """严格判断是否为整数（不允许正负号以外的符号）"""
    s = s.strip()
    return s.isdigit() or (s.startswith(('-', '+')) and s[1:].isdigit())


def node_get_full_path(node):
    current_dir = node.text(0)
    full_path = current_dir
    parent = node.parent()
    while parent is not None:
        full_path = parent.text(0) + '-' + full_path
        current_item = parent
        parent = current_item.parent()
    return full_path


class Tab1Window(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.InitUI()
        self.font = QFont()
        self.font.setFamily("Arial")  # 设置字体名称
        self.font.setPointSize(10)  # 设置字体大小
        self.font.setBold(True)  # 设置字体为粗体
        self.ui.textEdit.setFont(self.font)

    def InitUI(self, current_item=None):
        self.ui = Tab1_Window()
        self.ui.setupUi(self)
        self.current_item = current_item
        # 难度下拉框
        self.ui.comboBox.myadditems(diff_list)
        # 查询学力
        self.ui.pushButton.clicked.connect(self.analyse)
        # 生成试卷
        self.ui.pushButton_2.clicked.connect(self.create_exam)

    def analyse(self):
        student_name = self.ui.textEdit.toPlainText()
        point = self.ui.textBrowser.toPlainText()
        hard_list = self.ui.comboBox.currentText()
        if len(student_name) == 0:
            QMessageBox.critical(self.parent, '错误', '请输入学生姓名', QMessageBox.Ok)
            return
        if len(hard_list) == 0:
            QMessageBox.critical(self.parent, '错误', '请选择难度', QMessageBox.Ok)
            return
        topic_num, correct_num = query_topic_and_correct_number(student_name, hard_list, point)
        try:
            correct_per = str(correct_num / topic_num * 100)[:5] + '%'
        except:
            correct_per = '0' + '%'
        study_ability = '缺少数据' if topic_num == 0 else calculate_ablility(student_name, hard_list, point)
        self.ui.textBrowser_4.setText('\n' + str(topic_num))
        self.ui.textBrowser_4.setFont(self.font)
        self.ui.textBrowser_2.setText('\n' + correct_per)
        self.ui.textBrowser_2.setFont(self.font)
        self.ui.textBrowser_3.setText('\n' + str(study_ability))
        self.ui.textBrowser_3.setFont(self.font)

    def create_exam(self):
        student_name = self.ui.textEdit.toPlainText()
        if len(student_name) == 0:
            QMessageBox.critical(self.parent, '错误', '请输入学生姓名', QMessageBox.Ok)
            return
        create_exam(student_name, True)
        QMessageBox.information(self.parent, "成功", "试卷生成成功", QMessageBox.Ok)


class Tab2Window(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.InitUI()
        self.font = QFont()
        self.font.setFamily("Arial")  # 设置字体名称
        self.font.setPointSize(10)  # 设置字体大小
        self.font.setBold(True)  # 设置字体为粗体
        self.ui.textEdit.setFont(self.font)

    def InitUI(self, current_item=None):
        self.ui = Tab2_Window()
        self.ui.setupUi(self)
        # 难度下拉框
        self.ui.comboBox.myadditems(diff_list)
        # 题型下拉框
        self.ui.comboBox_2.myadditems(topic_type)
        self.ui.pushButton.clicked.connect(self.add_row)
        # 右键菜单
        self.ui.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tableWidget.customContextMenuRequested.connect(self.show_context_menu)
        self.ui.pushButton_3.clicked.connect(self.clearall)
        self.ui.pushButton_2.clicked.connect(self.create_topic)

    def add_row(self):
        point = self.ui.textBrowser.toPlainText()
        difficulty = self.ui.comboBox.currentText()
        type = self.ui.comboBox_2.currentText()
        topic_num = self.ui.textEdit.toPlainText()
        if len(point) == 0:
            QMessageBox.critical(self.parent, '错误', '请选择知识点', QMessageBox.Ok)
            return
        if len(difficulty) == 0:
            QMessageBox.critical(self.parent, '错误', '请选择难度', QMessageBox.Ok)
            return
        if len(type) == 0:
            QMessageBox.critical(self.parent, '错误', '请选择题型', QMessageBox.Ok)
            return
        if len(type.split('; ')) > 1:
            QMessageBox.critical(self.parent, '错误', '只能选择一种题型', QMessageBox.Ok)
            return
        if len(topic_num) == 0:
            QMessageBox.critical(self.parent, '错误', '请输入题目数量', QMessageBox.Ok)
            return
        if not is_strict_integer(topic_num):
            QMessageBox.critical(self.parent, '错误', '请输入正确的数字', QMessageBox.Ok)
            return
        # 获取当前行数，作为新行的索引
        row_position = self.ui.tableWidget.rowCount()
        # 插入新行
        self.ui.tableWidget.insertRow(row_position)
        data = (point, difficulty, type, topic_num)
        # 设置行数据
        for col, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignCenter)
            self.ui.tableWidget.setItem(row_position, col, item)

    # 右键菜单
    def show_context_menu(self, position):
        # 获取当前选中的行
        index = self.ui.tableWidget.verticalHeader().logicalIndexAt(position)
        if index != -1:
            # 自动选择一整行
            self.ui.tableWidget.selectRow(index)
            # 创建一个右键菜单
            menu = QMenu(self)
            # 添加一个删除行的动作
            delete_action = QAction("删除", self)
            delete_action.triggered.connect(lambda: self.delete_row(index))
            menu.addAction(delete_action)
            # 显示右键菜单
            menu.exec_(self.ui.tableWidget.mapToGlobal(position))

    # 删除
    def delete_row(self, row_index):
        self.ui.tableWidget.removeRow(row_index)
        QMessageBox.information(self, '成功', '删除成功', QMessageBox.Ok)

    # 清空所有
    def clearall(self):
        while self.ui.tableWidget.rowCount() > 0:
            self.ui.tableWidget.removeRow(0)  # 从顶部开始删除行，这样可以避免改变索引的问题
        self.ui.textEdit.clear()
        self.ui.textBrowser.clear()
        self.ui.comboBox.text.clear()
        for checkbox in self.ui.comboBox.box_list:
            checkbox.setChecked(False)
        self.ui.comboBox_2.text.clear()
        self.ui.comboBox_2.text.clear()
        for checkbox in self.ui.comboBox_2.box_list:
            checkbox.setChecked(False)

    def create_topic(self):
        data = []
        row_count = self.ui.tableWidget.rowCount()
        col_count = self.ui.tableWidget.columnCount()
        for row in range(row_count):
            row_data = []
            for col in range(col_count):
                item = self.ui.tableWidget.item(row, col)
                # 检查单元格是否为空
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append('')  # 空单元格添加空字符串
            data.append(row_data)
        topic_point_list, topic_hard_list, topic_type_list, topic_num_list = [], [], [], []
        for item in data:
            topic_point_list.append(item[0])
            topic_hard_list.append(item[1])
            topic_type_list.append(item[2])
            topic_num_list.append(item[3])
        res = create_exam(None, False, topic_point_list, topic_hard_list, topic_type_list, topic_num_list)
        if res != 1:
            QMessageBox.critical(self.parent, '错误', res + ' 题库题目数量不足', QMessageBox.Ok)
        else:
            QMessageBox.information(self, '成功', '生成成功', QMessageBox.Ok)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Main_Window()
        self.ui.setupUi(self)
        self.setWindowTitle("星悦学橙")
        self.conn = sqlite3.connect('data.db')
        self.cursor = self.conn.cursor()
        self.tree = self.ui.treeWidget
        self.tree.setHeaderLabels(['知识点'])
        # 设置根节点
        self.root = QTreeWidgetItem(self.tree)
        self.root.setText(0, '初中数学')
        # self.tree.itemDoubleClicked.connect(self.on_item_clicked)
        # 设置列宽
        self.tree.setColumnWidth(0, 150)
        # 为tree增加顶级项目
        self.tree.addTopLevelItem(self.root)
        # tree展开
        self.traverse_tree(self.root)

        self.first_page = Tab1Window(self)
        self.second_page = Tab2Window(self)
        layout = QHBoxLayout()
        layout.addWidget(self.first_page)
        self.ui.tab.setLayout(layout)
        layout = QHBoxLayout()
        layout.addWidget(self.second_page)
        self.ui.tab_2.setLayout(layout)
        self.ui.treeWidget.currentItemChanged.connect(self.refresh_tree)
        self.ui.tabWidget.setCurrentIndex(0)
        self.setFixedSize(952, 661)  # 设置固定大小
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)  # 禁止最大化和最小化，保留关闭按钮

    # 判断是第几级标签
    def cal_level(self, node):
        level = 0
        parent = node.parent()
        while parent is not None:
            current_item = parent
            parent = current_item.parent()
            level += 1
        return level

    # 直接递归算法获取所有树节点
    def traverse_tree(self, item):
        child_list = []
        # sql = 'select distinct label_2_name from point_label_table where label_1_name = \'初中数学\''
        level = self.cal_level(item)  # 判断标签等级
        if level == 5:
            return  # 最后一级
        else:
            sql = 'select distinct {} from point_label_table where {} = ?'.format(sql_label_list[level + 1],
                                                                                  sql_label_list[level])
            self.cursor.execute(sql, (item.text(0),))
            result = self.cursor.fetchall()
            for res in result:
                if res[0] is not None:
                    child_list.append(res[0])
            for child_dir in child_list:
                child = QTreeWidgetItem(item)
                child.setText(0, child_dir)
                self.traverse_tree(child)

    def refresh_tree(self):
        current_index = self.ui.tabWidget.currentIndex()
        self.ui.tabWidget.setCurrentIndex(current_index)
        if current_index == 0:
            self.ui.tab.close()
            point_name = node_get_full_path(self.tree.currentItem())
            self.first_page.ui.textBrowser.setText(point_name)
            self.first_page.ui.textBrowser.setFont(self.first_page.font)
            self.first_page.ui.textBrowser_4.clear()
            self.first_page.ui.textBrowser_3.clear()
            self.first_page.ui.textBrowser_2.clear()
            self.ui.tab.show()
        elif current_index == 1:
            self.ui.tab_2.close()
            point_name = node_get_full_path(self.tree.currentItem())
            self.second_page.ui.textBrowser.setText(point_name)
            self.second_page.ui.textBrowser.setFont(self.second_page.font)
            self.ui.tab_2.show()


if __name__ == "__main__":
    app = QApplication([])  # 先建立一个app
    wid = MainWindow()  # 初始化一个对象，调用init函数，已加载设计的ui文件
    wid.show()  # 显示ui
    app.exec_()  # 执行app（运行界面，响应按钮等操作）
