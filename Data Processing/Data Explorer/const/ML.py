self.send_response(200)
self.send_header("Content-type", "text/html")
self.end_headers()
self.send(
    """
    <html>
        <head>
            <title>Explorer</title>
            <link rel="stylesheet" href="/css" media="all">
        </head>
        <body>""")

try:
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

    from sklearn.preprocessing import label_binarize
    from sklearn.multiclass import OneVsRestClassifier

    from sklearn.metrics import precision_recall_curve
    from sklearn.metrics import roc_curve
    from sklearn.metrics import average_precision_score
    import matplotlib.pyplot as plt

    from change_requests import ChangeRequest
    import datautil

    import datetime
                        
    # ghetto way to initialise
    try:
        if classifiers != None:
            pass
    except Exception as e:
        pass

    if True:
        scalers = {
            'No Scaling': None,
            #'Normalizer (L1)': '''Normalizer(norm='l1')''',
            #'Normalizer (L2)': '''Normalizer(norm='l2')''',
            #'Normalizer (max)': '''Normalizer(norm='max')''',
            #'Standard Scaler': 'StandardScaler(with_mean=True)',
            'Robust Scaler': 'RobustScaler(with_centering=True)',
            #'Min-Max Scaler': 'MinMaxScaler()',
            #'Max-Abs Scaler': 'MaxAbsScaler()'
        }

        samplers = {
            'No Sampling': None,
            #'Oversample - Random Over Sampler': 'RandomOverSampler()',
            #'Oversample - SMOTE': 'SMOTE()',
            #'Oversample - Borderline SMOTE': 'BorderlineSMOTE()',
            #'Oversample - ADASYN': 'ADASYN()',
            #'Oversample - SVMSMOTE': 'SVMSMOTE()',
            #'Oversample - K-means SMOTE': 'KMeansSMOTE()',
            'Undersample - Random Under Sample': 'RandomUnderSampler()',
            #'Undersample - Clustered Cetroids': 'ClusterCentroids()',
            #'Undersample - Condensed Nearest Neighbour': 'CondensedNearestNeighbour()',
            #'Undersample - One Sided Selection': 'OneSidedSelection()'
        }

        classifiers = {
            #'Nearest Neighbors': 'KNeighborsClassifier(3)',
            #'Linear SVM': '''SVC(kernel='linear', C=0.025)''',
            #'Linear SVC': '''LinearSVC(C=0.01, penalty='l1', dual=False)''',
            #'RBF SVM': 'SVC(gamma=2, C=1, probability=True)',
            #'RBF SVM (imbalance penalty)': '''SVC(gamma=2, C=1, probability=True, class_weight='balanced')''',
            #'Decision Tree': 'DecisionTreeClassifier(max_depth=12*12)',
            #'Decision Tree (imbalance penalty)': '''DecisionTreeClassifier(max_depth=12*12, class_weight='balanced')''',
            'Random Forest': 'RandomForestClassifier(max_depth=12*12, n_estimators=100, max_features=100)',
            'Random Forest (imbalance penalty)': '''RandomForestClassifier(max_depth=12*12, n_estimators=100, max_features=100, class_weight='balanced')''',
            #'Neural Net': '''MLPClassifier(hidden_layer_sizes=(100,100,100,100,100,100,100,100,100), solver='adam', max_iter=800)''',
            #'AdaBoost': 'AdaBoostClassifier()',
            #'Gaussian Process': 'GaussianProcessClassifier(1.0 * RBF(1.0))',
            #'Naive Bayes': 'GaussianNB()',
            #'QDA': 'QuadraticDiscriminantAnalysis()'
        }

        feature_selections = {
            'All Features': None,
            #'Low Variance Elimination': {'selector': 'VarianceThreshold(threshold=(.8 * (1 - .8)))', 'prefit': False},
            #'Chi Squared K-Best (10)': {'selector': 'SelectKBest(chi2, k=10)', 'prefit': False},
            #'L1-penalty': {'selector': '''SelectFromModel(trained_models['No Scaling']['No Sampling']['All Features']['Linear SVC'], prefit=True)''', 'prefit': True},
            'Random Forest': {'selector': '''SelectFromModel(trained_models['No Scaling']['No Sampling']['All Features']['Random Forest'], prefit=True)''', 'prefit': True}
        }
    
        trained_models = {
            #scaler:{
            #    sampler:{
            #        feature_selector: {
            #             classifier: model
            #        }
            #    }
            # }
        }

        DV = DictVectorizer(sparse=False)

    X_train, y_train, X_test, Y_test = (None, None, None, None)

    self.send('<h1>Preparing Data</h1>')

    for change_request in change_request_list:
        change_request_meta_map = change_request.getChangeRequestMetaMap()
        issue_map = change_request.getIssueMap()
        projects_version_info_map = change_request.getProjectsVersionInfoMap()

        self.send('<h2>%s</h2>' % html.escape(issue_map.getUniverseName()))

        self.send('Preparing data<br/>')
        data = []
        labels = []
        datasets = []

        for change_request_issue_key, change_request_meta in change_request_meta_map.items():
            change_request_project_key = change_request_meta['project_key']

            mlabel = change_request.getManualRiskLabel(change_request_issue_key)
            alabel = change_request.getAutomaticRiskLabel(change_request_issue_key)
            label = alabel
            if not mlabel is None:
                label = mlabel
            
            if not label is None and label != 'None':
                extracted_features = change_request.getExtractedFeatures(change_request_issue_key, datetime.datetime.now(tz=datetime.timezone.utc))
                extracted_features_meta = extracted_features['Meta']

                features = {
                    'number_of_issues': extracted_features['number_of_issues'],
                    'number_of_bugs': extracted_features['number_of_bugs'],
                    'number_of_features': extracted_features['number_of_features'],
                    'number_of_improvements': extracted_features['number_of_improvements'],
                    'number_of_other': extracted_features['number_of_other'],
                    'number_of_participants': extracted_features['number_of_participants'],
                    'elapsed_time': extracted_features['elapsed_time'].total_seconds(),
                }

                for feature in extracted_features_meta['aggregated_features']:
                    for aggregator_name in extracted_features_meta['aggregators']:
                        features['%s_%s' % (feature, aggregator_name)] = extracted_features[feature][aggregator_name]

                data += [features]

                labels += [label.lower()]
    
        if len(labels) == 0:
            self.send('No data !<br/>')
            continue

        self.send('Data Prepared !<br/>')

        try:
            X, y = (data, labels)

            n_classes = len(set(y))
            
            X = DV.fit_transform(X)

            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=.5, random_state=1)

            y_test_binarized = label_binarize(y_test, classes=['low', 'medium', 'high'])

            for scaler_name, scaler_technique in scalers.items():
                self.send('<h1>%s</h1>' % scaler_name)
  
                X_train_scaled, X_test_scaled = (X_train, X_test)
                if not scaler_technique is None:
                    scaler = eval(scaler_technique)
                    X_train_scaled = scaler.fit_transform(X_train)
                    X_test_scaled = scaler.transform(X_test)

                    datautil.map(trained_models, (scaler_name, 'scaler'), scaler) 

                for sampler_name, sampler_technique in samplers.items():
                    self.send('<h2>%s</h2>' % sampler_name)

                    X_resampled, y_resampled = (X_train_scaled, y_train)
                    y_train_binarized = None

                    if not sampler_technique is None:
                        sampler = eval(sampler_technique)
                        X_resampled, y_resampled = sampler.fit_resample(X_train_scaled, y_train)

                        y_train_binarized = label_binarize(y_resampled, classes=['low', 'medium', 'high'])

                        datautil.map(trained_models, (scaler_name, sampler_name, 'sampler'), sampler)
                    else:
                        y_train_binarized = label_binarize(y_train, classes=['low', 'medium', 'high'])

                    self.send('<h3>Training</h3>')

                    for fselector_name, fselector in feature_selections.items():
                        self.send('<h4>%s</h4>' % fselector_name)
                        
                        try:
                            X_fselected, y_fselected = (X_resampled, y_resampled)
                            X_test_fselected = X_test_scaled

                            if not fselector is None:
                                selector = eval(fselector['selector'])

                                if not fselector['prefit']:
                                    selector.fit(X_resampled, y_resampled)

                                X_fselected = selector.transform(X_resampled)

                                X_test_fselected = selector.transform(X_test_scaled)

                                datautil.map(trained_models, (scaler_name, sampler_name, fselector_name, 'selector'), selector)

                            for classifier_name, classifier_technique in classifiers.items():
                                self.send('<h5>%s</h5>' % classifier_name)

                                name = '%s - %s - %s - %s' % (scaler_name, sampler_name, fselector_name, classifier_name)

                                try:
                                    classifier = eval(classifier_technique)

                                    classifier.fit(X_fselected, y_fselected)

                                    datautil.map(trained_models, (scaler_name, sampler_name, fselector_name, classifier_name), classifier)

                                    score = classifier.score(X_test_fselected, y_test) * 100.0
                                    y_pred = classifier.predict(X_test_fselected)

                                    accuracy = metrics.accuracy_score(y_test, y_pred) * 100
                                    cm = metrics.confusion_matrix(y_test, y_pred)
                                    report = metrics.classification_report(y_test, y_pred)
                                    dimensionality = None
                                    d = None

                                    roc_score_ovr = -1
                                    roc_score_ovo = -1

                                    figfilename = TEMP_DIR + name + '_1.png'
                                    figfilename_roc = TEMP_DIR + name + '_roc.png'
                                    figfilename_3 = TEMP_DIR + name + '_prec_recall.png'
                                    figfilename_4 = TEMP_DIR + name + '_multi.png'

                                    try:
                                        y_prob = classifier.predict_proba(X_test_fselected)

                                        try:
                                            roc_score_ovr = roc_auc_score(y_test, y_prob, average='weighted', multi_class='ovr')
                                            roc_score_ovo = roc_auc_score(y_test, y_prob, average='weighted', multi_class='ovo')
                                        except:
                                            pass
                                        
                                        try:
                                            ovr = OneVsRestClassifier(eval(classifier_technique))
                                            ovr.fit(X_fselected, y_train_binarized)

                                            y_score = ovr.predict_proba(X_test_fselected)

                                            # precision recall curve
                                            precision = dict()
                                            recall = dict()
                                            
                                            plt.figure()
                                            for i in range(n_classes):
                                                precision[i], recall[i], _ = precision_recall_curve(y_test_binarized[:, i],
                                                                                                    y_score[:, i])
                                                plt.plot(recall[i], precision[i], lw=2, label=['low', 'medium', 'high'][i])

                                            plt.xlabel("recall")
                                            plt.ylabel("precision")
                                            plt.legend(loc="best")
                                            plt.title("precision vs. recall curve")
                                            plt.savefig(figfilename)

                                            #
                                            fpr = dict()
                                            tpr = dict()
                                            plt.figure()
                                            for i in range(n_classes):
                                                fpr[i], tpr[i], _ = roc_curve(y_test_binarized[:, i],
                                                                            y_score[:, i])
                                                plt.plot(fpr[i], tpr[i], lw=2, label=['low', 'medium', 'high'][i])

                                            plt.xlabel("false positive rate")
                                            plt.ylabel("true positive rate")
                                            plt.legend(loc="best")
                                            plt.title("ROC curve")
                                            plt.savefig(figfilename_roc)

                                        except Exception as e:
                                            self.send(exception_html(e))
                                        
                                        try:
                                            #
                                            try:
                                                y_score = ovr.decision_function(X_test_fselected)
                                            except:
                                                y_score = ovr.predict_proba(X_test_fselected)

                                            precision = dict()
                                            recall = dict()
                                            average_precision = dict()

                                            plt.figure()
                                            for i in range(n_classes):
                                                precision[i], recall[i], _ = precision_recall_curve(y_test_binarized[:, i],
                                                                                                    y_score[:, i])
                                                average_precision[i] = average_precision_score(y_test_binarized[:, i], y_score[:, i])

                                            # A "micro-average": quantifying score on all classes jointly
                                            precision["micro"], recall["micro"], _ = precision_recall_curve(y_test_binarized.ravel(),
                                                y_score.ravel())
                                            average_precision["micro"] = average_precision_score(y_test_binarized, y_score,
                                                                                                average="micro")

                                            plt.step(recall['micro'], precision['micro'], where='post')

                                            plt.xlabel('Recall')
                                            plt.ylabel('Precision')
                                            plt.ylim([0.0, 1.05])
                                            plt.xlim([0.0, 1.0])
                                            plt.title(
                                                'Average precision score, micro-averaged over all classes: AP={0:0.2f}'
                                                .format(average_precision["micro"]))

                                            plt.savefig(figfilename_3)
                                        

                                            #
                                            from itertools import cycle
                                            # setup plot details
                                            colors = cycle(['navy', 'turquoise', 'darkorange', 'cornflowerblue', 'teal'])

                                            plt.figure(figsize=(7, 8))
                                            f_scores = np.linspace(0.2, 0.8, num=4)
                                            lines = []
                                            labels = []
                                            for f_score in f_scores:
                                                x = np.linspace(0.01, 1)
                                                y = f_score * x / (2 * x - f_score)
                                                l, = plt.plot(x[y >= 0], y[y >= 0], color='gray', alpha=0.2)
                                                plt.annotate('f1={0:0.1f}'.format(f_score), xy=(0.9, y[45] + 0.02))

                                            lines.append(l)
                                            labels.append('iso-f1 curves')
                                            l, = plt.plot(recall["micro"], precision["micro"], color='gold', lw=2)
                                            lines.append(l)
                                            labels.append('micro-average Precision-recall (area = {0:0.2f})'
                                                        ''.format(average_precision["micro"]))

                                            for i, color in zip(range(n_classes), colors):
                                                l, = plt.plot(recall[i], precision[i], color=color, lw=2)
                                                lines.append(l)
                                                labels.append('Precision-recall for class {0} (area = {1:0.2f})'
                                                            ''.format(['low', 'medium', 'high'][i], average_precision[i]))

                                            fig = plt.gcf()
                                            fig.subplots_adjust(bottom=0.25)
                                            plt.xlim([0.0, 1.0])
                                            plt.ylim([0.0, 1.05])
                                            plt.xlabel('Recall')
                                            plt.ylabel('Precision')
                                            plt.title('Extension of Precision-Recall curve to multi-class')
                                            plt.legend(lines, labels, loc=(0, -.38), prop=dict(size=14))
                                            plt.savefig(figfilename_4)
  
                                        except Exception as e:
                                            self.send(exception_html(e))

                                    except:
                                        pass                    
                                    
                                    try:
                                        if 'coef_' in dir(classifier):
                                            dimensionality = classifier.coef_.shape[1]
                                            d = density(classifier.coef_)
                                    except Exception as e:
                                        dimensionality = None
                                        d = None

                                    self.send('''
                                        Score: {score:.2f}%<br/>
                                        ROC Area-Under-Curve (ovr): {roc_score_ovr:.2f}%<br/>
                                        ROC Area-Under-Curve (ovo): {roc_score_ovo:.2f}%<br/>
                                        Density: {density}<br/>
                                        Dimensionality: {dimensionality}<br/>
                                        Report: <br/>
                                        <pre>{report}</pre>
                                        <br/>
                                        Confusion Matrix:<br/>
                                        <pre>{cm}</pre>
                                        <br/>
                                        <img src="static?filename=Data Processing/{figfilename}&contenttype=image/png"><br/>
                                        <img src="static?filename=Data Processing/{figfilename_roc}&contenttype=image/png"><br/>
                                        <img src="static?filename=Data Processing/{figfilename_3}&contenttype=image/png"><br/>
                                        <img src="static?filename=Data Processing/{figfilename_4}&contenttype=image/png"><br/>
                                        '''.format(
                                            score = score,
                                            roc_score_ovr = roc_score_ovr * 100,
                                            roc_score_ovo = roc_score_ovo * 100,
                                            density = html.escape(str(d)),
                                            dimensionality = html.escape(str(dimensionality)),
                                            report = html.escape(str(report)),
                                            cm = html.escape(str(cm)),
                                            figfilename = figfilename,
                                            figfilename_roc = figfilename_roc,
                                            figfilename_3 = figfilename_3,
                                            figfilename_4 = figfilename_4
                                        )
                                    )

                                #self.send('<h4>Feature Selection</h4>')

                                #for name, fs, prefit in feature_selections:
                                #    self.send('<h5>%s</h5>' % name)

                                #    if not prefit:
                                #        fs.fit(X_resampled, y_resampled)

                                #    support = fs.get_support(True)
                                #    self.send('<h6>Included:</h6><ul>')
                                #    for i in support:
                                #        self.send('<li>%s</li>' % DV.get_feature_names()[i])
                                #    self.send('</ul>')

                                #    self.send('<h6>Excluded:</h6><ul>')
                                #    for i in set(range(len(DV.get_feature_names()))) ^ set(support):
                                #        self.send('<li>%s</li>' % DV.get_feature_names()[i])
                                #    self.send('</ul>')
                                except Exception as e:
                                    self.send(exception_html(e))
                                    continue

                        except Exception as e:
                                self.send(exception_html(e))
                                continue

        except Exception as e:
            self.send(exception_html(e))
            continue

except Exception as e:
    self.send(exception_html(e))

self.send('</body></html>')

exports = {
    'classifiers': classifiers,
    'feature_selections': feature_selections,
    'scalers': scalers,
    'samplers': samplers,
    'trained_models': trained_models,
    'train_data_set': (X_train, y_train),
    'test_data_set': (X_test, y_test),
    'DV': DV
}
