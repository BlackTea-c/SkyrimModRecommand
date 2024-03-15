

import django
from django.conf import settings
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moiveRe.settings")  # 替换 "yourproject.settings" 为你的项目的 settings 模块路径
django.setup()

from moiveReApp.models import Question
import numpy as np
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity



class itemcf():

    def build_user_item_matrix(question_list):
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

        return user_item_matrix, item_dict, user_dict  #转置一下就是倒排。。

    def calculate_user_similarity(user_item_matrix):
        # 计算物品相似度矩阵
        item_similarity_matrix = cosine_similarity(user_item_matrix.T) #转置才是物品-用户表
        np.fill_diagonal(item_similarity_matrix, 0)
        return item_similarity_matrix

    def generate_recommendations(target_user, item_similarity_matrix, user_item_matrix, user_dict, item_dict, k):


        # 获取目标用户的索引
            target_user_index = user_dict.get(target_user)
            if target_user_index is None:
               raise ValueError(f"目标用户 '{target_user}' 不存在。")

            # 获取目标用户(未)交互的物品
            target_user_interactions = user_item_matrix[target_user_index]

            # 初始化推荐列表
            recommendations = []


            # 遍历每个物品，计算目标用户对未交互物品的感兴趣程度
            for item_id, item_index in item_dict.items():
                if not target_user_interactions[item_index]:
                    # 目标用户未交互过该物品
                    interest_score = 0
                    # 获取与目标物品最相似的前K个物品的索引
                    similar_item_indices = np.argsort(item_similarity_matrix[item_index])[::-1][:k]

                    # 计算目标用户对该物品的感兴趣程度
                    for similar_item_index in similar_item_indices:
                        if user_item_matrix[target_user_index, similar_item_index] == 1:
                            # 用户u交互过该物品,此即为N(u)∩S（j,k）
                            similarity_score = item_similarity_matrix[item_index, similar_item_index]
                            interest_score += similarity_score

                    recommendations.append((item_id, interest_score))

            # 根据感兴趣程度排序推荐列表
            recommendations.sort(key=lambda x: x[1], reverse=True)
            print(recommendations)


            # 返回排序后的物品ID列表
            return [item_id for item_id, _ in recommendations]


class hotitem():


    def recall_hot_item(question_list,k):
        sorted_question_list = sorted(question_list, key=lambda q: q.likes, reverse=True)

        return sorted_question_list[:k]










