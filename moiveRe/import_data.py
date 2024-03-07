import os
import sys
import django

# 设置环境变量，指向你的Django项目的settings模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moiveRe.settings')

# 配置Django
django.setup()



import csv
from datetime import datetime
from django.db import models
from moiveReApp.models import Question
csv_file_path = 'mod_data.csv'
questions_to_create = []
with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
    csv_reader = csv.DictReader(csv_file)

    for row in csv_reader:
        question = Question(
            question_text=row['Title'],
            img_url=row['Image URL'],
            category=row['Category'],
            link=row['Link'],
            detail=row['Description'],
            pub_date=datetime.now(),
        )
        questions_to_create.append(question)

Question.objects.bulk_create(questions_to_create)

print("Data imported successfully")
