import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from deepctr.models import DeepFM
from deepctr.feature_column import SparseFeat, get_feature_names

# 假设有一个包含广告特征和点击情况的数据集
data = {
    'user_id': [1, 2, 3, 4, 5],
    'ad_id': [101, 102, 103, 104, 105],
    'age': [25, 30, 35, 40, 45],
    'gender': ['M', 'F', 'M', 'F', 'M'],
    'click': [1, 0, 1, 0, 1]
}
df = pd.DataFrame(data)

# 定义特征列
sparse_features = ['user_id', 'ad_id', 'gender']
dense_features = ['age']

# 将特征列转换为SparseFeat和DenseFeat类型
feature_columns = [SparseFeat(feat, vocabulary_size=df[feat].nunique(), embedding_dim=4)
                   for feat in sparse_features] + [DenseFeat(feat, 1) for feat in dense_features]

# 划分训练集和测试集
train, test = train_test_split(df, test_size=0.2)

# 创建模型
model = DeepFM(feature_columns, feature_columns, task='binary')

# 编译模型
model.compile("adam", "binary_crossentropy", metrics=['binary_crossentropy'])

# 将数据转换为模型所需的输入格式
train_model_input = {name: train[name] for name in sparse_features + dense_features}
test_model_input = {name: test[name] for name in sparse_features + dense_features}
train_target = train['click'].values
test_target = test['click'].values

# 训练模型
history = model.fit(train_model_input, train_target, batch_size=256, epochs=10, verbose=2, validation_split=0.2)

# 预测
preds = model.predict(test_model_input, batch_size=256)

# 输出预测结果
print("预测点击率：", preds)
