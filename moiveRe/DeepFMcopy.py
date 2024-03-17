import django
import os
import torch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moiveRe.settings")
django.setup()









import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
import torch
from deepctr_torch.models import DeepFM
from deepctr_torch.inputs import SparseFeat, DenseFeat, get_feature_names

# 生成示例数据
np.random.seed(2024)
data_size = 10000

# 假设有 26 个离散特征 C1, C2, ..., C26
sparse_features = ['C' + str(i) for i in range(1,4)]
# 假设有 13 个连续特征 I1, I2, ..., I13
dense_features = ['I' + str(i) for i in range(1,3)]

data = {feat: np.random.choice([0, 1, 2, 3, 4], data_size) for feat in sparse_features}
data.update({feat: np.random.rand(data_size) for feat in dense_features})
data['label'] = np.random.randint(0, 2, data_size)

# 转换为 DataFrame
df = pd.DataFrame(data)
print(df)


#预处理部分:
# 对离散特征进行标签编码,转为数值的意思
for feat in sparse_features:
    lbe = LabelEncoder()
    df[feat] = lbe.fit_transform(df[feat])
# 对连续特征进行归一化
mms = MinMaxScaler()
df[dense_features] = mms.fit_transform(df[dense_features])

train, test = train_test_split(df, test_size=0.2)

# deepctr模型输入
fixlen_feature_columns = [SparseFeat(feat, df[feat].nunique(), embedding_dim=4) for feat in sparse_features] + [DenseFeat(feat, 1,) for feat in dense_features]




# DeepFM 模型，开导！
model = DeepFM(fixlen_feature_columns, fixlen_feature_columns, task='binary') # 重复传入相同的列~ 这里因为是根据CTR来对召回进行排序所以就是binary任务

# 编译模型
model.compile("adam", "binary_crossentropy",
              metrics=["binary_crossentropy"], ) #优化器选择balabala，这里直接看库里给的文档

# 训练模型
train_model_input = {name: train[name].values for name in get_feature_names(fixlen_feature_columns)}
test_model_input = {name: test[name].values for name in get_feature_names(fixlen_feature_columns)}
label_distribution = train['label'].value_counts()
print('label_dis:',label_distribution)
history = model.fit(train_model_input, train['label'].values,
                    batch_size=50, epochs=4, verbose=2, validation_split=0, ) #fit开始train





