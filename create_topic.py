# 随机生成伪题库
import os
import random
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image, ImageDraw, ImageFont

cwd = os.path.join(os.getcwd(), '题库')


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


conn = sqlite3.connect('data.db')
cursor = conn.cursor()
sql = "SELECT * FROM topic_label_table WHERE label_code like ?"
topic_type_list = []
result = cursor.execute(sql, ('ZAB%',))
for res in result:
    topic_type_list.append(res[0])
print(topic_type_list)
topic_difficulty_list = []
result = cursor.execute(sql, ('ZBB%',))
for res in result:
    topic_difficulty_list.append(res[0])
print(topic_difficulty_list)
topic_from_list = []
result = cursor.execute(sql, ('ZBA%',))
for res in result:
    topic_from_list.append(res[0])
print(topic_from_list)
point_list = []
sql = "SELECT label_code From point_label_table"
result = cursor.execute(sql, ())
for res in result:
    point_list.append(res[0])
print(point_list)
sql = "SELECT label_code From point_label_table"
result = cursor.execute(sql, ())
for res in result:
    point_list.append(res[0])
print(point_list)


def work(_):
    local_random = random.Random()
    name = local_random.choice(point_list) + ',' + local_random.choice(topic_type_list) + ',' + local_random.choice(
        topic_difficulty_list) + ',' + local_random.choice(topic_from_list)
    create_topic(name)


# 多线程加速
with ThreadPoolExecutor(max_workers=20) as executor:  # max_workers指定了线程池中的线程数量
    futures = [executor.submit(work, i) for i in range(20000)]
    for future in as_completed(futures):
        try:
            future.result()
        except Exception as e:
            print("Error:", e)
# 单线程
# for i in range(5):
#     name = random.choice(point_list) + ',' + random.choice(topic_type_list) + ',' + random.choice(
#         topic_difficulty_list) + ',' + random.choice(topic_from_list)
#     create_topic(name)
