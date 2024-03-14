import django
import os
import torch
import numpy as np
from transformers import DistilBertTokenizer, DistilBertModel
from sklearn.metrics.pairwise import cosine_similarity

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moiveRe.settings")
django.setup()

from moiveReApp.models import Question

# 加载DistilBERT模型和分词器
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
model = DistilBertModel.from_pretrained('distilbert-base-uncased')

question_list = Question.objects.all()
num_questions = len(question_list)

# 初始化相似度矩阵
similarity_matrix = np.zeros((num_questions, num_questions))

# 计算相似度矩阵
for i in range(num_questions):
    text_i = question_list[i].question_text + question_list[i].detail + question_list[i].category
    for j in range(i + 1, num_questions):  # 只计算下三角部分
        text_j = question_list[j].question_text + question_list[j].detail + question_list[j].category

        # 使用分词器对文本进行处理
        inputs = tokenizer([text_i, text_j], return_tensors='pt', padding=True, truncation=True)

        # 将模型和输入数据转移到GPU上
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model.to(device)
        input_ids = inputs['input_ids'].to(device)
        attention_mask = inputs['attention_mask'].to(device)

        # 使用DistilBERT模型进行推理
        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)

        # 将文本表示向量转移到CPU上
        text_i_embedding = outputs.last_hidden_state[0].mean(dim=0).cpu()
        text_j_embedding = outputs.last_hidden_state[1].mean(dim=0).cpu()
        print(text_i_embedding)

        # 计算文本相似度（这里简单地使用余弦相似度）
        similarity = torch.nn.functional.cosine_similarity(text_i_embedding, text_j_embedding, dim=0)
        similarity_matrix[i, j] = similarity.item()
        print(i," ",j," ","finished")

# 将下三角部分的相似度复制到上三角部分
similarity_matrix += similarity_matrix.T - np.diag(similarity_matrix.diagonal())

# 打印相似度矩阵
print("相似度矩阵：")
print(similarity_matrix)

np.save('similarity_matrix.npy', similarity_matrix)  #保存一下，计算真滴慢
