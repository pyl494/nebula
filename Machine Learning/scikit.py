#imports
import pandas
import glob
from pandas.io.json import json_normalize
import json

#load data
path = r'C:\Users\SATAN\Desktop\321\atlassian'
allFiles = glob.glob(path + "/*.json")
li = []

#debug limit
count = 0

for filename in allFiles:
    if count == 2:
        break
    else:
        count += 1

    #combine comments into one attribute

    print("reading: " + filename)
    data = json.load(open(filename))

    for issue in data['issues']:
        li.append(json_normalize(issue))

print(li[0].head())

data_frame = pandas.concat(li, axis=0, ignore_index=True)

print(data_frame.head())

#process data
from sklearn import preprocessing

le = preprocessing.LabelEncoder()

data = data[data.Creator.notnull()]

#data['Assignee'] = le.fit_transform(data['Assignee'])
data['Creator'] = le.fit_transform(data['Creator'])
data['Reporter'] = le.fit_transform(data['Reporter'])
#data['Component.s'] = le.fit_transform(data['Component.s'])
#data['Labels'] = le.fit_transform(data['Labels'])

data['Resolution'] = le.fit_transform(data['Resolution'])
data['Priority'] = le.fit_transform(data['Priority'])
values = data[['Priority', 'Creator', 'Reporter']]
target = data['Resolution']

from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(values, target, test_size = 0.3, random_state = 0)

#import necessary modules
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score

#create object of the lassifier
gnb = GaussianNB()

#Train the algorithm
pred = gnb.fit(X_train, y_train).predict(X_test)

print("Naive-Bayes accuracy : ", accuracy_score(y_test, pred, normalize = True))