from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
from django.views import generic
from .forms import RatingForm
from django.db.models import Avg
from django.shortcuts import render, get_object_or_404, redirect
from .models import Question, Rating
import random
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


class IndexView(generic.ListView):
    template_name = "moiveReApp/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """Return the last five published questions."""
        return Question.objects.order_by("-pub_date")
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


from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect

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



