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

from sklearn.impute import KNNImputer

import datetime
import pickle
import json

import datautil
import debug

class MachineLearningModel:
    def __init__(self, change_requests):
        self.change_requests = change_requests

        from pymongo import MongoClient

        client = MongoClient(tz_aware=True)
        db = client['data-explorer']

        self.collection_data = db['ml_data_set']

        try:
            self.collection_data.create_index([('universe_name', 1), ('change_request_issue_key', 1)], unique=True)
        except Exception as e:
            debug.exception_print(e)
            print('failed to set index on features')

        import gridfs
        self.collection_models = gridfs.GridFS(db, collection='ml_models')

        self.reducers = {
            'No Reduction': None,
            #'Principal Component Analysis': 'PCA(n_components=2, random_state=1)',
            'Linear Discriminant Analysis': 'LinearDiscriminantAnalysis(n_components=2)',
            #'Linear Discriminant Analysis (with shrinkage)': 'LinearDiscriminantAnalysis(n_components=2, solver="eigen", shrinkage="auto")',
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
            #'Nearest Neighbors': 'KNeighborsClassifier(3)',
            #'Linear SVM': '''SVC(kernel='linear', C=0.025)''',
            'Linear SVC': '''LinearSVC(C=0.01, penalty='l1', dual=False)''',
            'Linear SVC (dual)': '''LinearSVC(C=0.01, dual=True)''',
            #'Stochastic Gradient Descent SVM (online)': 'self.sgdclassifier',
            #'Stochastic Gradient Descent SVM (offline)': 'SGDClassifier()',
            #'RBF SVM': 'SVC(gamma=2, C=1, probability=True)',
            #'RBF SVM (imbalance penalty)': '''SVC(gamma=2, C=1, probability=True, class_weight='balanced')''',
            #'Decision Tree': 'DecisionTreeClassifier(max_depth=12*12)',
            #'Decision Tree (imbalance penalty)': '''DecisionTreeClassifier(max_depth=12*12, class_weight='balanced')''',
            #'Random Forest': 'RandomForestClassifier(max_depth=12*12, n_estimators=10)',
            'Random Forest (imbalance penalty)': '''RandomForestClassifier(max_depth=12*12, n_estimators=10, class_weight='balanced')''',
            #'Neural Net': '''MLPClassifier(hidden_layer_sizes=(100,100,100,100,100,100,100,100,100), solver='adam', max_iter=800)''',
            #'AdaBoost': 'AdaBoostClassifier()',
            #'Gaussian Process': 'GaussianProcessClassifier(1.0 * RBF(1.0))',
            #'Naive Bayes': 'GaussianNB()',
            #'QDA': 'QuadraticDiscriminantAnalysis()'
        }

        self.selectors = {
            'All Features': None,
            'Low Variance Elimination': {'selector': 'VarianceThreshold(threshold=(.8 * (1 - .8)))', 'prefit': False},
            'Chi Squared K-Best (10)': {'selector': 'SelectKBest(chi2, k=10)', 'prefit': False},
            #'L1-penalty': {'selector': '''SelectFromModel(trained_models['No Scaling']['No Sampling']['All Features']['No Reduction']['Linear SVC'], prefit=True)''', 'prefit': True},
            #'Random Forest': {'selector': '''SelectFromModel(RandomForestClassifier(max_depth=12*12, n_estimators=10, max_features=10), prefit=False)''', 'prefit': False}
        }

    def get_model_id(self):
        return 'statistical'

    def prepare_data(self, change_request_meta, target_date):
        change_request_issue_key = change_request_meta['issue_key']

        key = {'universe_name': self.change_requests.get_issue_map().get_universe_name(), 'change_request_issue_key': change_request_issue_key}
        data = self.collection_data.find_one({**key, 'target_date': target_date})

        update_features = False
        try:
            label = data['label']
            features = data['features']
        except:
            update_features = True
            label = None
            features = None

        if True:#label is None :
            mlabel = self.change_requests.get_manual_risk_label(change_request_issue_key)
            alabel = self.change_requests.get_automatic_risk_label(change_request_meta)
            label = alabel
            if not mlabel is None:
                label = mlabel

        if features is None:
            update_features = True
            if not label is None and label != 'None':
                extracted_features = self.change_requests.get_extracted_features(change_request_issue_key, target_date)
                extracted_features_meta = extracted_features['Meta']

                features = {
                    'number_of_participants': extracted_features['number_of_participants'],
                    'elapsed_time': extracted_features['elapsed_time'],
                }

                for feature in extracted_features_meta['aggregated_features']:
                    for aggregator_name in extracted_features_meta['aggregators']:
                        features['%s_%s' % (feature, aggregator_name)] = extracted_features[feature][aggregator_name]

        if update_features:
            self.collection_data.update_one(
                key,
                {'$set': {**key, 'target_date': target_date, 'label': label, 'features': features, 'set': None}},
                upsert=True
            )
        else:
            self.collection_data.update_one(
                key,
                {'$set': {'label': label, 'set': None}},
                upsert=True
            )

        return (features,), (label.lower(),)

    def prepare_dataset(self):
        for change_request_meta in self.change_requests.iterate_change_request_meta_map():
            try:
                self.prepare_data(change_request_meta, change_request_meta['release_date'])
            except Exception as e:
                debug.exception_print(e)

    def split_dataset_incremental(self):
        issue_map = self.change_requests.get_issue_map()
        universe_name = issue_map.get_universe_name()
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
        issue_map = self.change_requests.get_issue_map()
        universe_name = issue_map.get_universe_name()

        data = self.collection_data.find(
            {'universe_name': universe_name},
            {'_id': 0, 'change_request_issue_key': 1, 'label': 1})

        X, y = ([], [])
        for d in data:
            if 'label' in d:
                X += (d['change_request_issue_key'],)
                y += (d['label'],)

        if len(X) > 0:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, stratify=y,
                test_size=.5, random_state=1)

            self.collection_data.update_many(
                {'universe_name': universe_name, 'change_request_issue_key': {'$in': X_train}},
                {'$set': {'set': 'training'}},
                upsert=True
            )

            self.collection_data.update_many(
                {'universe_name': universe_name, 'change_request_issue_key': {'$in': X_test}},
                {'$set': {'set': 'test'}},
                upsert=True
            )

    def fit_vectorizer(self):
        issue_map = self.change_requests.get_issue_map()
        universe_name = issue_map.get_universe_name()

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

    def train(self, incremental=False, n='combined', configurations=None, mpqueue=False):
        issue_map = self.change_requests.get_issue_map()
        universe_name = issue_map.get_universe_name()

        if configurations is None:
            configurations = self.get_configuration_permutations()

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

                    self._train(X, y, trained_models, incremental=True, configurations=configurations, mpqueue=mpqueue)
            else:
                X_train, y_train = ([], [])
                for X, y in self.get_dataset_training():
                    X_train += X
                    y_train += y

                X_train, y_train = (np.array(X_train), np.array(y_train))

                X_train = DV.transform(X_train)
                self._train(X_train, y_train, trained_models, incremental=False, configurations=configurations, mpqueue=mpqueue)

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

        except Exception as e:
            debug.exception_print(e)

    def combine_models(self, parts):
        issue_map = self.change_requests.get_issue_map()
        universe_name = issue_map.get_universe_name()

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
                    for sampler_name, samplers_ in scalers_.items():
                        for selector_name, selectors_ in samplers_.items():
                            for reducer_name, reducers_ in selectors_.items():
                                for classifier_name, configuration in reducers_.items():
                                    datautil.map(combined_models, (scaler_name, sampler_name, selector_name, reducer_name, classifier_name), configuration)

            except Exception as e:
                debug.exception_print(e)

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

    def get_configuration_permutations(self):
        configurations = []
        for scaler_name in self.scalers:
            for sampler_name in self.samplers:
                for selector_name in self.selectors:
                    for reducer_name in self.reducers:
                        for classifier_name in self.classifiers:
                            configurations += [{
                                'scaler_name': scaler_name,
                                'sampler_name': sampler_name,
                                'selector_name': selector_name,
                                'reducer_name': reducer_name,
                                'classifier_name': classifier_name
                            }]

        return configurations

    def _train(self, X_train, y_train, trained_models, configurations, incremental, mpqueue):
        cache = {}

        def iterate_configurations(configurations, mpqueue):
            if mpqueue:
                while not configurations.empty():
                    batch = configurations.get()
                    for configuration in batch:
                        yield configuration
            else:
                for configuration in configurations:
                    yield configuration

        for configuration in iterate_configurations(configurations, mpqueue):
            X_ = X_train
            y_ = y_train
            try:
                scaler_ = self.scalers[configuration['scaler_name']]
                sampler_ = self.samplers[configuration['sampler_name']]
                selector_ = self.selectors[configuration['selector_name']]
                reducer_ = self.reducers[configuration['reducer_name']]
                classifier_ = self.classifiers[configuration['classifier_name']]

                scaler = datautil.map_get(cache, (configuration['scaler_name'], 'scaler'), None)
                x = datautil.map_get(cache, (configuration['scaler_name'], 'X_'), None)
                if not x is None:
                    X_ = x
                elif not scaler_ is None:
                    scaler = eval(scaler_)
                    X_ = scaler.fit_transform(X_)
                    datautil.map(cache, (configuration['scaler_name'], 'scaler'), scaler)
                    datautil.map(cache, (configuration['scaler_name'], 'X_'), X_)

                sampler = datautil.map_get(cache, (configuration['scaler_name'], configuration['sampler_name'], 'sampler'), None)
                x = datautil.map_get(cache, (configuration['scaler_name'], configuration['sampler_name'], 'X_'), None)
                y = datautil.map_get(cache, (configuration['scaler_name'], configuration['sampler_name'], 'y_'), None)
                if not x is None and not y is None:
                    X_ = x
                    y_ = y
                elif not sampler_ is None:
                    sampler = eval(sampler_)
                    X_, y_ = sampler.fit_resample(X_, y_)
                    datautil.map(cache, (configuration['scaler_name'], configuration['sampler_name'], 'sampler'), sampler)
                    datautil.map(cache, (configuration['scaler_name'], configuration['sampler_name'], 'X_'), X_)
                    datautil.map(cache, (configuration['scaler_name'], configuration['sampler_name'], 'y_'), y_)

                selector = datautil.map_get(cache, (configuration['scaler_name'], configuration['sampler_name'], configuration['selector_name'], 'selector'), None)
                x = datautil.map_get(cache, (configuration['scaler_name'], configuration['sampler_name'], configuration['selector_name'], 'X_'), None)
                if not x is None:
                    X_ = x
                elif not selector_ is None:
                    selector = eval(selector_['selector'])

                    if not selector_['prefit']:
                        selector.fit(X_, y_)

                    X_ = selector.transform(X_)
                    datautil.map(cache, (configuration['scaler_name'], configuration['sampler_name'], configuration['selector_name'], 'selector'), selector)
                    datautil.map(cache, (configuration['scaler_name'], configuration['sampler_name'], configuration['selector_name'], 'X_'), X_)

                reducer = datautil.map_get(cache, (configuration['scaler_name'], configuration['sampler_name'], configuration['selector_name'], configuration['reducer_name'], 'reducer'), None)
                x = datautil.map_get(cache, (configuration['scaler_name'], configuration['sampler_name'], configuration['selector_name'], configuration['reducer_name'], 'X_'), None)
                if not x is None:
                    X_ = x
                elif not reducer_ is None:
                    reducer = eval(reducer_)
                    X_ = reducer.fit_transform(X_, y_)
                    datautil.map(cache, (configuration['scaler_name'], configuration['sampler_name'], configuration['selector_name'], configuration['reducer_name'], 'reducer'), reducer)
                    datautil.map(cache, (configuration['scaler_name'], configuration['sampler_name'], configuration['selector_name'], configuration['reducer_name'], 'X_'), X_)

                classifier = eval(classifier_)

                if incremental:
                    classifier.partial_fit(X_, y_, classes=['low', 'medium', 'high'])
                else:
                    classifier.fit(X_, y_)

                datautil.map(trained_models, (configuration['scaler_name'], configuration['sampler_name'], configuration['selector_name'], configuration['reducer_name'], configuration['classifier_name']), {
                            'scaler': scaler,
                            'sampler': sampler,
                            'selector': selector,
                            'reducer': reducer,
                            'classifier': classifier
                })

            except Exception as e:
                print('!!!', configuration['scaler_name'], configuration['sampler_name'], configuration['selector_name'], configuration['reducer_name'], configuration['classifier_name'])
                debug.exception_print(e)

    def iterate_test(self, X, X_impute_examples=None, configurations=None):
        DV_bin = self.collection_models.get({
            'universe_name': self.change_requests.get_issue_map().get_universe_name(),
            'model_id': self.get_model_id(),
            'data': 'DV'
        }).read()

        models_bin = self.collection_models.get({
            'universe_name': self.change_requests.get_issue_map().get_universe_name(),
            'model_id': self.get_model_id(),
            'data': 'models',
            'n': 'combined'
        }).read()

        DV = pickle.loads(DV_bin)
        models = pickle.loads(models_bin)

        feature_names_list = self.get_feature_names_list()

        X_in = X

        if not X_impute_examples is None:
            feature_set = set(feature_names_list)
            DVs = []
            for x in X:
                dv = DictVectorizer()
                dv.fit_transform(x)
                DVs += [dv]

            unique_features = [feature_set - set(x.vocabulary_.keys()) for x in DVs]

            missing_features = [dict(zip(f, [None] * len(f))) for f in unique_features]

            X_in = []
            for x in zip(X, missing_features):
                xx = []
                for z in x[0]:
                    xx += [{**z, **x[1]}]
                X_in += [xx]

        X_ = [DV.transform(x) for x in X_in]

        if not X_impute_examples is None:
            imputer = KNNImputer()
            X_impute_examples_ = DV.transform(X_impute_examples)
            imputer.fit(X_impute_examples_)
            X_ = [imputer.transform(x) for x in X_]

        configuration_scalers = None
        configuration_samplers = None
        configuration_selectors = None
        configuration_reducers = None
        configuration_classifiers = None
        if not configurations is None:
            configuration_scalers = set()
            configuration_samplers = set()
            configuration_selectors = set()
            configuration_reducers = set()
            configuration_classifiers = set()

            for configuration in configurations:
                configuration_scalers.add(configuration['scaler_name'])
                configuration_samplers.add(configuration['sampler_name'])
                configuration_selectors.add(configuration['selector_name'])
                configuration_reducers.add(configuration['reducer_name'])
                configuration_classifiers.add(configuration['classifier_name'])

        for scaler_name, scalers_ in models.items():
            if not configuration_scalers is None and not scaler_name in configuration_scalers:
                continue
            for sampler_name, samplers_ in scalers_.items():
                if not configuration_samplers is None and not sampler_name in configuration_samplers:
                    continue
                for selector_name, selectors_ in samplers_.items():
                    if not configuration_selectors is None and not selector_name in configuration_selectors:
                        continue
                    for reducer_name, reducers_ in selectors_.items():
                        if not configuration_reducers is None and not reducer_name in configuration_reducers:
                            continue
                        for classifier_name, configuration in reducers_.items():
                            if not configuration_classifiers is None and not classifier_name in configuration_classifiers:
                                continue

                            X_test = X_
                            if not configuration['scaler'] is None:
                                scaler = configuration['scaler']
                                X_test = [scaler.transform(x) for x in X_test]

                            # X_test = sampler.Don't not resample the test set!

                            selected_feature_names_list = feature_names_list
                            if not configuration['selector'] is None:
                                selector = configuration['selector']
                                X_test = [selector.transform(x) for x in X_test]

                                selected_feature_names_list = []
                                for x, y in zip(feature_names_list, selector.get_support()):
                                    if y == 1:
                                        selected_feature_names_list += [x]

                            reducer = None
                            if not configuration['reducer'] is None:
                                reducer = configuration['reducer']
                                X_test = [reducer.transform(x) for x in X_test]

                            yield {
                                'scaler_name': scaler_name,
                                'sampler_name': sampler_name,
                                'selector_name': selector_name,
                                'reducer_name': reducer_name,
                                'classifier_name': classifier_name,
                                'DV': DV,
                                'scaler': configuration['scaler'],
                                'sampler': configuration['sampler'],
                                'selector': configuration['selector'],
                                'reducer': configuration['reducer'],
                                'classifier': configuration['classifier'],
                                'feature_names_list': feature_names_list,
                                'selected_feature_names_list': selected_feature_names_list,
                                'X': X_test
                            }

    def get_dataset(self):
        for data in self.collection_data.find({'universe_name': self.change_requests.get_issue_map().get_universe_name()}):
            if 'features' in data and 'label' in data:
                yield (data['features'],), ([data['label']],)

    def get_dataset_test(self):
        for data in self.collection_data.find({'universe_name': self.change_requests.get_issue_map().get_universe_name(), 'set': 'test'}):
            if 'features' in data and 'label' in data:
                yield (data['features'],), (data['label'],)

    def get_dataset_training(self):
        for data in self.collection_data.find({'universe_name': self.change_requests.get_issue_map().get_universe_name(), 'set': 'training'}):
            if 'features' in data and 'label' in data:
                yield (data['features'],), (data['label'],)

    def get_feature_names_list(self):
        DV_bin = self.collection_models.get({
            'universe_name': self.change_requests.get_issue_map().get_universe_name(),
            'model_id': self.get_model_id(),
            'data': 'DV'
        }).read()

        DV = pickle.loads(DV_bin)

        try:
            return np.array(datautil.vocabulary_index(DV.vocabulary_))
        except:
            return np.array([])

    def calc_score(self):
        out = {}

        X_test, y_test = ([], [])
        for X, y in self.get_dataset_test():
            X_test += X
            y_test += y

        for x in self.iterate_test([X_test]):
            try:
                name = '%s - %s - %s - %s - %s' % (x['scaler_name'], x['sampler_name'], x['selector_name'], x['reducer_name'], x['classifier_name'])

                y_pred = x['classifier'].predict(x['X'][0])

                cm = metrics.confusion_matrix(y_test, y_pred)

                n = len(x['classifier'].classes_)

                weights = [10,1]
                weighted_matrix = np.zeros((n, n))
                for i, weight in enumerate(weights):
                    weighted_matrix += np.eye(n, n,k=i) * (weight / 2)
                    weighted_matrix += np.eye(n, n,k=-i) * (weight / 2)

                for i in range(n - len(weights)):
                    weighted_matrix[0][i + 1] = weights[i + 1]
                    weighted_matrix[n - 1][n - 2 - i] = weights[n - 2 - i]

                interestingness = np.sum((np.sum(weighted_matrix * cm, axis=0)) / (np.sum(weighted_matrix, axis=0) * np.sum(cm, axis=0)) * 100) / 3

                proportional_score = pow(np.diag(cm) / np.sum(cm, axis=1), 2) / np.array([np.sum(x.transpose() / np.sum(cm, axis=1)) for x in np.split(cm, n, axis=1)]) * 100

                average_proportional_score = np.sum(proportional_score) / n

                out[name] = {
                    'classes': list(x['classifier'].classes_),
                    'interestingness': interestingness,
                    'proportional_score': proportional_score,
                    'average_proportional_score': average_proportional_score,
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
