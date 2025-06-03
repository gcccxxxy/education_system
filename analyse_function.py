import os
import random
import shutil
import sqlite3
from datetime import datetime

conn = sqlite3.connect('data.db')
cursor = conn.cursor()
cwd = os.path.join(os.getcwd(), '千人千卷')

ERROR_PENALTY = {
    '低级错误': 0.5,
    '答题书写不规范被扣分': 0.5,
    '其他错误': 0.4,
    '知识点记忆差错': 3,
    '解题思路差错': 1.8
}

# 时间衰减参数（指数衰减）
DECAY_FACTOR = 0.003  # 调整衰减系数增强近期权重

# 当前日期（来自系统信息）
CURRENT_DATE = datetime(2025, 4, 23)
# 知识点标签等级
level_list = ['first_label', 'second_label', 'third_label', 'fourth_label', 'fifth_label']


def query_topic_and_correct_number(student_name, hard_list_str, point):
    point_split_list = point.split('-')
    level = len(point_split_list)
    hard_list = hard_list_str.replace(' ', '')
    hard_list = hard_list.split(';')
    for i in range(len(hard_list)):
        hard_list[i] = '\'' + hard_list[i] + '\''
    hard_list = ','.join(hard_list)
    sql = 'select count(*) from student_topic_table where student_name = ? and difficulty in ({}) and {} = ?'.format(
        hard_list, level_list[level - 1])
    cursor.execute(sql, (student_name, point_split_list[-1],))
    result = cursor.fetchall()
    topic_num = result[0][0]
    sql = 'select count(*) from student_topic_table where student_name = ? and difficulty in ({}) and {} = ? and correct = {}'.format(
        hard_list, level_list[level - 1], '\'全对\'')
    cursor.execute(sql, (student_name, point_split_list[-1],))
    result = cursor.fetchall()
    correct_num = result[0][0]
    return topic_num, correct_num


def safe_date_parse(date_str):
    """安全解析日期，处理异常情况"""
    try:
        return datetime.strptime(date_str, '%Y%m%d')
    except:
        return None


def calculate_ablility(student_name, hard_list_str, point):
    level_list = ['first_label', 'second_label', 'third_label', 'forth_label', 'fifth_label']
    point_split_list = point.split('-')
    level = len(point_split_list)
    hard_list = hard_list_str.replace(' ', '')
    hard_list = hard_list.split(';')
    for i in range(len(hard_list)):
        hard_list[i] = '\'' + hard_list[i] + '\''
    hard_list = ','.join(hard_list)
    sql = """
        SELECT student_name,{},
               correct,
               difficulty,
               error_type,
               time
        FROM student_topic_table
        WHERE student_name = ? and difficulty in ({}) and {} = ?
        """.format(level_list[level - 1], hard_list, level_list[level - 1])
    cursor.execute(sql, (student_name, point_split_list[-1],))
    records = cursor.fetchall()
    print(records)
    total = 0.0
    max_possible = 0.0
    for record in records:
        student, knowledge, correct, diff_str, error, time_str = record
        difficulty = int(diff_str.replace('难度', ''))  # 提取难度值

        # 安全处理日期
        answer_date = safe_date_parse(time_str)
        if not answer_date:
            weight = 0.8  # 默认权重调整为0.8
        else:
            try:
                days_ago = (CURRENT_DATE - answer_date).days
                if days_ago < 0:
                    # 未来日期使用反向衰减（越远的未来权重越高）
                    weight = 1 / (1 + abs(days_ago)) ** DECAY_FACTOR
                else:
                    weight = 1 / (1 + days_ago) ** DECAY_FACTOR
                weight = max(0.2, min(weight, 1.0))  # 限制权重范围0.2-1.0
            except:
                weight = 0.8  # 兜底处理

        # 基础分计算（强化全对奖励）
        if correct == '全对':
            base_score = difficulty * 1.8  # 奖励系数提升至1.5
        elif correct == '半对':
            base_score = difficulty * 0.8
        else:
            base_score = 0.0

        # 错误扣分（优化非错误情况处理）
        penalty = ERROR_PENALTY.get(error, 0.2) if error else 0.0

        # 最终得分（增加非负限制）
        final_score = max(0.0, (base_score - penalty)) * weight

        total += final_score
        # 最大可能得分（假设全对且无错误）
        max_possible += difficulty * 1.5 * weight  # 匹配奖励系数

    # 生成结果并归一化到1-10分
    if max_possible == 0:
        mastery = 1.0
    else:
        raw_score = total / max_possible
        # 分段线性归一化（更直观的评分机制）
        if raw_score >= 0.9:
            mastery = 9 + (raw_score - 0.9) * 10
        elif raw_score >= 0.7:
            mastery = 7 + (raw_score - 0.7) * 10
        elif raw_score >= 0.5:
            mastery = 5 + (raw_score - 0.5) * 10
        else:
            mastery = 1 + raw_score * 4
        mastery = round(max(1.0, min(10.0, mastery)), 1)
    # 按学生和掌握程度排序输出
    return mastery


def calculate_ablility_dic():
    query = """
        SELECT student_name,
               COALESCE(fifth_label, forth_label, third_label) AS knowledge_point,
               correct,
               difficulty,
               error_type,
               time
        FROM student_topic_table
        WHERE knowledge_point IS NOT NULL  -- 过滤无知识点记录
        """

    # 获取最细粒度知识点（优先使用第五级）
    cursor.execute(query)
    records = cursor.fetchall()

    # 学生-知识点统计字典
    stats = {}

    for record in records:
        student, knowledge, correct, diff_str, error, time_str = record
        difficulty = int(diff_str.replace('难度', ''))  # 提取难度值

        # 安全处理日期
        answer_date = safe_date_parse(time_str)
        if not answer_date:
            weight = 0.8  # 默认权重调整为0.8
        else:
            try:
                days_ago = (CURRENT_DATE - answer_date).days
                if days_ago < 0:
                    # 未来日期使用反向衰减（越远的未来权重越高）
                    weight = 1 / (1 + abs(days_ago)) ** DECAY_FACTOR
                else:
                    weight = 1 / (1 + days_ago) ** DECAY_FACTOR
                weight = max(0.2, min(weight, 1.0))  # 限制权重范围0.2-1.0
            except:
                weight = 0.8  # 兜底处理

        # 基础分计算（强化全对奖励）
        if correct == '全对':
            base_score = difficulty * 1.8  # 奖励系数提升至1.5
        elif correct == '半对':
            base_score = difficulty * 0.8
        else:
            base_score = 0.0

        # 错误扣分（优化非错误情况处理）
        penalty = ERROR_PENALTY.get(error, 0.2) if error else 0.0

        # 最终得分（增加非负限制）
        final_score = max(0.0, (base_score - penalty)) * weight

        # 累计统计
        key = (student, knowledge)
        if key not in stats:
            stats[key] = {'total': 0.0, 'max_possible': 0.0}

        stats[key]['total'] += final_score
        # 最大可能得分（假设全对且无错误）
        stats[key]['max_possible'] += difficulty * 1.5 * weight  # 匹配奖励系数

    # 生成结果并归一化到1-10分
    results = {}
    for (student, knowledge), data in stats.items():
        if data['max_possible'] == 0:
            mastery = 1.0
        else:
            raw_score = data['total'] / data['max_possible']
            # 分段线性归一化（更直观的评分机制）
            if raw_score >= 0.9:
                mastery = 9 + (raw_score - 0.9) * 10
            elif raw_score >= 0.7:
                mastery = 7 + (raw_score - 0.7) * 10
            elif raw_score >= 0.5:
                mastery = 5 + (raw_score - 0.5) * 10
            else:
                mastery = 1 + raw_score * 4
            mastery = round(max(1.0, min(10.0, mastery)), 1)
        if student not in results.keys():
            results[student] = {}
        results[student][knowledge] = mastery
    return results


def create_exam_function(student_name, mastery_dic):
    topic_type_list = []
    topic_difficulty_list = []
    exam_hard_list = []
    exam_topic_type = []
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    sql = "SELECT label_detail_name FROM topic_label_table WHERE label_code like ?"

    result = cursor.execute(sql, ('ZAB%',))
    for res in result:
        topic_type_list.append(res[0])
    # print(topic_type_list)

    result = cursor.execute(sql, ('ZBB%',))
    for res in result:
        topic_difficulty_list.append(res[0])
    for i in range(0, 3):
        exam_hard_list.append(topic_difficulty_list[random.choice([0, 1, 2])])
    for i in range(3, 6):
        exam_hard_list.append(topic_difficulty_list[random.choice([1, 2, 3])])
    for i in range(6, 9):
        exam_hard_list.append(topic_difficulty_list[random.choice([3, 4, 5])])
    exam_hard_list.append(topic_difficulty_list[random.choice([7, 8, 9])])
    for i in range(10, 13):
        exam_hard_list.append(topic_difficulty_list[random.choice([0, 1, 2, 3])])
    exam_hard_list.append(topic_difficulty_list[random.choice([4, 5, 6])])
    exam_hard_list.append(topic_difficulty_list[random.choice([4, 5, 6])])
    exam_hard_list.append(topic_difficulty_list[random.choice([7, 8, 9])])
    for i in range(16, 19):
        exam_hard_list.append(topic_difficulty_list[random.choice([1, 2, 3])])
    for i in range(19, 24):
        exam_hard_list.append(topic_difficulty_list[random.choice([3, 4, 5, 6])])
    exam_hard_list.append(topic_difficulty_list[random.choice([7, 8, 9])])
    exam_hard_list.append(topic_difficulty_list[random.choice([8, 9])])
    # print(exam_hard_list)
    for i in range(0, 10):
        exam_topic_type.append(topic_type_list[0])
    for i in range(10, 16):
        exam_topic_type.append(topic_type_list[1])
    exam_topic_type.append(topic_type_list[3])
    for i in range(17, 26):
        exam_topic_type.append(topic_type_list[5])
    # print(exam_topic_type)
    # print(mastery_dic['XiaoC'])
    exam_topic_id_list = []
    num = 0
    for difficulty in exam_hard_list:
        difficulty = int(difficulty.replace('难度', ''))  # 提取难度值
        sub_point_list = []
        for point in mastery_dic[student_name].keys():
            if difficulty > mastery_dic[student_name][point]:
                sub_point_list.append((point, mastery_dic[student_name][point]))
        if len(sub_point_list) == 0:
            difficulty += 1
            while len(sub_point_list) == 0 and difficulty < 11:
                for point in mastery_dic[student_name].keys():
                    if difficulty > mastery_dic[student_name][point]:
                        sub_point_list.append((point, mastery_dic[student_name][point]))
                if len(sub_point_list) == 0:
                    difficulty += 1
                else:
                    break
        # # 根据难度选择备选出题知识点，条件是掌握程度与难度相差小于1，若没有则降难度(掌握较差)
        # while len(sub_point_list) == 0 and difficulty > 0:
        #     for point in mastery_dic[student_name].keys():
        #         if 0 <= difficulty - mastery_dic[student_name][point] <= 1:
        #             sub_point_list.append((point, mastery_dic[student_name][point]))
        #     if len(sub_point_list) == 0:
        #         difficulty -= 1
        #     else:
        #         break
        # # 根据难度选择备选出题知识点，条件是掌握程度与难度相差小于1，若没有则升难度（掌握较好）
        # while len(sub_point_list) == 0 and difficulty < 11:
        #     for point in mastery_dic[student_name].keys():
        #         if 0 <= difficulty - mastery_dic[student_name][point] <= 1:
        #             sub_point_list.append((point, mastery_dic[student_name][point]))
        #     if len(sub_point_list) == 0:
        #         difficulty += 1
        #     else:
        #         break
        sub_point_list.sort(key=lambda x: x[1], reverse=True)
        # 随机选择知识点
        flag = False
        while not flag:
            point = random.choice(sub_point_list)[0]
            sql = 'select * from topic_recode_table where dificulty = ? and (fourth_label = ? or fifth_label = ?) and topic_detail_type = ?'
            cursor.execute(sql, ('难度' + str(difficulty), point, point, exam_topic_type[num],))
            result = cursor.fetchall()
            if len(result) > 0:
                exam_topic_id_list.append(random.choice(result))
                flag = True
        num += 1
    # 获取当前时间
    now = datetime.now()
    # 将当前时间格式化为 "%Y%m%d%H%M%S"
    formatted_time = now.strftime("%Y%m%d%H%M%S")
    os.makedirs(os.path.join(cwd, student_name, formatted_time))
    for i, topic in enumerate(exam_topic_id_list):
        shutil.copy(cwd[0] + topic[-1][1:], os.path.join(cwd, student_name, formatted_time, str(i + 1) + '.png'))


def create_topic(topic_point_list, topic_hard_list, topic_type_list, topic_num_list, from_list=None):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    return_list = []
    for index in range(len(topic_point_list)):
        # 知识点
        topic_point_temp = topic_point_list[index].split('-')
        point_level = len(topic_point_temp)
        topic_point_level = level_list[point_level - 1]
        topic_point = '\'' + topic_point_temp[-1] + '\''
        # 难度
        hard_list = topic_hard_list[index].replace(' ', '')
        hard_list = hard_list.split(';')
        for i in range(len(hard_list)):
            hard_list[i] = '\'' + hard_list[i] + '\''
        hard_list = ','.join(hard_list)
        # 题型
        type_list = topic_type_list[index].replace(' ', '')
        type_list = type_list.split(';')
        for i in range(len(type_list)):
            type_list[i] = '\'' + type_list[i] + '\''
        type_list = ','.join(type_list)
        # 题数
        topic_num = topic_num_list[index]
        sql = 'select * from topic_recode_table where {} = {} and dificulty in ({}) and topic_detail_type in ({}) ORDER BY RANDOM() LIMIT {}'.format(
            topic_point_level, topic_point, hard_list, type_list, topic_num)
        cursor.execute(sql, )
        result = cursor.fetchall()
        if len(result) < int(topic_num):
            return topic_point
        for item in result:
            return_list.append(item)
    # 获取当前时间
    now = datetime.now()
    # 将当前时间格式化为 "%Y%m%d%H%M%S"
    formatted_time = now.strftime("%Y%m%d%H%M%S")
    os.makedirs(os.path.join(cwd, '自建题目', formatted_time))
    for i, topic in enumerate(return_list):
        shutil.copy(cwd[0] + topic[-1][1:], os.path.join(cwd, '自建题目', formatted_time, str(i + 1) + '.png'))
    return 1


def create_exam(student_name, auto, topic_point_list=None, topic_hard_list=None, topic_type_list=None,
                topic_num_list=None):
    if auto is True:
        dic = calculate_ablility_dic()
        create_exam_function(student_name, dic)
    else:
        return create_topic(topic_point_list, topic_hard_list, topic_type_list, topic_num_list)


if __name__ == "__main__":
    print(calculate_ablility_dic())
