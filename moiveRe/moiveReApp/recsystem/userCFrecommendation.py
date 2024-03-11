import os
import sys
import django
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class usercf():

  def build_user_item_matrix(self,question_list):
    """
    根据物品-用户倒排表构建用户-物品交互矩阵

    参数:
    - question_list: QuerySet，包含所有问题的列表

    返回:
    - user_item_matrix: 2D numpy数组，表示用户-物品交互矩阵
    - item_dict: 字典，将物品ID映射到索引
    - user_dict: 字典，将用户ID映射到索引
    """

    # 获取所有用户的ID和物品的ID
    all_users = set()
    all_items = set()

    for question in question_list:
        item_id = question.id
        liked_users = question.liked_by.all()

        all_users.update(user.id for user in liked_users)
        all_items.add(item_id)

    # 创建物品-用户的倒排表
    item_user_dict = {}
    for question in question_list:
        item_id = question.id
        liked_users = set(user.id for user in question.liked_by.all())
        item_user_dict[item_id] = liked_users

    # 创建物品相似性矩阵
    num_items = len(all_items)
    num_users = len(all_users)

    # 建立物品ID到索引的映射
    item_dict = {item_id: index for index, item_id in enumerate(all_items)}

    # 建立用户ID到索引的映射
    user_dict = {user_id: index for index, user_id in enumerate(all_users)}

    # 初始化用户-物品交互矩阵
    user_item_matrix = np.zeros((num_users, num_items))

    for item_id, liked_users in item_user_dict.items():
        item_index = item_dict[item_id]

        for user_id in liked_users:
            user_index = user_dict[user_id]
            user_item_matrix[user_index, item_index] = 1  # 表示用户喜欢该物品

    return user_item_matrix, item_dict, user_dict
  def calculate_user_similarity(self,user_item_matrix):
    # 计算用户相似度矩阵
    user_similarity_matrix = cosine_similarity(user_item_matrix)
    np.fill_diagonal(user_similarity_matrix, 0)
    return user_similarity_matrix
  def generate_recommendations(self,target_user, user_similarity_matrix, user_item_matrix, user_dict, item_dict, k):
    """
    为目标用户生成推荐列表

    参数:
    - target_user: 字符串，目标用户的名称
    - user_similarity_matrix: 2D numpy数组，表示用户相似度矩阵
    - user_item_matrix: 2D numpy数组，表示用户-物品交互矩阵
    - user_dict: 字典，将用户映射到索引
    - item_dict: 字典，将物品ID映射到索引
    - k: 整数，选择最相似的前K个用户

    返回:
    - recommendations: 列表，包含按感兴趣程度排序的物品ID
    """

    # 获取目标用户的索引
    target_user_index = user_dict.get(target_user)
    if target_user_index is None:
        raise ValueError(f"目标用户 '{target_user}' 不存在。")

    # 获取目标用户未交互的物品
    target_user_interactions = user_item_matrix[target_user_index]

    # 初始化推荐列表
    recommendations = []

    # 获取与目标用户最相似的前K个用户的索引
    similar_user_indices = np.argsort(user_similarity_matrix[target_user_index])[::-1][:k]

    # 遍历每个物品，计算目标用户对未交互物品的感兴趣程度
    for item_id, item_index in item_dict.items():
        if not target_user_interactions[item_index]:
            # 目标用户未交互过该物品
            interest_score = 0

            # 计算目标用户对该物品的感兴趣程度
            for similar_user_index in similar_user_indices:
                if user_item_matrix[similar_user_index, item_index] == 1:
                    # 该相似用户交互过该物品
                    similarity_score = user_similarity_matrix[target_user_index, similar_user_index]
                    interest_score += similarity_score

            recommendations.append((item_id, interest_score))

    # 根据感兴趣程度排序推荐列表
    recommendations.sort(key=lambda x: x[1], reverse=True)

    # 返回排序后的物品ID列表
    return [item_id for item_id, _ in recommendations]



