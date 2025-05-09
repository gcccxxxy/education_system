# 随机生成学生做的试题
import os
import random
import sqlite3
from datetime import datetime, timedelta

from PIL import Image, ImageDraw, ImageFont

cwd = os.path.join(os.getcwd(), '学生做题信息')


# 创建题目
def create_topic(topic_name):
    # 创建一个新的白色背景图片
    image = Image.new('RGB', (512, 512), color=(255, 255, 255))
    # 创建一个可以在给定图像上绘图的对象
    draw = ImageDraw.Draw(image)
    # 设置字体和大小（需要事先安装字体，例如arial.ttf）
    font = ImageFont.truetype("arial.ttf", 30)
    # 在图片上写文字
    draw.text((10, 10), topic_name, fill=(0, 0, 0), font=font)
    # 保存图片
    save_path = os.path.join(cwd, topic_name + '.png')
    i = 1
    while os.path.exists(save_path):
        save_path = os.path.join(cwd, topic_name + f'({i}).png')
        i = i + 1
    image.save(save_path)


topic_type_list = []
topic_difficulty_list = []
point_list = []
exam_hard_list = []
exam_topic_type = []
correct_list = ['全对', '半对', '全错']
error_list = ['审题不认真', '忽略了情况', '低级差错', '没想起对应的知识点', '知识点对应错误', '知识点记忆差错',
              '题目理解错误', '想不到解题思路']

cwd = os.path.join(os.getcwd(), '学生做题信息')
conn = sqlite3.connect('data.db')
cursor = conn.cursor()
sql = "SELECT label_detail_name FROM topic_label_table WHERE label_code like ?"

result = cursor.execute(sql, ('ZAB%',))
for res in result:
    topic_type_list.append(res[0])
print(topic_type_list)

result = cursor.execute(sql, ('ZBB%',))
for res in result:
    topic_difficulty_list.append(res[0])
print(topic_difficulty_list)

sql = "SELECT label_code From point_label_table"
result = cursor.execute(sql, ())
for res in result:
    point_list.append(res[0])
print(point_list)
topic_type = 'ZCBBA6'

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
print(exam_hard_list)

for i in range(0, 10):
    exam_topic_type.append(topic_type_list[0])
for i in range(10, 16):
    exam_topic_type.append(topic_type_list[1])
exam_topic_type.append(topic_type_list[3])
for i in range(17, 26):
    exam_topic_type.append(topic_type_list[5])
print(exam_topic_type)
# 正确率
xiaoA_easy = [90, 5, 5]
xiaoA_medium = [65, 15, 20]
xiaoA_hard = [25, 35, 40]
xiaoA_easy_error = [33, 33, 33, 0.25, 0.25, 0.25, 0.25, 0]
xiaoA_medium_error = [25, 25, 25, 5, 5, 5, 5, 5]
xiaoA_hard_error = [5, 15, 5, 15, 5, 5, 5, 50]

xiaoB_easy = [60, 30, 10]
xiaoB_medium = [30, 50, 20]
xiaoB_hard = [0, 25, 75]
xiaoB_easy_error = [20, 20, 20, 10, 10, 10, 5, 5]
xiaoB_medium_error = [15, 15, 15, 15, 10, 10, 10, 10]
xiaoB_hard_error = [1, 1, 1, 5, 5, 2, 5, 80]

xiaoC_easy = [20, 30, 50]
xiaoC_medium = [10, 40, 50]
xiaoC_hard = [0, 10, 90]
xiaoC_easy_error = [10, 10, 10, 10, 10, 10, 20, 20]
xiaoC_medium_error = [2, 3, 5, 20, 20, 10, 10, 40]
xiaoC_hard_error = [1, 1, 1, 5, 5, 2, 5, 80]


def create_student_exam(easy, medium, hard, easy_error, medium_error, hard_error, exam_id, time, student_name):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    sql = 'select label_code from topic_label_table where label_detail_name = ?'
    exam_list = []
    for i in range(26):
        topic = {'student_name': student_name, 'id': str(i).zfill(7), 'topic_type': exam_topic_type[i],
                 'difficulty': exam_hard_list[i], 'label_code': random.choice(point_list), 'error_type': None}
        sql1 = 'select label_1_name,label_2_name,label_3_name,label_4_name,label_5_name from point_label_table where label_code = ?'
        cursor.execute(sql1, (topic['label_code'],))
        result = cursor.fetchone()
        topic['first_label'], topic['second_label'], topic['third_label'], topic['forth_label'], topic['fifth_label'] = \
            result[0], result[1], result[2], result[3], result[4]
        # 根据难度模拟正确情况
        if topic['difficulty'] in ['难度1', '难度2', '难度3']:
            wei = easy if topic['topic_type'] not in ['单选题', '填空题'] else [
                easy[0] + easy[1], 0, easy[2]]
        elif topic['difficulty'] in ['难度3', '难度4', '难度5', '难度6']:
            wei = medium if topic['topic_type'] not in ['单选题', '填空题'] else [
                medium[0] + medium[1], 0, medium[2]]
        else:
            wei = hard if topic['topic_type'] not in ['单选题', '填空题'] else [
                hard[0] + hard[1], 0, hard[2]]
        topic['correct'] = random.choices(correct_list, weights=wei)[0]
        # 根据难度、正确情况模拟错误原因
        if topic['correct'] in ['半对', '全错']:
            if topic['difficulty'] in ['难度1', '难度2', '难度3']:
                wei = easy_error
            elif topic['difficulty'] in ['难度3', '难度4', '难度5', '难度6']:
                wei = medium_error
            else:
                wei = hard_error
            topic['error_type'] = random.choices(error_list, weights=wei)[0]
        exam_list.append(topic)
        cursor.execute(sql, (topic['difficulty'],))
        result = cursor.fetchone()
        diff_code = result[0]
        cursor.execute(sql, (topic['topic_type'],))
        result = cursor.fetchone()
        type_code = result[0]
        id = ','.join([exam_id + topic['id'], diff_code, type_code, topic['label_code']])
        create_topic(id)
        sql2 = 'insert into student_topic_table(student_name,exam_type,id,correct,error_type,time,topic_type,difficulty,label_code,first_label,second_label,third_label,forth_label,fifth_label) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
        cursor.execute(sql2, (
            topic['student_name'], '训练卷', exam_id + topic['id'], topic['correct'], topic['error_type'], time,
            topic['topic_type'], topic['difficulty'], topic['label_code'], topic['first_label'], topic['second_label'],
            topic['third_label'], topic['forth_label'], topic['fifth_label']))
        conn.commit()
    return exam_list


start_date = datetime.strptime("20240401", "%Y%m%d")
for i in range(60, 74):
    current_date = start_date + timedelta((i-60) * 30)
    current_date = current_date.strftime("%Y%m%d")
    create_student_exam(xiaoC_easy, xiaoC_medium, xiaoC_hard, xiaoC_easy_error, xiaoC_medium_error, xiaoC_hard_error,
                        'ex00' + str(i).zfill(2), current_date, 'XiaoC')
