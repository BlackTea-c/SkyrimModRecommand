from django.shortcuts import render

# Create your views here.
from django.views import generic
from .forms import RatingForm
from django.db.models import Avg
from django.shortcuts import render, get_object_or_404, redirect
from .models import Question, Rating



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
            return redirect('moiveReApp:question_detail', question_id=question_id)

    return render(request, 'moiveReApp/ratings.html', {'question': question, 'ratings': ratings, 'avg_rating': avg_rating, 'form': form})



