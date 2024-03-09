from django.db import models

# Create your models here.

from django.db import models
import datetime
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

class Tag(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    img = models.ImageField("封面图",upload_to='question_image/', blank=True, null=True,default='question_image/placeholder.jpg')
    img_url = models.URLField("外部图片链接", blank=True, null=True)
    tags = models.ManyToManyField(Tag)
    category = models.CharField(max_length=200,default='other')
    link = models.CharField(max_length=200,default='http://127.0.0.1:8000/moiveReApp/')
    detail = models.CharField(max_length=600,default=' ')
    pub_date = models.DateTimeField("date published")

    likes = models.PositiveIntegerField(default=0)
    liked_by = models.ManyToManyField(User, blank=True, related_name='liked_questions')
    def __str__(self):
        return f"{self.question_text} - {self.img.url}"

    def photo_url(self):
        if self.photo and hasattr(self.photo, 'url'):
            return self.photo.url
        else:
            return '/moiveReApp/images/placeholder.jpg'

    def get_image_url(self):
        return self.img_url or (
            self.img.url if self.img and hasattr(self.img, 'url') else '/moiveReApp/question_image/placeholder.jpg')

    def was_published_recently(self):
        return self.pub_date >=timezone.now() - datetime.timedelta(days=1)

    def avg_rating(self):
        ratings = Rating.objects.filter(question=self)
        if ratings.exists():
            avg = ratings.aggregate(models.Avg('value'))['value__avg']
            return round(avg, 1)
        return None


class Rating(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.CharField(max_length=255,default='some_default_value')
    value = models.IntegerField(default=0)  # 确保这一行存在

    def __str__(self):
        return f"{self.question.question_text} - {self.value}"



