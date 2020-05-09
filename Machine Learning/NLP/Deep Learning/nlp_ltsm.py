# Purpose
# Use LTSM to train a text to generate a summary from a description

# Instructions
# This requires bert data to be downloaded.

# Status
# This script is currently broken. It nearly works..

# Source
# https://nlpforhackers.io/keras-intro/

ROOT = 'F:/jsondumps/atlassian/'

import re
import pandas as pd
import numpy
from sklearn.model_selection import train_test_split

import json

import importlib.util
spec = importlib.util.spec_from_file_location('jsonquery', '../../../Data Processing/jsonquery.py')
jsonquery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jsonquery)

import nltk
nltk.download('stopwords')

with open(ROOT + 'ATLASSIAN_CLOV_0.json', 'r', encoding='UTF-8') as f:
    data = json.loads(f.read())

print(len(data['issues']))
    
d = jsonquery.query(data, 'issues.fields.^description')
t = jsonquery.query(data, 'issues.fields.^summary')

do = []
to = []

for i in range(min(len(d), len(t))):
    if not d[i] is None and not t[i] is None:
        do += [d[i]]
        to += [t[i]]

do = numpy.array(do)
to = numpy.array(to)

print(len(do))
print(len(to))

X_train, X_test, y_train, y_test = train_test_split(do, to, test_size=0.2)

from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
 
vectorizer = CountVectorizer(binary=True, stop_words=stopwords.words('english'), 
                             lowercase=True, min_df=3, max_df=0.9, max_features=5000)
X_train_onehot = vectorizer.fit_transform(X_train)

word2idx = {word: idx for idx, word in enumerate(vectorizer.get_feature_names())}
tokenize = vectorizer.build_tokenizer()
preprocess = vectorizer.build_preprocessor()
 
def to_sequence(tokenizer, preprocessor, index, text):
    words = tokenizer(preprocessor(text))
    indexes = [index[word] for word in words if word in index]
    return indexes
 
print(to_sequence(tokenize, preprocess, word2idx, "This is an important test!"))  # [2269, 4453]
X_train_sequences = [to_sequence(tokenize, preprocess, word2idx, x) for x in X_train]
print(X_train_sequences[0])

# Compute the max lenght of a text
MAX_SEQ_LENGHT = len(max(X_train_sequences, key=len))
print("MAX_SEQ_LENGHT=", MAX_SEQ_LENGHT)
 
from keras.preprocessing.sequence import pad_sequences
N_FEATURES = len(vectorizer.get_feature_names())
X_train_sequences = pad_sequences(X_train_sequences, maxlen=MAX_SEQ_LENGHT, value=N_FEATURES)
print(X_train_sequences[0])

X_test_sequences = [to_sequence(tokenize, preprocess, word2idx, x) for x in X_test]
X_test_sequences = pad_sequences(X_test_sequences, maxlen=MAX_SEQ_LENGHT, value=N_FEATURES)

from keras.models import Sequential
from keras.layers import Dense, LSTM, Embedding
 
model = Sequential()
model.add(Embedding(len(vectorizer.get_feature_names()) + 1,
                    64,  # Embedding size
                    input_length=MAX_SEQ_LENGHT))
model.add(LSTM(64))
model.add(Dense(units=1, activation='sigmoid'))
 
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
print(model.summary())

model.fit(X_train_sequences[:-100], y_train[:-100], 
          epochs=2, batch_size=128, verbose=1, 
          validation_data=(X_train_sequences[-100:], y_train[-100:]))

scores = model.evaluate(X_test_sequences, y_test, verbose=1)
print("Accuracy:", scores[1]) # 0.875