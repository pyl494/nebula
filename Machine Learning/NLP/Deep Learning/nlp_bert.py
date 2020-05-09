# Purpose
# Attempting to use state-of-the-art NLP processing

# Instructions
# This requires bert data to be downloaded and python module installed: https://github.com/google-research/bert
# This script requires tensorflow 2.0 and keras
# This script requires the atlassian issue json data dump

# Status
# This script isn't complete yet.

# Source: https://github.com/kpe/bert-for-tf2

with open('../../../jsondumps.txt', 'r') as f:
    ROOT = f.readline()

import os
import bert

import json
import random

from tensorflow import keras
import tensorflow

class Model:
    model_name = 'uncased_L-12_H-768_A-12'
    model_dir = './models/' + model_name
    model_ckpt = os.path.join(model_dir, "bert_model.ckpt")
    max_seq_len = 128

    def __init__(self):
        self.bert_params = bert.params_from_pretrained_ckpt(model_dir)
        self.l_bert = bert.BertModelLayer.from_params(self.bert_params, name="bert")

        self.l_input_ids      = keras.layers.Input(shape=(max_seq_len,), dtype='int32')
        self.l_token_type_ids = keras.layers.Input(shape=(max_seq_len,), dtype='int32')

        # using the default token_type/segment id 0
        self.output = self.l_bert(self.l_input_ids)                              # output: [batch_size, max_seq_len, hidden_size]
        self.model = keras.Model(inputs=self.l_input_ids, outputs=self.output)
        self.model.build(input_shape=(None, max_seq_len))

class PrepData:
    def __init__(self, model):
        self.model = model
        do_lower_case = not (self.model.model_name.find("cased") == 0 or self.model.model_name.find("multi_cased") == 0)
        bert.bert_tokenization.validate_case_matches_checkpoint(do_lower_case, self.model.model_ckpt)
        vocab_file = os.path.join(self.model.model_dir, "vocab.txt")
        self.tokenizer = bert.bert_tokenization.FullTokenizer(vocab_file, do_lower_case)

    def tokenize(self, message):
        tokens = tokenizer.tokenize(message)
        token_ids = tokenizer.convert_tokens_to_ids(tokens)
        return {'tokens':tokens, 'token_ids': token_ids}

    def serialize(self, token_ids, label):
        feature = {
            "token_ids": tensorflow.train.Feature(int64_list=tensorflow.train.Int64List(value=token_ids)),
            "label":     tensorflow.train.Feature(int64_list=tensorflow.train.Int64List(value=[label]))
        }
        proto = tensorflow.train.Example(features=tensorflow.train.Features(feature=feature))
        return proto.SerializeToString()

    def split_training_test(self, data):
        random.shuffle(data)
        l = len(data) * 0.8
        return {'training': data[:l], 'test': data[l:]}

    def get_data(self):
        data = {'text':[], 'label':[]}
        count = 0

        while True:
            try:
                with open(ROOT + 'ATLASSIAN_strings.txt', 'w', encoding='utf-8') as out:
                    with open(ROOT + 'ATLASSIAN_' + str(count) +'.json', 'r') as f:
                        data = json.loads(f.read())
                    print('ATLASSIAN_' + str(count) + '.json')

                    for x in data['issues']:
                        s = x['resolution']['status']
                        if s != 'Unresolved':
                            t = x['description'] 
                            if not t is None:
                                data['label'] += [int(s == 'Fixed')]
                                data['text'] += [t]

                    count += 1001
            except Exception as e:
                print('error', e)
                break

        