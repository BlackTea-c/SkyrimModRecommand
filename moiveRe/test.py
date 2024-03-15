import django
import os
import torch
import numpy as np
from transformers import DistilBertTokenizer, DistilBertModel
from sklearn.metrics.pairwise import cosine_similarity

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moiveRe.settings")
django.setup()

from moiveReApp.models import Question

# 初始化DistilBERT分词器
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

# 加载DistilBERT模型
model = DistilBertModel.from_pretrained('distilbert-base-uncased')

# 检查是否有可用的GPU，并将模型移动到GPU上
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# 获取问题列表
question_list = Question.objects.all()
num_questions = len(question_list)

# 初始化相似度矩阵
similarity_matrix = np.zeros((num_questions, num_questions))

# 将文本列表转换为张量
texts = [question.question_text + question.detail + question.category for question in question_list]
inputs = tokenizer(texts, return_tensors='pt', padding=True, truncation=True)

# 将张量移动到GPU上
input_ids = inputs['input_ids'].to(device)
attention_mask = inputs['attention_mask'].to(device)
# 使用DistilBERT模型进行推理
with torch.no_grad():
    outputs = model(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state

# 将文本表示向量转移到CPU上
text_embeddings = outputs.mean(dim=1).cpu().numpy()

print(text_embeddings)


# 计算相似度矩阵（并行计算）
for i in range(num_questions):
    for j in range(i + 1, num_questions):
        similarity_matrix[i, j] = cosine_similarity([text_embeddings[i]], [text_embeddings[j]])[0][0]
        print(i,j,'finished')

# 将下三角部分的相似度复制到上三角部分
similarity_matrix += similarity_matrix.T - np.diag(similarity_matrix.diagonal())

# 打印相似度矩阵
print("相似度矩阵：")
print(similarity_matrix)

# 保存相似度矩阵为.npy文件
np.save('similarity_matrix.npy', similarity_matrix)

