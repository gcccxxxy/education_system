from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QTreeWidgetItem

from analyse import *
from main import Ui_Form as Main_Window
from tab1 import Ui_Form as Tab1_Window

database = 'data.db'
sql_label_list = ['label_1_name', 'label_2_name', 'label_3_name', 'label_4_name', 'label_5_name', 'label_6_name']
diff_list = ['所有', '难度1', '难度2', '难度3', '难度4', '难度5', '难度6', '难度7', '难度8', '难度9', '难度10']


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
        mastery_dic, mastery_dic1, mastery_dic2, mastery_dic3 = calculate_1234mastery()
        self.dic_list = [mastery_dic3, mastery_dic2, mastery_dic1, mastery_dic]
        print(self.dic_list)

    def InitUI(self, current_item=None):
        self.ui = Tab1_Window()
        self.ui.setupUi(self)
        self.current_item = current_item
        # 难度下拉框
        self.ui.comboBox.myadditems(diff_list)
        # 查询学力
        self.ui.pushButton.clicked.connect(self.analyse)

    def analyse(self):
        level_list = ['first_label', 'second_label', 'third_label', 'forth_label', 'fifth_label']
        student_name = self.ui.textEdit.toPlainText()
        point = self.ui.textBrowser.toPlainText()
        hard_list = self.ui.comboBox.currentText()
        if len(student_name) == 0:
            QMessageBox.critical(self.parent, '错误', '请输入学生姓名', QMessageBox.Ok)
            return
        if len(hard_list) == 0:
            QMessageBox.critical(self.parent, '错误', '请选择难度', QMessageBox.Ok)
            return
        hard_list = hard_list.replace(' ', '')
        hard_list = hard_list.split(';')
        for i in range(len(hard_list)):
            hard_list[i] = '\'' + hard_list[i] + '\''
        hard_list = ','.join(hard_list)
        point_split_list = point.split('-')
        level = len(point_split_list)
        # 做题数
        sql = 'select count(*) from student_topic_table where student_name = ? and difficulty in ({}) and {} = ?'.format(
            hard_list, level_list[level - 1])
        self.parent.cursor.execute(sql, (student_name, point_split_list[-1],))
        result = self.parent.cursor.fetchall()
        topic_num = result[0][0]
        # 正确题数
        sql = 'select count(*) from student_topic_table where student_name = ? and difficulty in ({}) and {} = ? and correct = {}'.format(
            hard_list, level_list[level - 1], '\'全对\'')
        self.parent.cursor.execute(sql, (student_name, point_split_list[-1],))
        result = self.parent.cursor.fetchall()
        correct_num = result[0][0]
        try:
            correct_per = str(correct_num / topic_num * 100)[:5] + '%'
        except:
            correct_per = '0' + '%'
        study_ability = '缺少数据'
        if point_split_list[-1] in self.dic_list[min(3, level - 1)][student_name].keys():
            study_ability = self.dic_list[min(3, level - 1)][student_name][point_split_list[-1]]
        self.ui.textBrowser_4.setText('\n' + str(topic_num))
        self.ui.textBrowser_4.setFont(self.font)
        self.ui.textBrowser_2.setText('\n' + correct_per)
        self.ui.textBrowser_2.setFont(self.font)
        self.ui.textBrowser_3.setText('\n'+str(study_ability))
        self.ui.textBrowser_3.setFont(self.font)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Main_Window()
        self.ui.setupUi(self)
        self.setWindowTitle("星途优学")
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
        layout = QHBoxLayout()
        layout.addWidget(self.first_page)
        self.ui.tab.setLayout(layout)
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
            pass
            # self.ui.tab_2.close()
            # self.second_page.InitUI(self.tree.currentItem())
            # self.ui.tab_2.show()


if __name__ == "__main__":
    app = QApplication([])  # 先建立一个app
    wid = MainWindow()  # 初始化一个对象，调用init函数，已加载设计的ui文件
    wid.show()  # 显示ui
    app.exec_()  # 执行app（运行界面，响应按钮等操作）
