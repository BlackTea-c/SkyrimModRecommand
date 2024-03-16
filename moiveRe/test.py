import django
import os
import torch
import numpy as np
from transformers import DistilBertTokenizer, DistilBertModel
from sklearn.metrics.pairwise import cosine_similarity
import torch
from transformers import DistilBertTokenizer, DistilBertModel
from sklearn.metrics.pairwise import cosine_similarity



os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moiveRe.settings")
django.setup()

from moiveReApp.models import UserProfile,Question
from django.contrib.auth.models import User


user = User.objects.get(username='gly233')


user_profile = UserProfile.get_user_profile(user)
question_list = Question.objects.all()

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

top_k = U2TAG2I.generate_recommendations(a,b,10)
print(top_k)