from django.contrib import admin

# Register your models here.
from .models import Question,Rating,Tag,UserProfile

admin.site.register(Question)
admin.site.register(Rating)
admin.site.register(Tag)
admin.site.register(UserProfile)