import os
import shutil
import sqlite3

cwd = os.path.join(os.getcwd(), '题库')
topic_save_path = os.path.join(os.getcwd(), '分类题库')
point_save_path = None


def generate_file_id():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    sql = 'select count(*) from topic_recode_table'
    cursor.execute(sql, )
    return str(cursor.fetchall()[0][0] + 1).zfill(8)


def record_point_and_topic(src_path):
    path1 = src_path.replace('，', ',')
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    # 分离标签
    label_list = os.path.basename(path1).split('.')[0].split(',')
    label_list = [label.strip() for label in label_list]
    label_list = [label[0:6] if len(label) > 6 else label for label in label_list]
    topic_label_list = []  # 题库+档案库标签编码
    point_label_list = []  # 知识点编码
    label_type = []  # 知识点or题库
    page = None  # 页码
    point_data_dict = {'唯一标识': None, '资料类型': None, '一级标签': None, '二级标签': None, '三级标签': None,
                       '四级标签': None, '五级标签': None, '六级标签': None, '资料来源': None, '页码': None}  # 知识点数据字典
    topic_data_dict = {'唯一标识': None, '一级标签': None, '二级标签': None, '三级标签': None, '四级标签': None,
                       '五级标签': None, '六级标签': None, '分类训练题类型': None, '套卷类型': None, '题型(小项)': None,
                       '题型(细项)': None, '题目出题逻辑': None, '题目难度': None, '题目考频': None,
                       '是否解法不唯一': '否', '题目属性题目来源': None, '资料来源': None, '页码': None}  # 题目数据字典
    id = generate_file_id()
    # 一个文件的所有标签解析
    for label in label_list:
        if len(label) < 3: continue
        # 题目类型
        if label[0] == 'Z':
            # 类型解析
            if label[0:3] == 'ZBA':
                label_type.append(label + '6' * (6 - len(label)))
            # 页码解析
            elif label[0:2] == 'ZP':
                # topic_label_list.append('ZP')
                # 直接记录页码
                if len(label) == 5:
                    page = label[2:5]
            else:
                topic_label_list.append(label + '6' * (6 - len(label)))
        # 知识点
        elif label[0] >= 'A' and label[0] <= 'G':
            point_label_list.append(label + '6' * (6 - len(label)))
    sql1 = 'select distinct label_1_name from point_label_table where label_1_code = ?'  # 查一级标签
    sql2 = 'select distinct label_2_name from point_label_table where label_1_code = ? and label_2_code = ?'  # 查二级标签
    sql3 = 'select distinct label_3_name from point_label_table where label_1_code = ? and label_2_code = ? and label_3_code = ?'  # 查三级标签
    sql4 = 'select distinct label_4_name from point_label_table where label_1_code = ? and label_2_code = ? and label_3_code = ? and label_4_code = ?'  # 查四级标签
    sql5 = 'select distinct label_5_name from point_label_table where label_1_code = ? and label_2_code = ? and label_3_code = ? and label_4_code = ? and label_5_code = ?'  # 查五级标签
    sql6 = 'select distinct label_6_name from point_label_table where label_1_code = ? and label_2_code = ? and label_3_code = ? and label_4_code = ? and label_5_code = ? and label_6_code = ?'  # 查六级标签
    sql_list = [sql1, sql2, sql3, sql4, sql5, sql6]
    key_list = ['一级标签', '二级标签', '三级标签', '四级标签', '五级标签', '六级标签']
    # 知识点
    if len(label_type) > 0 and label_type[0][0:3] == 'ZCA':
        sql = 'select point_id from point_recode_table where point_id = ?'
        cursor.execute(sql, (id,))
        if len(cursor.fetchall()) > 0:
            print('已存在知识点')
            return
        # 处理知识点
        print('知识点录入')
        point_data_dict['唯一标识'] = id
        sql = 'select label_major_name,label_minor_name,label_detail_name from topic_label_table where label_code = ?'
        cursor.execute(sql, (label_type[0],))
        point_data_dict['资料类型'] = '-'.join(cursor.fetchall()[0])
        # 知识点标签检索
        code_list = []
        for i, code in enumerate(point_label_list[0]):
            if code == '6':
                break  # 无内容，终止
            else:
                code_list.append(code)
                cursor.execute(sql_list[i], code_list)
                result = cursor.fetchall()
                # print(result[0][0])
                point_data_dict[key_list[i]] = result[0][0]
        # 资料来源
        for label in label_list:
            if label[0:2] == 'ZE':
                cursor.execute(sql, (label,))
                point_data_dict['资料来源'] = '-'.join(cursor.fetchall()[0])
        # 页码
        point_data_dict['页码'] = page
        # 存储路径记录并将文件复制到指定存储位置
        save_dir = point_save_path + '\\' + point_label_list[0][0] + '-' + point_data_dict['一级标签'][-2:]
        save_name = point_data_dict['唯一标识'] + ',' + ",".join(label_list) + ".png"
        point_data_dict['存储路径'] = os.path.join(save_dir, save_name)
        # 记录到数据库
        sql = 'insert into point_recode_table(point_id,point_code,first_label,second_label,third_label,fourth_label,fifth_label,sixth_label,point_type,point_from,page,save_path) values(?,?,?,?,?,?,?,?,?,?,?,?)'
        cursor.execute(sql, (
            point_data_dict['唯一标识'], point_label_list[0], point_data_dict['一级标签'],
            point_data_dict['二级标签'], point_data_dict['三级标签'], point_data_dict['四级标签'],
            point_data_dict['五级标签'], point_data_dict['六级标签'], point_data_dict['资料类型'],
            point_data_dict['资料来源'], point_data_dict['页码'], point_data_dict['存储路径']))
        conn.commit()
        shutil.copy(src_path, point_data_dict['存储路径'])
    # 题库
    if len(label_type) > 0 and label_type[0][0:3] == 'ZBA':
        sql = 'select topic_id from topic_recode_table where topic_id = ?'
        cursor.execute(sql, (id,))
        if len(cursor.fetchall()) > 0:
            print('已存在题目')
            return
        topic_data_dict['唯一标识'] = id
        # 记录题目类型
        for i in range(len(label_type)):
            sql = 'select label_major_name,label_minor_name,label_detail_name from topic_label_table where label_code = ?'
            cursor.execute(sql, (label_type[i],))

            if label_type[i][0:4] == 'ZCBA':
                topic_data_dict['分类训练题类型'] = cursor.fetchall()[0][-1]
            if label_type[i][0:4] == 'ZCBB':
                topic_data_dict['套卷类型'] = cursor.fetchall()[0][-1]
            # 题目属性题目来源
            if label_type[i][0:3] == 'ZBA':
                topic_data_dict['题目属性题目来源'] = cursor.fetchall()[0][-1]
        # 资料来源
        for label in label_list:
            if label[0:2] == 'ZE':
                cursor.execute(sql, (label,))
                topic_data_dict['资料来源'] = '-'.join(cursor.fetchall()[0])
        # 页码
        point_data_dict['页码'] = page
        # 记录题目题目属性信息
        for label in topic_label_list:
            # 题型
            if label[0:2] == 'ZA':
                sql = 'select label_minor_name,label_detail_name from topic_label_table where label_code = ?'
                cursor.execute(sql, (label,))
                result = cursor.fetchall()[0]
                topic_data_dict['题型(小项)'] = result[0]
                topic_data_dict['题型(细项)'] = result[1]
            # 题目出题逻辑
            if label[0:4] == 'ZBAA':
                sql = 'select label_detail_name from topic_label_table where label_code = ?'
                cursor.execute(sql, (label,))
                result = cursor.fetchall()[0]
                topic_data_dict['题目出题逻辑'] = result[0]
            # 题目难度
            if label[0:3] == 'ZBB':
                sql = 'select label_detail_name from topic_label_table where label_code = ?'
                cursor.execute(sql, (label,))
                result = cursor.fetchall()[0]
                topic_data_dict['题目难度'] = result[0]
            # 题目考频
            if label[0:3] == 'ZBC':
                sql = 'select label_detail_name from topic_label_table where label_code = ?'
                cursor.execute(sql, (label,))
                result = cursor.fetchall()[0]
                topic_data_dict['题目考频'] = result[0]
            # 是否解法不唯一
            if label[0:3] == 'ZBD':
                sql = 'select label_detail_name from topic_label_table where label_code = ?'
                cursor.execute(sql, (label,))
                result = cursor.fetchall()[0]
                topic_data_dict['是否解法不唯一'] = result[0]
        # 记录知识点信息
        for index in range(len(point_label_list)):
            code_list = []
            for i, code in enumerate(point_label_list[index]):
                if code == '6':
                    break  # 无内容，终止
                else:
                    code_list.append(code)
                    cursor.execute(sql_list[i], code_list)
                    result = cursor.fetchall()
                    print(result[0][0])
                    topic_data_dict[key_list[i]] = result[0][0]
            # 存储路径记录并将文件复制到指定存储位置
            save_dir = topic_save_path + '\\' + point_label_list[0][0] + '-' + topic_data_dict['一级标签'][-2:]
            save_name = topic_data_dict['唯一标识'] + ',' + ",".join(label_list) + ".png"
            topic_data_dict['存储路径'] = os.path.join(save_dir, save_name)
            sql = 'insert into topic_recode_table(topic_id,point_code,first_label,second_label,third_label,fourth_label,fifth_label,sixth_label,train_topic_type,exam_type,topic_minor_type,topic_detail_type,logic,dificulty,frequency,method_num,topic_source,topic_from,page,save_path) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
            cursor.execute(sql, (
                topic_data_dict['唯一标识'], point_label_list[index], topic_data_dict['一级标签'],
                topic_data_dict['二级标签'], topic_data_dict['三级标签'], topic_data_dict['四级标签'],
                topic_data_dict['五级标签'], topic_data_dict['六级标签'], topic_data_dict['分类训练题类型'],
                topic_data_dict['套卷类型'], topic_data_dict['题型(小项)'], topic_data_dict['题型(细项)'],
                topic_data_dict['题目出题逻辑'], topic_data_dict['题目难度'], topic_data_dict['题目考频'],
                topic_data_dict['是否解法不唯一'], topic_data_dict['题目属性题目来源'], topic_data_dict['资料来源'],
                topic_data_dict['页码'], topic_data_dict['存储路径'],))
            conn.commit()
        shutil.copy(os.path.join(cwd, src_path), topic_data_dict['存储路径'])


path = os.path.join(os.getcwd(), '题库')
topic_list = os.listdir(path)
for topic in topic_list:
    record_point_and_topic(topic)
