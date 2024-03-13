# Create your views here.
from django.views import generic
from .forms import RatingForm
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from .models import Question, Rating
import random
from django.contrib.auth.decorators import login_required
#from recsystem.userCFrecommendation import usercf
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import math

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
# ...
def question_detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    ratings = Rating.objects.filter(question=question)
    avg_rating = ratings.aggregate(Avg('value'))['value__avg']
    form = RatingForm()

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
    question = get_object_or_404(Question, id=question_id)

    if request.user in question.liked_by.all():
        # 用户已经点过赞，取消点赞
        question.liked_by.remove(request.user)
        if question.likes>0:
           question.likes-=1
    else:
        # 用户还未点赞，添加点赞
        question.liked_by.add(request.user)
        question.likes += 1

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



