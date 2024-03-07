from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve
from .views import question_detail
from .views import register, user_login,random_questions

app_name = "moiveReApp"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path('register/', register, name='register'),
    path('login/', user_login, name='user_login'),
    path('randomsort/', random_questions, name='random_questions'),

    path('<int:question_id>/ratings/', question_detail, name='question_detail'),

    path('admin/', admin.site.urls),

    #url(r'^media/(?P<path>.*)$',serve,{'document_root':settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)