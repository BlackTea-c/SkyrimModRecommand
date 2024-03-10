from django.utils import timezone
from moiveReApp.models import Question


questions_to_create = [
    Question(
        question_text='问题1',

        pub_date=timezone.now(),
    ),
    Question(
        question_text='问题2',

        pub_date=timezone.now(),
    ),
    # 添加更多问题实例...
]
Question.objects.bulk_create(questions_to_create)
