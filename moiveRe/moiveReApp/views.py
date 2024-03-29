# Create your views here.
from django.views import generic
from .forms import RatingForm
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from .models import Question, Rating ,UserProfile,Userinterests
import random
from django.contrib.auth.decorators import login_required
#from recsystem.userCFrecommendation import usercf
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import math
from collections import Counter
import torch
from transformers import DistilBertTokenizer, DistilBertModel
import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
import torch
from deepctr_torch.models import DeepFM
from deepctr_torch.inputs import SparseFeat, DenseFeat, get_feature_names

class IndexView(generic.ListView):
    template_name = "moiveReApp/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """Return the last five published questions."""
        return Question.objects.order_by("-pub_date")
class usercf_():
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

    return user_item_matrix, item_dict, user_dict

  def calculate_user_similarity(user_item_matrix):
      # 构建物品到用户的倒排表
      item_users = {}
      for u, items in enumerate(user_item_matrix):
          for i in range(len(items)):
              if items[i] == 1:
                  if i not in item_users:
                      item_users[i] = set()
                  item_users[i].add(u)

      # 计算共同交互物品数的对数惩罚的用户相似度矩阵
      C = {u: {v: 0 for v in range(len(user_item_matrix))} for u in range(len(user_item_matrix))}
      N = {u: 0 for u in range(len(user_item_matrix))}

      for i, users in item_users.items():
          for u in users:
              N[u] += 1
              for v in users:
                  if u == v:
                      continue
                  C[u][v] += 1 / math.log(1 + len(users))

      # 计算最终的用户相似度矩阵
      W = {u: {v: 0 for v in range(len(user_item_matrix))} for u in range(len(user_item_matrix))}

      for u, related_users in C.items():
          for v, cuv in related_users.items():
              W[u][v] = cuv / math.sqrt(N[u] * N[v])

      # 将字典形式的相似度矩阵转换为 NumPy 数组
      user_ids = list(W.keys())
      user_similarity_matrix_array = np.array([[W[u][v] for v in user_ids] for u in user_ids])

      return user_similarity_matrix_array
  def generate_recommendations(target_user, user_similarity_matrix, user_item_matrix, user_dict, item_dict, k):
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
    #print(recommendations)

    # 返回排序后的物品ID列表
    return [item_id for item_id, _ in recommendations]

class itemcf_():

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
# ...

#兴趣标签更新
def update_uesrinterests(user_profile):
    # 获取用户喜欢和点击的物品类别
    liked_categories = [question.category for question in user_profile.liked_items.all()]
    clicked_categories = [question.category for question in user_profile.click_items.all()]
    all_categories = liked_categories + clicked_categories
    # 计算频率
    category_counter = Counter(all_categories)

    # 根据一定的规则选择兴趣标签;这里我暂时就设置阈值
    threshold = 4
    interests = []
    for category, count in category_counter.items():
        # 这里可以根据你的规则选择兴趣标签，比如出现频率大于阈值的类别
        if count >= threshold:
            interests.append(category)

    # 将选定的兴趣标签添加到用户的兴趣标签列表中
    #user_profile.interests.clear()  # 清除旧标签保持时效性
    #print(interests)

    for interest in interests:
        user_interest, created = Userinterests.objects.get_or_create(name=interest)
        user_profile.interests.add(user_interest)



def question_detail(request, question_id):
    user_profile = UserProfile.get_user_profile(request.user)
    question = get_object_or_404(Question, pk=question_id)
    ratings = Rating.objects.filter(question=question)
    avg_rating = ratings.aggregate(Avg('value'))['value__avg']
    form = RatingForm()
    user_profile.click_items.add(question)
    question.clicks+=1
    update_uesrinterests(user_profile)

    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            value = form.cleaned_data['value']
            Rating.objects.create(question=question, user=request.user.username, value=value)
            return redirect('moiveReApp:index')

    return render(request, 'moiveReApp/ratings.html', {'question': question, 'ratings': ratings, 'avg_rating': avg_rating, 'form': form})




def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('moiveReApp:index')
    else:
        form = UserCreationForm()
    return render(request, 'moiveReApp/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('moiveReApp:index')
    else:
        form = AuthenticationForm()
    return render(request, 'moiveReApp/login.html', {'form': form})


def random_questions(request):
    # 获取所有问题
    all_questions = Question.objects.all()

    # 获取随机的20个问题
    random_questions = random.sample(list(all_questions), min(20, len(all_questions)))

    return render(request, 'moiveReApp/randomsort.html', {'random_questions': random_questions})


@login_required
def like_question(request, question_id):
    user_profile = UserProfile.get_user_profile(request.user)

    question = get_object_or_404(Question, id=question_id)

    if request.user in question.liked_by.all():
        # 用户已经点过赞，取消点赞
        question.liked_by.remove(request.user)
        user_profile.liked_items.remove(question)
        update_uesrinterests(user_profile)
        if question.likes>0:
           question.likes-=1
    else:
        # 用户还未点赞，添加点赞
        question.liked_by.add(request.user)
        user_profile.liked_items.add(question)
        question.likes += 1
        update_uesrinterests(user_profile)

    question.save()

    # 获取请求的来源URL，如果没有则默认重定向到首页
    redirect_url = request.META.get('HTTP_REFERER', 'moiveReApp:index')

    # 重定向到来源页面
    return redirect(redirect_url)


def usercf(request):
    # 获取当前登录用户\
    current_user_id = request.user.id  # 假设你使用了Django的认证系统

    # 获取问题列表
    question_list = Question.objects.all()

    # 构建用户-物品交互矩阵等
    user_item_matrix, item_dict, user_dict = usercf_.build_user_item_matrix(question_list)
    user_similarity_matrix = usercf_.calculate_user_similarity(user_item_matrix)
    #print(user_similarity_matrix,user_similarity_matrix.shape)
    #print(user_similarity_matrix)
    # 生成推荐列表
    recommendations = usercf_.generate_recommendations(current_user_id, user_similarity_matrix, user_item_matrix, user_dict, item_dict, k=40)
    # 获取推荐的电影信息
    recommended_movies = Question.objects.filter(id__in=recommendations[:8]) #只展示前五个

    # 在模板中渲染推荐结果
    return render(request, 'moiveReApp/usercf.html', {'recommended_movies': recommended_movies})


def itemcf(request):
    # 获取当前登录用户\
    current_user_id = request.user.id  # 假设你使用了Django的认证系统

    # 获取问题列表
    question_list = Question.objects.all()

    # 构建用户-物品交互矩阵等
    user_item_matrix, item_dict, user_dict = itemcf_.build_user_item_matrix(question_list)
    item_similarity_matrix = itemcf_.calculate_user_similarity(user_item_matrix)
    bert_similarity_matrix = np.load('similarity_matrix.npy')


    #print(user_similarity_matrix,user_similarity_matrix.shape)
    #print(user_similarity_matrix)
    # 生成推荐列表
    recommendations = itemcf_.generate_recommendations(current_user_id, item_similarity_matrix, user_item_matrix, user_dict, item_dict, k=30)
    # 获取推荐
    recommended_movies = Question.objects.filter(id__in=recommendations[:8]) #只展示前ki个


    return render(request, 'moiveReApp/itemcf.html', {'recommended_movies': recommended_movies})



def bertcall(request):
    # 获取当前登录用户\
    current_user_id = request.user.id  # 假设你使用了Django的认证系统

    # 获取问题列表
    question_list = Question.objects.all()

    # 构建用户-物品交互矩阵等
    user_item_matrix, item_dict, user_dict = itemcf_.build_user_item_matrix(question_list)
    item_similarity_matrix = itemcf_.calculate_user_similarity(user_item_matrix)
    bert_similarity_matrix = np.load('similarity_matrix.npy')

    # 设置权重
    weight_item = 0.4
    weight_bert = 0.6

    # 对相似度矩阵进行加权求和
    weighted_similarity_matrix = weight_item * item_similarity_matrix + weight_bert * bert_similarity_matrix

    # 生成推荐列表
    recommendations = itemcf_.generate_recommendations(current_user_id,weighted_similarity_matrix, user_item_matrix, user_dict, item_dict, k=40)
    # 获取推荐的电影信息
    recommended_movies = Question.objects.filter(id__in=recommendations[:8]) #只展示前ki个

    # 在模板中渲染推荐结果
    return render(request, 'moiveReApp/bertcall.html', {'recommended_movies': recommended_movies})







#多路召回 + DeepFM 推荐



class itemcf_deepfm():

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

class hotitem():


    def recall_hot_item(question_list):
        sorted_question_list = sorted(question_list, key=lambda q: q.likes, reverse=True)
        recommendations = [(question.id, question.likes) for question in sorted_question_list]
        return recommendations

class newitem():
    @staticmethod
    def recall_new_item(question_list):
        sorted_question_list = sorted(question_list, key=lambda q: q.pub_date, reverse=True)
        recommendations = [(question.id, 1) for question in sorted_question_list]  #得分为1 不带偏见的推荐新物品~
        return recommendations

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

    def generate_recommendations(score1,score2):
            result_dict = {}
            for key in score1:
                if key in score2:
                    result_dict[key] = score1[key] + score2[key]

            sorted_items = sorted(result_dict.items(), key=lambda x: x[1], reverse=True)
            top_k = sorted_items

            return top_k



def deepfmrec(request):
    current_user_id = request.user.id # 假设你使用了Django的认证系统
    question_list = Question.objects.all()
    user_profile = UserProfile.get_user_profile(current_user_id)

    #召回路
    #1.协同过滤itemcf
    user_item_matrix, item_dict, user_dict = itemcf_deepfm.build_user_item_matrix(question_list)
    item_similarity_matrix = itemcf_deepfm.calculate_user_similarity(user_item_matrix)
    r1 = itemcf_deepfm.generate_recommendations(current_user_id, item_similarity_matrix, user_item_matrix, user_dict, item_dict, k=30)
    liked_items = list(user_profile.liked_items.values_list('id', flat=True))

    #2.热门物品
    r2 = hotitem.recall_hot_item(question_list)
    r2 = [item for item in r2 if item[0] not in liked_items]

    #3.新出物品
    r3 = newitem.recall_new_item(question_list)
    r3 = [item for item in r3 if item[0] not in liked_items]

    #4.U2TAG2L
    a = U2TAG2I.compute_interest_score(user_profile, questions=question_list)
    b = U2TAG2I.compute_similarity(user_profile, questions=question_list)

    r4 = U2TAG2I.generate_recommendations(a, b)
    r4 = [item for item in r4 if item[0] not in liked_items]

    #汇总4路召回

    # 获取每个类别前 10 个物品的 ID，去除重复项
    top_10_ids = list(
        set([item[0] for item in r1[:10]] + [item[0] for item in r2[:10]] + [item[0] for item in r3[:10]] + [item[0] for item in
        r4[:10]]))
    # print(top_10_ids)
    # 根据 top_10_ids 从 r1, r2, r3, r4 中找到对应的得分
    result = []
    for item_id in top_10_ids:
        score1 = next((item[1] for item in r1 if item[0] == item_id), None)
        score2 = next((item[1] for item in r2 if item[0] == item_id), None)
        score3 = next((item[1] for item in r3 if item[0] == item_id), None)
        score4 = next((item[1] for item in r4 if item[0] == item_id), None)
        result.append((item_id, score1, score2, score3, score4))
    df_origin = pd.DataFrame(result, columns=['id', 'feature1', 'feature2', 'feature3', 'feature4'])
    df = pd.DataFrame(result, columns=['id', 'feature1', 'feature2', 'feature3', 'feature4'])

    #进入模型预测:

    rec_id = df['id']
    df.drop(columns=['id'], inplace=True) #id不是特征
    # 进行预测任务，不需要标签列
    # 对特征进行预处理，包括离散特征进行标签编码，连续特征进行归一化

    # 对离散特征进行标签编码
    sparse_features = ['feature2', 'feature3']  # 假设这些是离散特征的列名
    for feat in sparse_features:
        lbe = LabelEncoder()
        df[feat] = lbe.fit_transform(df[feat])

    # 对连续特征进行归一化
    dense_features = ['feature1', 'feature4']  # 假设这些是连续特征的列名
    mms = MinMaxScaler()
    df[dense_features] = mms.fit_transform(df[dense_features])
    # deepctr模型输入
    fixlen_feature_columns = [SparseFeat(feat, df[feat].nunique(), embedding_dim=4) for feat in sparse_features] + [
        DenseFeat(feat, 1, ) for feat in dense_features]

    # DeepFM 模型
    model = DeepFM(fixlen_feature_columns, fixlen_feature_columns, task='binary')
    # 编译模型
    model.compile("adam", "binary_crossentropy", metrics=["binary_crossentropy"])
    # 获取模型输入
    model_input = {name: df[name].values for name in get_feature_names(fixlen_feature_columns)}
    # 进行预测
    pred_ans = model.predict(model_input, batch_size=1)
    pred_list = [(id, score) for id, score in zip(rec_id, pred_ans.flatten())]
    # 假设 pred_list 是一个包含预测结果的列表，每个元素是一个元组 (id, score)
    pred_list_sorted = sorted(pred_list, key=lambda x: x[1], reverse=True)

    # 输出排序后的预测结果列表
    #print(pred_list_sorted)

    # 获取推荐
    recommendations =[item_id for item_id, _ in pred_list_sorted]
    recommended_all = Question.objects.filter(id__in=recommendations)
    ki=8
    recommended_movies = Question.objects.filter(id__in=recommendations[:ki])  # 只展示前ki个
    print('前者：',recommended_movies)


    #根据用户反馈实时训练更新===================================================================
    # 获取当前用户喜欢或点击的物品的ID列表
    liked_or_clicked_items_ids = list(user_profile.liked_items.values_list('id', flat=True))
    liked_or_clicked_items_ids.extend(list(user_profile.click_items.values_list('id', flat=True)))
    liked_or_clicked_items_ids = set(liked_or_clicked_items_ids)

    #与推荐的物品取交集

    # 将被当前用户点击或喜欢的物品的ID放入列表中
    like_or_click_items = [movie.id for movie in recommended_all if movie.id in liked_or_clicked_items_ids]
    recommend_but_not_click_or_like = [movie.id for movie in recommended_all[ki:] if movie.id not in liked_or_clicked_items_ids]
    # 获取 like_or_click_items 对应的行号
    row_indices_true = df_origin[df_origin['id'].isin(like_or_click_items)].index
    row_indices_false =df_origin[df_origin['id'].isin(recommend_but_not_click_or_like)].index

    train_data_true= df.loc[row_indices_true, ['feature1', 'feature2', 'feature3', 'feature4']]
    train_data_false = df.loc[row_indices_false, ['feature1', 'feature2', 'feature3', 'feature4']]
    train_data_false['label'] = 0
    train_data_true['label'] = 1

    train_data = pd.concat([train_data_true, train_data_false], ignore_index=True)

    #print(train_data)
    train_threshold=1
    # 检查 train_data 中的标签分布情况
    label_distribution = train_data['label'].value_counts()
    #print('label_dis:',label_distribution)

    if len(train_data) >= train_threshold:
       #训练输入
        fixlen_feature_columns = [SparseFeat(feat, train_data[feat].nunique(), embedding_dim=4) for feat in sparse_features] + [
            DenseFeat(feat, 1, ) for feat in dense_features]

        train_model_input = {name: train_data[name].values for name in get_feature_names(fixlen_feature_columns)}
        #print('input:',train_model_input)

        history = model.fit(train_model_input, train_data['label'].values,
                        batch_size=len(train_data), epochs=4, verbose=2, validation_split=0.0, )

        #训练后预测
        model_input = {name: df[name].values for name in get_feature_names(fixlen_feature_columns)}
        pred_ans = model.predict(model_input, batch_size=1)
        pred_list = [(id, score) for id, score in zip(rec_id, pred_ans.flatten())]
        pred_list_sorted = sorted(pred_list, key=lambda x: x[1], reverse=True)
        recommendations = [item_id for item_id, _ in pred_list_sorted]
        recommended_movies1 = []

        for question_id in recommendations:
           q =Question.objects.filter(id=question_id)
           recommended_movies1.append(q)
        from itertools import chain
        recommended_movies = list(chain.from_iterable(recommended_movies1))


        return render(request, 'moiveReApp/deepfmrec.html', {'recommended_movies': recommended_movies})
    return render(request, 'moiveReApp/deepfmrec.html', {'recommended_movies': recommended_movies})




