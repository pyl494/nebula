import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import make_moons, make_circles, make_classification
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.feature_extraction import DictVectorizer
from sklearn import metrics
from sklearn.utils.extmath import density
from sklearn.linear_model import SGDClassifier

from sklearn.feature_selection import SelectFromModel
from sklearn.feature_selection import VarianceThreshold
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import chi2
from sklearn.svm import LinearSVC

from imblearn.over_sampling import RandomOverSampler
from imblearn.over_sampling import SMOTE
from imblearn.over_sampling import BorderlineSMOTE
from imblearn.over_sampling import ADASYN
from imblearn.over_sampling import SVMSMOTE
from imblearn.over_sampling import SMOTENC
from imblearn.over_sampling import KMeansSMOTE

from imblearn.under_sampling import ClusterCentroids
from imblearn.under_sampling import RandomUnderSampler
from imblearn.under_sampling import CondensedNearestNeighbour
from imblearn.under_sampling import OneSidedSelection

from sklearn.metrics import roc_auc_score
from sklearn.metrics import average_precision_score

from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import RobustScaler
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import MaxAbsScaler
from sklearn.preprocessing import Normalizer

from change_requests import ChangeRequest
import datautil

import datetime

class MachineLearning:
    def __init__(self, change_requests):
        self.change_requests = change_requests

        from pymongo import MongoClient

        client = MongoClient()
        db = client['data-explorer']

        self.collection = db['ml_data_set']

        try:
            self.collection.create_index([('universe_name', 1), ('change_request_issue_key', 1)], unique=True)
        except Exception as e:
            print('Exception:', str(e))
            print('failed to set index on features')

        self.scalers = {
            'No Scaling': None,
            #'Normalizer (L1)': '''Normalizer(norm='l1')''',
            #'Normalizer (L2)': '''Normalizer(norm='l2')''',
            #'Normalizer (max)': '''Normalizer(norm='max')''',
            #'Standard Scaler': 'StandardScaler(with_mean=True)',
            #'Robust Scaler': 'RobustScaler(with_centering=True)',
            #'Min-Max Scaler': 'MinMaxScaler()',
            #'Max-Abs Scaler': 'MaxAbsScaler()'
        }

        self.samplers = {
            'No Sampling': None,
            #'Oversample - Random Over Sampler': 'RandomOverSampler()',
            #'Oversample - SMOTE': 'SMOTE()',
            #'Oversample - Borderline SMOTE': 'BorderlineSMOTE()',
            #'Oversample - ADASYN': 'ADASYN()',
            #'Oversample - SVMSMOTE': 'SVMSMOTE()',
            #'Oversample - K-means SMOTE': 'KMeansSMOTE()',
            #'Undersample - Random Under Sample': 'RandomUnderSampler()',
            #'Undersample - Clustered Centroids': 'ClusterCentroids()',
            #'Undersample - Condensed Nearest Neighbour': 'CondensedNearestNeighbour()',
            #'Undersample - One Sided Selection': 'OneSidedSelection()'
        }

        self.sgdclassifier = SGDClassifier()

        self.classifiers = {
            #'Nearest Neighbors': 'KNeighborsClassifier(3)',
            #'Linear SVM': '''SVC(kernel='linear', C=0.025)''',
            #'Linear SVC': '''LinearSVC(C=0.01, penalty='l1', dual=False)''',
            'Stochastic Gradient Descent SVM': 'self.sgdclassifier'
            #'RBF SVM': 'SVC(gamma=2, C=1, probability=True)',
            #'RBF SVM (imbalance penalty)': '''SVC(gamma=2, C=1, probability=True, class_weight='balanced')''',
            #'Decision Tree': 'DecisionTreeClassifier(max_depth=12*12)',
            #'Decision Tree (imbalance penalty)': '''DecisionTreeClassifier(max_depth=12*12, class_weight='balanced')''',
            #'Random Forest': 'RandomForestClassifier(max_depth=12*12, n_estimators=10, max_features=10)',
            #'Random Forest (imbalance penalty)': '''RandomForestClassifier(max_depth=12*12, n_estimators=10, max_features=10, class_weight='balanced')''',
            #'Neural Net': '''MLPClassifier(hidden_layer_sizes=(100,100,100,100,100,100,100,100,100), solver='adam', max_iter=800)''',
            #'AdaBoost': 'AdaBoostClassifier()',
            #'Gaussian Process': 'GaussianProcessClassifier(1.0 * RBF(1.0))',
            #'Naive Bayes': 'GaussianNB()',
            #'QDA': 'QuadraticDiscriminantAnalysis()'
        }

        self.feature_selections = {
            'All Features': None,
            #'Low Variance Elimination': {'selector': 'VarianceThreshold(threshold=(.8 * (1 - .8)))', 'prefit': False},
            #'Chi Squared K-Best (10)': {'selector': 'SelectKBest(chi2, k=10)', 'prefit': False},
            #'L1-penalty': {'selector': '''SelectFromModel(trained_models['No Scaling']['No Sampling']['All Features']['Linear SVC'], prefit=True)''', 'prefit': True},
            #'Random Forest': {'selector': '''SelectFromModel(RandomForestClassifier(max_depth=12*12, n_estimators=10, max_features=10), prefit=False)''', 'prefit': False}
        }
    
        self.trained_models = {
            #scaler:{
            #    sampler:{
            #        feature_selector: {
            #             classifier: model
            #        }
            #    }
            # }
        }

        self.DV = DictVectorizer(sparse=False)
        self.DV_fitted = False

    def prepare_data(self, change_request_issue_key, change_request_release_date):
        key = {'universe_name': self.change_requests.getIssueMap().getUniverseName(), 'change_request_issue_key': change_request_issue_key}
        data = self.collection.find_one(key)

        if not data is None:
            try:
                label = data['label']
                features = data['features']
            except:
                label = None
                features = None
        
        if label is None or features is None:
            mlabel = self.change_requests.getManualRiskLabel(change_request_issue_key)
            alabel = self.change_requests.getAutomaticRiskLabel(change_request_issue_key)
            label = alabel
            if not mlabel is None:
                label = mlabel
            
            if not label is None and label != 'None':
                extracted_features = self.change_requests.getExtractedFeatures(change_request_issue_key, change_request_release_date)
                extracted_features_meta = extracted_features['Meta']

                features = {
                    'number_of_issues': extracted_features['number_of_issues'],
                    'number_of_bugs': extracted_features['number_of_bugs'],
                    'number_of_features': extracted_features['number_of_features'],
                    'number_of_improvements': extracted_features['number_of_improvements'],
                    'number_of_other': extracted_features['number_of_other'],
                    'number_of_participants': extracted_features['number_of_participants'],
                    'elapsed_time': extracted_features['elapsed_time'],
                }

                for feature in extracted_features_meta['aggregated_features']:
                    for aggregator_name in extracted_features_meta['aggregators']:
                        features['%s_%s' % (feature, aggregator_name)] = extracted_features[feature][aggregator_name]

                self.collection.update_one(
                    key, 
                    {'$set': {'label': label, 'features': features}}, 
                    upsert=True
                )

        return {'X': [features], 'y': [label.lower()]}

    def train(self):
        change_request_meta_map = self.change_requests.getChangeRequestMetaMap()
        issue_map = self.change_requests.getIssueMap()
        universe_name = issue_map.getUniverseName()

        for change_request_issue_key, change_request_meta in change_request_meta_map.items():
            test_counter += 1

            try:
                data = self.prepare_data(change_request_issue_key, change_request_meta['release_date'])
                X, y = data['X'], data['y']
                
                if not self.DV_fitted:
                    X = self.DV.fit_transform(X)
                else:
                    X = self.DV.transform(X)

                #X_train, X_test, y_train, y_test = train_test_split(
                #    X, y,
                #    test_size=.5, random_state=1)

                if (test_counter % 2) == 0:
                    self.collection.update_one(
                        {'universe_name': universe_name, 'change_request_issue_key': change_request_issue_key}, 
                        {'$set': {'set': 'test'}}, 
                        upsert=True
                    )
                    continue
                else:
                    self.collection.update_one(
                        {'universe_name': universe_name, 'change_request_issue_key': change_request_issue_key}, 
                        {'$set': {'set': 'training'}}, 
                        upsert=True
                    )
                    X_train = X
                    y_train = y

                for scaler_name, scaler_technique in self.scalers.items():

                    X_train_scaled, = X_train
                    if not scaler_technique is None:
                        scaler = eval(scaler_technique)
                        X_train_scaled = scaler.fit_transform(X_train)

                        datautil.map(self.trained_models, (scaler_name, 'scaler'), scaler) 

                    for sampler_name, sampler_technique in self.samplers.items():

                        X_resampled, y_resampled = (X_train_scaled, y_train)

                        if not sampler_technique is None:
                            sampler = eval(sampler_technique)
                            X_resampled, y_resampled = sampler.fit_resample(X_train_scaled, y_train)

                            datautil.map(self.trained_models, (scaler_name, sampler_name, 'sampler'), sampler)

                        for fselector_name, fselector in self.feature_selections.items():

                            try:
                                X_fselected, y_fselected = (X_resampled, y_resampled)

                                if not fselector is None:
                                    selector = eval(fselector['selector'])

                                    if not fselector['prefit']:
                                        selector.fit(X_resampled, y_resampled)

                                    X_fselected = selector.transform(X_resampled)

                                    datautil.map(self.trained_models, (scaler_name, sampler_name, fselector_name, 'selector'), selector)

                                for classifier_name, classifier_technique in self.classifiers.items():

                                    try:
                                        classifier = eval(classifier_technique) 

                                        classifier.partial_fit(X_fselected, y_fselected, classes=['low', 'medium', 'high'])

                                        datautil.map(self.trained_models, (scaler_name, sampler_name, fselector_name, classifier_name), classifier)

                                    except Exception as e:
                                        print(e)
                                        continue

                            except Exception as e:
                                    print(e)
                                    continue

            except Exception as e:
                print(e)
                continue

    def iterate_test(self, X):
        X_ = self.DV.transform(X)

        for scaling_name, scalings_ in self.trained_models.items():
            if not isinstance(scalings_, dict):
                continue
                
            X_scaled = X_
            scaler = None
            if 'scaler' in scalings_:
                scaler = scalings_['scaler']
                X_scaled = scaler.transform(X_)
            
            for sampling_name, samplings_ in scalings_.items():
                if not isinstance(samplings_, dict):
                    continue
                
                X_sampled = X_scaled
                sampler = None
                if 'sampler' in samplings_:
                    sampler = samplings_['sampler']
                
                for fselection_name, fselections_ in samplings_.items():
                    if not isinstance(fselections_, dict):
                        continue
                        
                    X_fselected = X_sampled
                    selector = None
                    if 'selector' in fselections_:
                        selector = fselections_['selector']
                        X_fselected = selector.transform(X_sampled)

                    for classifier_name, classifier in fselections_.items():
                        if classifier_name == 'selector':
                            continue

                        yield {
                            'scaling_name': scaling_name,
                            'sampling_name': sampling_name,
                            'fselection_name': fselection_name,
                            'classifier_name': classifier_name,
                            'scaler': scaler,
                            'sampler': sampler,
                            'selector': selector,
                            'classifier': classifier,
                            'X': X_fselected
                        }

    def calc_score(self, X, y):
        out = {}

        lowi = 1
        medi = 2
        highi = 0

        for x in self.iterate_test(X):
            try:
                name = '%s - %s - %s - %s' % (x['scaling_name'], x['sampling_name'], x['fselection_name'], x['classifier_name'])

                y_pred = x['classifier'].predict(x['X'])

                cm = metrics.confusion_matrix(y, y_pred)

                interestingness = (
                    1 * (cm[lowi][lowi] * 10 + cm[lowi][medi] * 1 + cm[lowi][highi] * 0) / (11 * (cm[lowi][lowi] + cm[lowi][medi] + cm[lowi][highi])) +
                    1 * (cm[medi][lowi] * 0.5 + cm[medi][medi] * 10 + cm[medi][highi] * 0.5) / (11 * (cm[medi][lowi] + cm[medi][medi] + cm[medi][highi])) +
                    1 * (cm[highi][lowi] * 0 + cm[highi][medi] * 1 + cm[highi][highi] * 10) / (11 * (cm[highi][lowi] + cm[highi][medi] + cm[highi][highi]))
                ) / (1 + 1 + 1) * 100

                low_percent_precision = (
                    pow(cm[lowi][lowi] / (cm[lowi][lowi] + cm[lowi][medi] + cm[lowi][highi]), 2) /
                        (cm[lowi][lowi] / (cm[lowi][lowi] + cm[lowi][medi] + cm[lowi][highi]) +
                        cm[medi][lowi] / (cm[medi][lowi] + cm[medi][medi] + cm[medi][highi]) +
                        cm[highi][lowi] / (cm[highi][lowi] + cm[highi][medi] + cm[highi][highi])) * 100
                )
                
                med_percent_precision = ( 
                        pow(cm[medi][medi] / (cm[medi][lowi] + cm[medi][medi] + cm[medi][highi]), 2) /
                        (cm[lowi][medi] / (cm[lowi][lowi] + cm[lowi][medi] + cm[lowi][highi]) +
                        cm[medi][medi] / (cm[medi][lowi] + cm[medi][medi] + cm[medi][highi]) +
                        cm[highi][medi] / (cm[highi][lowi] + cm[highi][medi] + cm[highi][highi])) * 100
                )
                
                high_percent_precision = (
                        pow(cm[highi][highi] / (cm[highi][lowi] + cm[highi][medi] + cm[highi][highi]), 2) /
                        (cm[lowi][highi] / (cm[lowi][lowi] + cm[lowi][medi] + cm[lowi][highi]) +
                        cm[medi][highi] / (cm[medi][lowi] + cm[medi][medi] + cm[medi][highi]) +
                        cm[highi][highi] / (cm[highi][lowi] + cm[highi][medi] + cm[highi][highi])) * 100
                )

                average_percent_precision = (low_percent_precision + med_percent_precision + high_percent_precision) / 3

                out[name] = {
                    'int': interestingness,
                    'low%p': low_percent_precision,
                    'med%p': med_percent_precision,
                    'high%p': high_percent_precision,
                    'avg%p': average_percent_precision,
                    'cm': cm,
                    'classifier': x['classifier'],
                    'selector': x['selector'],
                    'scaler': x['scaler'],
                    'sampler': x['sampler']
                }
                
            except Exception as e:
                print(e)

        return out
