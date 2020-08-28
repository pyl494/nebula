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
from sklearn.feature_extraction import DictVectorizer
from sklearn import metrics
from sklearn.utils.extmath import density
from sklearn.linear_model import SGDClassifier

from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.neighbors import NeighborhoodComponentsAnalysis

from sklearn.decomposition import PCA
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

import datetime
import pickle
import json

import datautil
import debug

class MachineLearningModel:
    def __init__(self, change_requests):
        self.change_requests = change_requests

        from pymongo import MongoClient

        client = MongoClient()
        db = client['data-explorer']

        self.collection_data = db['ml_data_set']

        try:
            self.collection_data.create_index([('universe_name', 1), ('change_request_issue_key', 1)], unique=True)
        except Exception as e:
            debug.exception_print(e)
            print('failed to set index on features')

        import gridfs
        self.collection_models = gridfs.GridFS(db, collection='ml_models')

        self.dimensional_reducers = {
            'No Reduction': None,
            'Principal Component Analysis': 'PCA(n_components=2, random_state=1)',
            'Linear Discriminant Analysis': 'LinearDiscriminantAnalysis(n_components=2)',
            'Linear Discriminant Analysis (with shrinkage)': 'LinearDiscriminantAnalysis(n_components=2, solver="eigen", shrinkage="auto")',
            'Neighbourhood Component Analysis': 'NeighborhoodComponentsAnalysis(n_components=2, random_state=1)'
        }

        self.scalers = {
            'No Scaling': None,
            #'Normalizer (L1)': '''Normalizer(norm='l1')''',
            #'Normalizer (L2)': '''Normalizer(norm='l2')''',
            #'Normalizer (max)': '''Normalizer(norm='max')''',
            'Standard Scaler': 'StandardScaler(with_mean=True)',
            'Robust Scaler': 'RobustScaler(with_centering=True)',
            #'Min-Max Scaler': 'MinMaxScaler()',
            #'Max-Abs Scaler': 'MaxAbsScaler()'
        }

        self.samplers = {
            'No Sampling': None,
            #'Oversample - Random Over Sampler': 'RandomOverSampler()',
            #'Oversample - SMOTE': 'SMOTE()',
            #'Oversample - Borderline SMOTE': 'BorderlineSMOTE()',
            'Oversample - ADASYN': 'ADASYN()',
            #'Oversample - SVMSMOTE': 'SVMSMOTE()',
            #'Oversample - K-means SMOTE': 'KMeansSMOTE()',
            'Undersample - Random Under Sample': 'RandomUnderSampler()',
            #'Undersample - Clustered Centroids': 'ClusterCentroids()',
            #'Undersample - Condensed Nearest Neighbour': 'CondensedNearestNeighbour()',
            #'Undersample - One Sided Selection': 'OneSidedSelection()'
        }

        self.sgdclassifier = SGDClassifier()

        self.classifiers = {
            'Nearest Neighbors': 'KNeighborsClassifier(3)',
            #'Linear SVM': '''SVC(kernel='linear', C=0.025)''',
            'Linear SVC': '''LinearSVC(C=0.01, penalty='l1', dual=False)''',
            #'Stochastic Gradient Descent SVM (online)': 'self.sgdclassifier',
            #'Stochastic Gradient Descent SVM (offline)': 'SGDClassifier()',
            #'RBF SVM': 'SVC(gamma=2, C=1, probability=True)',
            #'RBF SVM (imbalance penalty)': '''SVC(gamma=2, C=1, probability=True, class_weight='balanced')''',
            'Decision Tree': 'DecisionTreeClassifier(max_depth=12*12)',
            'Decision Tree (imbalance penalty)': '''DecisionTreeClassifier(max_depth=12*12, class_weight='balanced')''',
            'Random Forest': 'RandomForestClassifier(max_depth=12*12, n_estimators=10)',
            'Random Forest (imbalance penalty)': '''RandomForestClassifier(max_depth=12*12, n_estimators=10, class_weight='balanced')''',
            #'Neural Net': '''MLPClassifier(hidden_layer_sizes=(100,100,100,100,100,100,100,100,100), solver='adam', max_iter=800)''',
            'AdaBoost': 'AdaBoostClassifier()',
            #'Gaussian Process': 'GaussianProcessClassifier(1.0 * RBF(1.0))',
            #'Naive Bayes': 'GaussianNB()',
            #'QDA': 'QuadraticDiscriminantAnalysis()'
        }

        self.feature_selections = {
            'All Features': None,
            'Low Variance Elimination': {'selector': 'VarianceThreshold(threshold=(.8 * (1 - .8)))', 'prefit': False},
            'Chi Squared K-Best (10)': {'selector': 'SelectKBest(chi2, k=10)', 'prefit': False},
            #'L1-penalty': {'selector': '''SelectFromModel(trained_models['No Scaling']['No Sampling']['All Features']['No Reduction']['Linear SVC'], prefit=True)''', 'prefit': True},
            #'Random Forest': {'selector': '''SelectFromModel(RandomForestClassifier(max_depth=12*12, n_estimators=10, max_features=10), prefit=False)''', 'prefit': False}
        }

    def get_model_id(self):
        return 'statistical'

    def prepare_data(self, change_request_issue_key, change_request_release_date):
        key = {'universe_name': self.change_requests.getIssueMap().getUniverseName(), 'change_request_issue_key': change_request_issue_key}
        data = self.collection_data.find_one(key)

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
                    'number_of_participants': extracted_features['number_of_participants'],
                    'elapsed_time': extracted_features['elapsed_time'],
                }

                for feature in extracted_features_meta['aggregated_features']:
                    for aggregator_name in extracted_features_meta['aggregators']:
                        features['%s_%s' % (feature, aggregator_name)] = extracted_features[feature][aggregator_name]

                self.collection_data.update_one(
                    key,
                    {'$set': {'label': label, 'features': features, 'set': None}},
                    upsert=True
                )

        return (features,), (label.lower(),)

    def prepare_dataset(self):
        print('??1')
        for change_request_meta in self.change_requests.iterate_change_request_meta_map():
            change_request_issue_key = change_request_meta['issue_key']
            print('?? ' + change_request_issue_key)
            try:
                self.prepare_data(change_request_issue_key, change_request_meta['release_date'])
            except Exception as e:
                debug.exception_print(e)
        print('??0')

    def split_dataset_incremental(self):
        issue_map = self.change_requests.getIssueMap()
        universe_name = issue_map.getUniverseName()
        test_counter = 0

        for change_request_meta in self.change_requests.iterate_change_request_meta_map():
            change_request_issue_key = change_request_meta['issue_key']
            test_counter += 1

            if (test_counter % 2) == 0:
                self.collection_data.update_one(
                    {'universe_name': universe_name, 'change_request_issue_key': change_request_issue_key},
                    {'$set': {'set': 'test'}},
                    upsert=True
                )
                continue
            else:
                self.collection_data.update_one(
                    {'universe_name': universe_name, 'change_request_issue_key': change_request_issue_key},
                    {'$set': {'set': 'training'}},
                    upsert=True
                )

    def split_dataset(self):
        print('0A')
        issue_map = self.change_requests.getIssueMap()
        universe_name = issue_map.getUniverseName()
        print(universe_name)
        data = self.collection_data.find(
            {'universe_name': universe_name},
            {'_id': 0, 'change_request_issue_key': 1, 'label': 1})
        print('0B')
        X, y = ([], [])
        for d in data:
            print('>>>', d)
            if 'label' in d:
                X += (d['change_request_issue_key'],)
                y += (d['label'],)
        print('==')
        print(X)
        print('==')
        print(y)
        print('==')
        print('0C')
        if len(X) > 0:
            print('0D')
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, stratify=y,
                test_size=.5, random_state=1)
            print(X_train)
            print('===')
            print(X_test)
            print('0E')
            self.collection_data.update_many(
                {'universe_name': universe_name, 'change_request_issue_key': {'$in': X_train}},
                {'$set': {'set': 'training'}},
                upsert=True
            )
            print('0F')
            self.collection_data.update_many(
                {'universe_name': universe_name, 'change_request_issue_key': {'$in': X_test}},
                {'$set': {'set': 'test'}},
                upsert=True
            )
            print('0G')

    def fit_vectorizer(self):
        issue_map = self.change_requests.getIssueMap()
        universe_name = issue_map.getUniverseName()

        X_train, y_train = ([], [])
        for X, y in self.get_dataset_training():
            X_train += X
            y_train += y

        DV = DictVectorizer(sparse=False)
        X_train, y_train = (np.array(X_train), np.array(y_train))
        X_train = DV.fit_transform(X_train)

        key = {
            'universe_name': universe_name,
            'model_id': self.get_model_id(),
            'data': 'DV'
        }

        self.collection_models.delete(key)
        f = self.collection_models.new_file(_id=key)
        f.write(pickle.dumps(DV))
        f.close()

    def train(self, incremental=False, n='combined'):
        issue_map = self.change_requests.getIssueMap()
        universe_name = issue_map.getUniverseName()

        trained_models = {
            #  scaler:{
            #    sampler:{
            #      feature_selector: {
            #         dimension_reducer: {
            #           classifier: model
            #         }
            #      }
            #    }
            #  }
        }

        DV_bin = self.collection_models.get({
            'universe_name': universe_name,
            'model_id': self.get_model_id(),
            'data': 'DV'
        }).read()

        DV = pickle.loads(DV_bin)

        try:
            if incremental:
                for X, y in self.get_dataset_training():
                    X = DV.transform(X)

                    self._train(X, y, trained_models, incremental)
            else:
                print('A')
                X_train, y_train = ([], [])
                for X, y in self.get_dataset_training():
                    X_train += X
                    y_train += y

                X_train, y_train = (np.array(X_train), np.array(y_train))

                print('B')
                X_train = DV.transform(X_train)
                print('C')
                self._train(X_train, y_train, trained_models, incremental)
                print('D')

            print('Z')
            key = {
                'universe_name': universe_name,
                'model_id': self.get_model_id(),
                'data': 'models',
                'n': n
            }

            self.collection_models.delete(key)

            f = self.collection_models.new_file(_id=key)
            f.write(pickle.dumps(trained_models))
            f.close()

            print('Zsuccess!')

        except Exception as e:
            print('F')
            debug.exception_print(e)

    def combine_models(self, parts):
        issue_map = self.change_requests.getIssueMap()
        universe_name = issue_map.getUniverseName()

        combined_models = {}

        for part in parts:
            key = {
                'universe_name': universe_name,
                'model_id': self.get_model_id(),
                'data': 'models',
                'n': part
            }

            try:
                models_bin = self.collection_models.get(key).read()
                models = pickle.loads(models_bin)

                for scaler_name, scalers_ in models.items():
                    if not isinstance(scalers_, dict):
                        continue

                    for sampler_name, samplers_ in scalers_.items():
                        if not isinstance(samplers_, dict):
                            continue

                        for fselection_name, fselections_ in samplers_.items():
                            if not isinstance(fselections_, dict):
                                continue

                            for dimreducer_name, dimreducers_ in fselections_.items():
                                if not isinstance(dimreducers_, dict):
                                    continue

                                for classifier_name, classifier in dimreducers_.items():
                                    if classifier_name == 'reducer':
                                        continue

                                    datautil.map(combined_models, (scaler_name, sampler_name, fselection_name, dimreducer_name, classifier_name), classifier)
            except:
                pass

        key = {
            'universe_name': universe_name,
            'model_id': self.get_model_id(),
            'data': 'models',
            'n': 'combined'
        }

        self.collection_models.delete(key)

        f = self.collection_models.new_file(_id=key)
        f.write(pickle.dumps(combined_models))
        f.close()

    def _train(self, X, y, trained_models, incremental):
        print(X)
        print('==')
        print(y)
        X_train = X
        y_train = y

        for scaler_name, scaler_technique in self.scalers.items():
            X_train_scaled = X_train
            try:
                if not scaler_technique is None:
                    scaler = eval(scaler_technique)
                    X_train_scaled = scaler.fit_transform(X_train)

                    datautil.map(trained_models, (scaler_name, 'scaler'), scaler)

                for sampler_name, sampler_technique in self.samplers.items():
                    X_resampled, y_resampled = (X_train_scaled, y_train)
                    try:
                        if not sampler_technique is None:
                            sampler = eval(sampler_technique)
                            X_resampled, y_resampled = sampler.fit_resample(X_train_scaled, y_train)

                            datautil.map(trained_models, (scaler_name, sampler_name, 'sampler'), sampler)

                        for fselector_name, fselector in self.feature_selections.items():
                            try:
                                X_fselected, y_fselected = (X_resampled, y_resampled)

                                if not fselector is None:
                                    selector = eval(fselector['selector'])

                                    if not fselector['prefit']:
                                        selector.fit(X_resampled, y_resampled)

                                    X_fselected = selector.transform(X_resampled)

                                    datautil.map(trained_models, (scaler_name, sampler_name, fselector_name, 'selector'), selector)

                                for dimreducer_name, dimreducer in self.dimensional_reducers.items():

                                    try:
                                        X_dimreduced, y_dimreduced = (X_fselected, y_fselected)

                                        if not dimreducer is None:
                                            reducer = eval(dimreducer)

                                            reducer.fit(X_fselected, y_fselected)
                                            X_dimreduced = reducer.transform(X_fselected)

                                            datautil.map(trained_models, (scaler_name, sampler_name, fselector_name, dimreducer_name, 'reducer'), reducer)

                                        for classifier_name, classifier_technique in self.classifiers.items():
                                            try:
                                                classifier = eval(classifier_technique)

                                                if incremental:
                                                    classifier.partial_fit(X_dimreduced, y_dimreduced, classes=['low', 'medium', 'high'])
                                                else:
                                                    classifier.fit(X_dimreduced, y_dimreduced)

                                                datautil.map(trained_models, (scaler_name, sampler_name, fselector_name, dimreducer_name, classifier_name), classifier)

                                            except Exception as e:
                                                print('!!!', scaler_name, sampler_name, fselector_name, dimreducer_name, classifier_name)
                                                debug.exception_print(e)
                                                continue

                                    except Exception as e:
                                        print('!!!', scaler_name, sampler_name, fselector_name, dimreducer_name)
                                        debug.exception_print(e)
                                        continue

                            except Exception as e:
                                print('!!!', scaler_name, sampler_name, fselector_name)
                                debug.exception_print(e)
                                continue

                    except Exception as e:
                        print('!!!', scaler_name, sampler_name, fselector_name, dimreducer_name)
                        debug.exception_print(e)
                        continue

            except Exception as e:
                print('!!!', scaler_name, sampler_name, fselector_name, dimreducer_name)
                debug.exception_print(e)
                continue

    def iterate_test(self, X):
        DV_bin = self.collection_models.get({
            'universe_name': self.change_requests.getIssueMap().getUniverseName(),
            'model_id': self.get_model_id(),
            'data': 'DV'
        }).read()

        models_bin = self.collection_models.get({
            'universe_name': self.change_requests.getIssueMap().getUniverseName(),
            'model_id': self.get_model_id(),
            'data': 'models',
            'n': 'combined'
        }).read()

        DV = pickle.loads(DV_bin)
        models = pickle.loads(models_bin)

        X_ = [DV.transform(x) for x in X]

        feature_names_list = self.get_feature_names_list()

        for scaler_name, scalers_ in models.items():
            if not isinstance(scalers_, dict):
                continue

            X_scaled = [x for x in X_]
            scaler = None
            if 'scaler' in scalers_:
                scaler = scalers_['scaler']
                X_scaled = [scaler.transform(x) for x in X_]

            for sampler_name, samplers_ in scalers_.items():
                if not isinstance(samplers_, dict):
                    continue

                X_sampled = [x for x in X_scaled]
                sampler = None
                if 'sampler' in samplers_:
                    sampler = samplers_['sampler']

                for fselection_name, fselections_ in samplers_.items():
                    if not isinstance(fselections_, dict):
                        continue

                    selected_feature_names_list = feature_names_list
                    X_fselected = [x for x in X_sampled]
                    selector = None

                    if 'selector' in fselections_:
                        selector = fselections_['selector']
                        X_fselected = [selector.transform(x) for x in X_sampled]

                        selected_feature_names_list = []
                        for x, y in zip(feature_names_list, fselections_['selector'].get_support()):
                            if y == 1:
                                selected_feature_names_list += [x]

                    for dimreducer_name, dimreducers_ in fselections_.items():
                        if not isinstance(dimreducers_, dict):
                            continue

                        X_dimreduced = [x for x in X_fselected]
                        reducer = None

                        if 'reducer' in dimreducers_:
                            reducer = dimreducers_['reducer']
                            X_dimreduced = [reducer.transform(x) for x in X_fselected]

                        for classifier_name, classifier in dimreducers_.items():
                            if classifier_name == 'reducer':
                                continue

                            yield {
                                'scaler_name': scaler_name,
                                'sampler_name': sampler_name,
                                'fselection_name': fselection_name,
                                'dimreducer_name': dimreducer_name,
                                'classifier_name': classifier_name,
                                'DV': DV,
                                'scaler': scaler,
                                'sampler': sampler,
                                'selector': selector,
                                'reducer': reducer,
                                'classifier': classifier,
                                'feature_names_list': feature_names_list,
                                'selected_feature_names_list': selected_feature_names_list,
                                'X': X_dimreduced
                            }

    def get_dataset(self):
        for data in self.collection_data.find({'universe_name': self.change_requests.getIssueMap().getUniverseName()}):
            if 'features' in data and 'label' in data:
                yield (data['features'],), ([data['label']],)

    def get_dataset_test(self):
        for data in self.collection_data.find({'universe_name': self.change_requests.getIssueMap().getUniverseName(), 'set': 'test'}):
            if 'features' in data and 'label' in data:
                yield (data['features'],), (data['label'],)

    def get_dataset_training(self):
        for data in self.collection_data.find({'universe_name': self.change_requests.getIssueMap().getUniverseName(), 'set': 'training'}):
            if 'features' in data and 'label' in data:
                yield (data['features'],), (data['label'],)

    def get_feature_names_list(self):
        DV_bin = self.collection_models.get({
            'universe_name': self.change_requests.getIssueMap().getUniverseName(),
            'model_id': self.get_model_id(),
            'data': 'DV'
        }).read()

        DV = pickle.loads(DV_bin)

        try:
            return np.array(list(DV.vocabulary_.keys()))
        except:
            return np.array([])

    def calc_score(self):
        out = {}

        lowi = 1
        medi = 2
        highi = 0

        X_test, y_test = ([], [])
        for X, y in self.get_dataset_test():
            X_test += X
            y_test += y

        for x in self.iterate_test([X_test]):
            try:
                name = '%s - %s - %s - %s - %s' % (x['scaler_name'], x['sampler_name'], x['fselection_name'], x['dimreducer_name'], x['classifier_name'])

                y_pred = x['classifier'].predict(x['X'][0])

                cm = metrics.confusion_matrix(y_test, y_pred)

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
                    'DV': x['DV'],
                    'classifier': x['classifier'],
                    'selector': x['selector'],
                    'scaler': x['scaler'],
                    'reducer': x['reducer'],
                    'sampler': x['sampler'],
                    'feature_names_list': x['feature_names_list'],
                    'selected_feature_names_list': x['selected_feature_names_list']
                }

            except Exception as e:
                debug.exception_print(e)

        return out
