# Purpose
# This script uses TF-IDF and LDA to perform topic extraction

# Instructions
# This script requires the json data dumps

# Status
# This should run. It takes a while to process each file though.

# Source
# https://stackabuse.com/python-for-nlp-topic-modeling/

with open('../../../jsondumps.txt', 'r') as f:
    ROOT = f.readline()

import pandas as pd
import numpy as np

import json

import gc
import traceback

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from sklearn.decomposition import LatentDirichletAllocation, NMF

import importlib.util
spec = importlib.util.spec_from_file_location('jsonquery', '../../../Data Processing/jsonquery.py')
jsonquery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jsonquery)

#import sentencepiece as spm

#sp = spm.SentencePieceProcessor()
#sp.Load("a.model")

def get_data():
    r = []
    sum = 0
    count = 0

    while True:
        try:
            with open('../../../../atlassian/' + 'ATLASSIAN_' + str(count) +'.json', 'r', encoding='UTF-8') as f:
                data = json.loads(f.read())
            print('ATLASSIAN_' + str(count) + '.json')

            d = jsonquery.query(data, 'issues.fields.^description')
            t = jsonquery.query(data, 'issues.fields.^summary')

            print(data)

            do = []
            to = []

            for i in range(min(len(d), len(t))):
                if not d[i] is None and not t[i] is None:
                    do += [d[i]]
                    to += [t[i]]
                
            r = do + to
            count_vect = TfidfVectorizer(max_df=0.8, min_df=2, stop_words=None)#, lowercase=False, analyzer=sp.EncodeAsPieces)
            
            #doc_term_matrix = count_vect.fit_transform(r).todense()

            
            #LDA = LatentDirichletAllocation(
            #    n_components=20, 
            #    random_state=42,
            #    n_jobs=-1)#, 
                #learning_method='online', 
                #learning_decay=1.0,
                #batch_size=500,
                #max_iter=20,
                #total_samples=1000000000)
            #LDA.fit(doc_term_matrix)
            """
            LDA = NMF(n_components=5, random_state=1,
                beta_loss='kullback-leibler', solver='mu', max_iter=1000, alpha=.1,
                l1_ratio=.5)
            LDA.fit(doc_term_matrix)

            first_topic = LDA.components_[0]
            top_topic_words = first_topic.argsort()[-20:]

            for i in top_topic_words:
                print(count_vect.get_feature_names()[i])

            topics = []
            for i,topic in enumerate(LDA.components_):
                t = [count_vect.get_feature_names()[i] for i in topic.argsort()[-20:]]
                #print(sp.DecodePieces(t))
                topics += [set(t)]
                print(f'Top 20 words for topic #{i}:')
                print(t)
                print('\n')
            """
            count += 1001
            
        except Exception as e:
            print('error', e)
            traceback.print_exc()
            break
    
    return r

d = get_data()
