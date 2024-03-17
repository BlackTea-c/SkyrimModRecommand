

import django
from django.conf import settings
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moiveRe.settings")  # 替换 "yourproject.settings" 为你的项目的 settings 模块路径
django.setup()

from moiveReApp.models import UserExperience


# 兴趣标签集合
experience_tags = [
    'NewtoGame','Middle','Experienced'
]

# 将标签添加到数据库中
for tag_name in experience_tags:
    tag, created = UserExperience.objects.get_or_create(name=tag_name)

    # 如果标签是新创建的，则打印一条消息
    if created:
        print(f'Created tag: {tag_name}')
    else:
        print(f'Tag already exists: {tag_name}')