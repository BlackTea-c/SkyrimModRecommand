import random
import string

from django.db import transaction
import os

import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moiveRe.settings")  # 替换 "yourproject.settings" 为你的项目的 settings 模块路径
django.setup()

from django.contrib.auth.models import User
from moiveReApp.models import Question

# 设置需要创建的用户数量和每个用户随机点赞的次数
num_users = 50
max_likes_per_user = 70

def generate_random_username():
    return ''.join(random.choices(string.digits, k=6))

@transaction.atomic
def create_users_and_likes():
    # 创建用户
    users = []
    for i in range(num_users):
        username = generate_random_username()
        email = f'{username}@example.com'
        password = 'woshihapi123'
        user = User.objects.create_user(username=username, email=email, password=password)
        users.append(user)

    # 为每个问题随机点赞
    questions = Question.objects.all()
    for user in users:
        liked_questions = random.sample(list(questions), min(max_likes_per_user, len(questions)))
        for question in liked_questions:
            question.likes += 1
            question.liked_by.add(user)
            question.save()

if __name__ == "__main__":
    create_users_and_likes()
