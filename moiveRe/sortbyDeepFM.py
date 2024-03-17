import django
import os
import torch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moiveRe.settings")
django.setup()









import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
import torch
from deepctr_torch.models import DeepFM
from deepctr_torch.inputs import SparseFeat, DenseFeat, get_feature_names

# 假设你已经准备好了包含特征的 DataFrame，其中 'id' 列是不参与预测的特征列，其余列是特征
# 你可以通过删除 'id' 列来获得特征数据
df = pd.read_csv('test_data.csv')  # 假设你的数据集保存为 CSV 文件
rec_id = df['id']
# 假设 'id' 列是索引，不是特征，因此将其从 DataFrame 中移除
df.drop(columns=['id'], inplace=True)
# 进行预测任务，不需要标签列
# 你需要对特征进行预处理，包括离散特征进行标签编码，连续特征进行归一化

# 对离散特征进行标签编码
sparse_features = ['feature2','feature3']  # 假设这些是离散特征的列名
for feat in sparse_features:
    lbe = LabelEncoder()
    df[feat] = lbe.fit_transform(df[feat])

# 对连续特征进行归一化
dense_features = ['feature1','feature4']  # 假设这些是连续特征的列名
mms = MinMaxScaler()
df[dense_features] = mms.fit_transform(df[dense_features])
print(df)
# deepctr模型输入
fixlen_feature_columns = [SparseFeat(feat, df[feat].nunique(), embedding_dim=4) for feat in sparse_features] + [DenseFeat(feat, 1,) for feat in dense_features]

# DeepFM 模型
model = DeepFM(fixlen_feature_columns, fixlen_feature_columns, task='binary')

# 编译模型
model.compile("adam", "binary_crossentropy", metrics=["binary_crossentropy"])

# 获取模型输入
model_input = {name: df[name].values for name in get_feature_names(fixlen_feature_columns)}

# 进行预测
pred_ans = model.predict(model_input, batch_size=1)
pred_list = [(id, score) for id, score in zip(rec_id, pred_ans.flatten())]

# 假设 pred_list 是一个包含预测结果的列表，每个元素是一个元组 (id, score)
pred_list_sorted = sorted(pred_list, key=lambda x: x[1], reverse=True)

# 输出排序后的预测结果列表
print(pred_list_sorted)









