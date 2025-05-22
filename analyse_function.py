import sqlite3
from datetime import datetime

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

# 错误类型扣分规则（优化权重）
ERROR_PENALTY = {
    '知识点对应错误': 2.5,
    '审题不认真': 0.7,
    '低级差错': 0.4,
    '忽略了情况': 1.0,
    '题目理解错误': 2.0,
    '知识点记忆差错': 1.8,
    '想不到解题思路': 3.0,
    '没想起对应的知识点': 2.8
}

# 时间衰减参数（指数衰减）
DECAY_FACTOR = 0.003  # 调整衰减系数增强近期权重

# 当前日期（来自系统信息）
CURRENT_DATE = datetime(2025, 4, 23)


def query_topic_and_correct_number(student_name, hard_list_str, point):
    level_list = ['first_label', 'second_label', 'third_label', 'forth_label', 'fifth_label']
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


def create_exam(student_name, mastery_dic, auto, topic_type_list=None, topic_difficulty_list=None, exam_hard_list=None,
                exam_topic_type=None):
    if auto is True:
        pass


if __name__ == "__main__":
    print(calculate_ablility_dic())
