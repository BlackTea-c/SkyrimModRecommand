import os
import sys
import django
import numpy as np


# Set up the Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moiveRe.settings')
django.setup()
from moiveReApp.models import Question, User


import numpy as np

def user_cf_recommendation(user_item_matrix, target_user_index, similarity_matrix, k=5):
    """
    用户协同过滤推荐算法

    参数:
    - user_item_matrix: 2D numpy数组，表示用户-物品交互矩阵
    - target_user_index: 目标用户的索引，用于生成推荐
    - similarity_matrix: 2D numpy数组，表示用户相似性矩阵
    - k: 考虑的邻居数量，默认为5

    返回:
    - recommended_items: 推荐给目标用户的物品索引列表
    """

    # 步骤1: 寻找邻居
    neighbors = find_neighbors(target_user_index, similarity_matrix, k)

    # 步骤2: 生成推荐
    recommended_items = generate_recommendations(target_user_index, user_item_matrix, neighbors)

    return recommended_items

def find_neighbors(target_user_index, similarity_matrix, k):
    """
    根据相似性矩阵找到目标用户的前k个邻居

    参数:
    - target_user_index: 目标用户的索引
    - similarity_matrix: 2D numpy数组，表示用户相似性矩阵
    - k: 考虑的邻居数量

    返回:
    - neighbors: 前k个邻居的索引列表
    """

    # 获取目标用户的相似性分数
    target_user_similarity = similarity_matrix[target_user_index]

    # 根据相似性分数降序排列用户
    sorted_users = np.argsort(target_user_similarity)[::-1]

    # 排除目标用户，获取前k个邻居
    neighbors = [user for user in sorted_users if user != target_user_index][:k]

    return neighbors

def generate_recommendations(target_user_index, user_item_matrix, neighbors):
    """
    根据邻居的喜好为目标用户生成物品推荐

    参数:
    - target_user_index: 目标用户的索引
    - user_item_matrix: 2D numpy数组，表示用户-物品交互矩阵
    - neighbors: 邻居的索引列表

    返回:
    - recommended_items: 推荐给目标用户的物品索引列表
    """

    # 找到目标用户尚未互动过的物品
    unrated_items = np.where(user_item_matrix[target_user_index] == 0)[0]

    # 预测目标用户对未互动过物品的兴趣
    predicted_preferences = np.sum(user_item_matrix[neighbors][:, unrated_items], axis=0)

    # 根据预测兴趣降序排列物品
    recommended_items = [item for item in np.argsort(predicted_preferences)[::-1]]

    return recommended_items

# 示例用法
user_item_matrix = np.array([[1, 0, 3, 0, 2],
                             [4, 0, 0, 5, 0],
                             [0, 0, 0, 0, 1],
                             [2, 0, 1, 0, 0]])

# 假设相似性矩阵已经预先计算
similarity_matrix = np.array([[1, 0.2, 0.4, 0.1],
                              [0.2, 1, 0.3, 0.6],
                              [0.4, 0.3, 1, 0.5],
                              [0.1, 0.6, 0.5, 1]])

目标用户索引 = 0
k_neighbors = 2

推荐结果 = user_cf_recommendation(user_item_matrix, 目标用户索引, similarity_matrix, k_neighbors)
print("用户{}的推荐结果: {}".format(目标用户索引, 推荐结果))
