
import torch
from transformers import DistilBertTokenizer, DistilBertModel
from sklearn.metrics.pairwise import cosine_similarity
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


from moiveReApp.models import UserProfile,Question
from django.contrib.auth.models import User


user = User.objects.get(username='gly233')
user_profile = UserProfile.get_user_profile(user)
question_list = Question.objects.all()




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


            # 返回排序后的物品ID列表
            return recommendations

user_item_matrix, item_dict, user_dict = itemcf.build_user_item_matrix(question_list)
item_similarity_matrix = itemcf.calculate_user_similarity(user_item_matrix)
r1 = itemcf.generate_recommendations(user.id, item_similarity_matrix, user_item_matrix, user_dict, item_dict, k=30)[:10]


class hotitem():


    def recall_hot_item(question_list,k):
        sorted_question_list = sorted(question_list, key=lambda q: q.likes, reverse=True)
        recommendations = [question.id for question in sorted_question_list]
        return recommendations[:k]

r2 = hotitem.recall_hot_item(question_list,10)

class newitem():

    def recall_new_item(question_list,k):
        sorted_question_list = sorted(question_list, key=lambda q: q.pub_date, reverse=True)
        recommendations = [question.id for question in sorted_question_list]
        return recommendations[:k]

r3 = newitem.recall_new_item(question_list,10)


class U2TAG2I():



    def compute_interest_score(user_profile, questions):
        interest_scores = {}
        user_interests = set(user_profile.interests.all())
        user_interests_names = [interest.name for interest in user_interests]
        #print(user_interests_names)
        for question in questions:
            if  question.category in user_interests_names:
                interest_scores[question.id] = 0.3
            else:
                interest_scores[question.id] = 0

        return interest_scores

    def compute_similarity(user_profile, questions):
        tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
        model = DistilBertModel.from_pretrained('distilbert-base-uncased')
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)

        user_interests_str = ' '.join([interest.name for interest in user_profile.interests.all()])

        question_details = [question.detail for question in questions]
        num_questions = len(question_details)
        question_ids = [question.id for question in questions]
        question_score = []
        #print(question_ids)
        question_details.append(user_interests_str)
        texts = question_details



        inputs = tokenizer(texts, return_tensors='pt', padding=True, truncation=True)

        # 将张量移动到GPU上
        input_ids = inputs['input_ids'].to(device)
        attention_mask = inputs['attention_mask'].to(device)
        # 使用DistilBERT模型进行推理
        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state

        # 将文本表示向量转移到CPU上
        text_embeddings = outputs.mean(dim=1).cpu().numpy()

        # 计算相似度
        for i in range(num_questions):
                similarity = cosine_similarity([text_embeddings[i]], [text_embeddings[-1]])[0][0]
                question_score.append(similarity*0.7)

        # 使用 zip() 函数合并两个列表成元组列表
        combined = list(zip(question_ids, question_score))
        # 将元组列表转换为字典
        interest_score = dict(combined)

        return interest_score

    def generate_recommendations(score1,score2,k):
            result_dict = {}
            for key in score1:
                if key in score2:
                    result_dict[key] = score1[key] + score2[key]

            sorted_items = sorted(result_dict.items(), key=lambda x: x[1], reverse=True)
            top_k = sorted_items[:k]
            return top_k



a=U2TAG2I.compute_interest_score(user_profile,questions=question_list)
b=U2TAG2I.compute_similarity(user_profile,questions=question_list)

r4 = U2TAG2I.generate_recommendations(a,b,10)



print(r1)
print(r2)
print(r3)
print(r4)













