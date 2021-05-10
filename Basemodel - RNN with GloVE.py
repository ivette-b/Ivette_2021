# -*- coding: utf-8 -*-
"""Basemodel_2__RNN_w__GloVe_(1)_(1)_(2)_(1) (1).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1rwkNpBTLM3-mFfms1UznLXoEGl5u3G-v
"""

#Mount google drive
import pickle

from google.colab import drive
drive.mount('/content/drive')

path = '/content/drive/My Drive/Thesis/training_data.pickle'
path2 = '/content/drive/My Drive/Thesis/test_data.pickle'

#loading train dataset
with open(path, 'rb') as file:
    train = pickle.loads(file.read())

#loading test dataset
with open(path2, 'rb') as file:
    test = pickle.loads(file.read())

!cp drive/MyDrive/Thesis/baseline_functions.py .
!cp drive/MyDrive/Thesis/data_functions.py .

import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt 
import torch 
import torchtext 
import torchtext.legacy.data 
from torchtext import vocab
import random 
import time # 
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('stopwords')
from baseline_functions import remover, preprocessing2, Recurrent, train_epoch, evaluate, random_search_RNN, hyperparametertuning
from data_functions import pickle_splitter, binarizer

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

import pandas as pd
## merging labels and transcripts together and merging the labels 2 and 3 (conspiracy labels)
transtr, labeltr = pickle_splitter(train)
transtest, labeltest = pickle_splitter(test)
y_tr = binarizer(labeltr)
y_test = binarizer(labeltest)

train_df = pd.DataFrame(transtr, columns = ['data'])
train_df['labels'] = y_tr
test_df = pd.DataFrame(transtest, columns = ['data'])
test_df['labels'] = y_test

print(test_df.head())
print(train_df.head())
print()

## removing transcripts containing a very few words
print(f"length train: {len(train_df)}, length test: {len(test_df)}")
print('Removing incomplete transcripts..')
train_df = remover(train_df, 50)
test_df= remover(test_df, 50)
print(f"length train: {len(train_df)}, length test: {len(test_df)}")

trainval_df = train_df.copy()
from sklearn.model_selection import train_test_split
train_df, val_df = train_test_split(train_df, test_size=0.25, random_state = 2021)
print(len(train_df), len(val_df), len(test_df))

TEXT = torchtext.legacy.data.Field(tokenize=preprocessing2)
LABEL = torchtext.legacy.data.LabelField(dtype=torch.float)
fields = [('data',TEXT),('labels',LABEL)]

## saving to csv to use the tabular dataset function from torchtext.legacy
train_df.to_csv(r'/content/drive/My Drive/Thesis/train.csv', index = False)
val_df.to_csv(r'/content/drive/My Drive/Thesis/val.csv', index = False)
trainval_df.to_csv(r'/content/drive/My Drive/Thesis/trainval.csv', index = False)
test_df.to_csv(r'/content/drive/My Drive/Thesis/test.csv', index = False)

out_path = '/content/drive/My Drive/Thesis/'
train = torchtext.legacy.data.TabularDataset(path=out_path +'train.csv',format='csv',skip_header=True,fields=fields)
val = torchtext.legacy.data.TabularDataset(path=out_path +'val.csv',format='csv',skip_header=True,fields=fields)

##getting glove embeddings
SEED = 2021
torch.manual_seed(SEED)
torch.cuda.manual_seed(SEED)
torch.backends.cudnn.deterministic = True
glove = vocab.Vectors(out_path +'glove.42B.300d.txt')
print(f'Shape of GloVe vectors is {glove.vectors.shape}')
TEXT.build_vocab(train,vectors=glove,unk_init=torch.Tensor.zero_)
LABEL.build_vocab(train)

##checks
#print(f'Type of "train:" {type(train)}\n Length of "train": {len(train)}\n' )
#i = random.randint(0,len(train)) 
#print(f'Keys at index {i} of "train": {train[i].__dict__.keys()}\n')
#print("Contents at random index:\n",vars(train.examples[i]))

## checks
print(f"Unique tokens in TEXT vocabulary: {len(TEXT.vocab)}")
print(f"Unique tokens in LABEL vocabulary: {len(LABEL.vocab)}")
print(f"Most common 15 words in the vocab are: {TEXT.vocab.freqs.most_common(15)}")

import csv
import torch
import random
import numpy as np
import logging
from torch import nn
logging.basicConfig(level=logging.INFO)

SEED = 2021
torch.manual_seed(SEED)
torch.cuda.manual_seed(SEED)
torch.backends.cudnn.deterministic = True
results, highest = hyperparametertuning(train, val, 150)

batch_size_RNN = list(highest.values())[0]
RNN_epochs = list(highest.values())[1]
pos_weight = list(highest.values())[2]
RNN_type = list(highest.values())[3]
RNN_lr = list(highest.values())[4]
RNN_wd = list(highest.values())[5]
RNN_layers = list(highest.values())[6]
RNN_units = list(highest.values())[7]
dropout = list(highest.values())[8] ## 1 layer so dropout does not really matter..
print(batch_size_RNN, pos_weight,RNN_type, RNN_epochs, RNN_lr, RNN_wd, RNN_layers, RNN_units, dropout)

TEXT2 = torchtext.legacy.data.Field(tokenize=preprocessing2 )
LABEL2 = torchtext.legacy.data.LabelField(dtype=torch.float)
fields2 = [('data',TEXT2),('labels',LABEL2)] 
trainval = torchtext.legacy.data.TabularDataset(path=out_path +'trainval.csv',format='csv',skip_header=True,fields=fields2)
test = torchtext.legacy.data.TabularDataset(path=out_path +'test.csv',format='csv',skip_header=True,fields=fields2)
TEXT2.build_vocab(trainval,vectors=glove,unk_init=torch.Tensor.zero_) 
LABEL2.build_vocab(trainval)

import csv
import torch
import random
import numpy as np
import logging
from torch import nn
logging.basicConfig(level=logging.INFO)
trainval_iter = torchtext.legacy.data.BucketIterator(trainval, batch_size=batch_size_RNN,
                                                  sort_key=lambda x: len(x.data),
                                                  sort_within_batch=False,
                                                  device='cuda') 
test_iter = torchtext.legacy.data.BucketIterator(test, batch_size=batch_size_RNN,
                                                sort_key=lambda x: len(x.data),
                                                sort_within_batch=False,
                                                device='cuda') 
input_dim = len(TEXT2.vocab)
embedding_dim = 300

model = Recurrent(recurrent = RNN_type, input_dim=input_dim, embedding_dim = embedding_dim, 
                  hidden_dim = RNN_units, num_layers=RNN_layers, output_dim=1, dropout = dropout, embedding = vocab.Vectors).cuda() #RNN_layers

## updating model embedding with glove embedding weights
pretrained_embeddings = TEXT2.vocab.vectors
model.embedding.weight.data = pretrained_embeddings.cuda() 

unknown_index = TEXT2.vocab.stoi[TEXT2.unk_token] # get index of unknown token
padding_index = TEXT2.vocab.stoi[TEXT2.pad_token] # get index of padding token
model.embedding.weight.data[unknown_index] = torch.zeros(embedding_dim) #change values to zeros
model.embedding.weight.data[padding_index] = torch.zeros(embedding_dim)

optimizer = torch.optim.Adam(model.parameters(), lr = RNN_lr , weight_decay= RNN_wd)
history = dict(auc=[], val_auc=[], loss=[], val_loss=[])

criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(np.array([pos_weight]))).cuda()
logging.basicConfig(level=logging.INFO)
logging.info("Epoch Loss Val_loss Acc Val_acc")
for epoch in range(1, RNN_epochs+1):
  optimizer.zero_grad()
  loss, auc = train_epoch(model, trainval_iter, optimizer, criterion)
  history['auc'].append(auc)
  history['loss'].append(loss)
  val_loss, val_auc = evaluate(model, test_iter, criterion)
  history['val_auc'].append(val_auc)
  history['val_loss'].append(val_loss)
  logging.info(f"{epoch:3d} {loss:.3f} {val_loss:.3f} {auc:.3f} {val_auc:.3f}")
last_tr_auc = history['auc'][-1]
last_test_auc = history['val_auc'][-1]
print(f'training auc: {last_tr_auc}, test auc: {last_test_auc}')