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

    import datetime
                        
    # ghetto way to initialise
    try:
        if classifiers != None:
            pass
    except Exception as e:
        pass
    feature_selections = None
    classifiers = {
        "Nearest Neighbors": KNeighborsClassifier(3),
        "Linear SVM": SVC(kernel="linear", C=0.025),
        "Linear SVC": LinearSVC(C=0.01, penalty="l1", dual=False),
        "RBF SVM": SVC(gamma=2, C=1),
        #"Gaussian Process": GaussianProcessClassifier(1.0 * RBF(1.0)),
        "Decision Tree": DecisionTreeClassifier(max_depth=12*12),
        "Random Forest": RandomForestClassifier(max_depth=12*12, n_estimators=10, max_features=10),
        "Neural Net": MLPClassifier(alpha=1, max_iter=1000),
        "AdaBoost": AdaBoostClassifier(),
        #"Naive Bayes": GaussianNB(),
        #"QDA": QuadraticDiscriminantAnalysis()
    }

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

                data += [{
                    'number_of_issues': extracted_features['number_of_issues'],
                    'number_of_bugs': extracted_features['number_of_bugs'],
                    'number_of_features': extracted_features['number_of_features'],
                    'number_of_improvements': extracted_features['number_of_improvements'],
                    'number_of_other': extracted_features['number_of_other'],
                    'number_of_comments': extracted_features['number_of_comments'],
                    'discussion_time': extracted_features['discussion_time'].days,
                    'number_of_blocked_by_issues': extracted_features['number_of_blocked_by_issues'],
                    'number_of_blocks_issues': extracted_features['number_of_blocks_issues'],
                    'number_of_participants': extracted_features['number_of_participants'],
                    'elapsed_time': extracted_features['elapsed_time'].days,
                    'delays': extracted_features['delays'].days
                }]

                lowlabel = label.lower()
                if 'low' in lowlabel:
                    labels += [0]
                elif 'medium' in lowlabel:
                    labels += [1]
                elif 'high' in lowlabel:
                    labels += [2]
                else:
                    raise Exception('unexpected label %s %s %s' % (change_request_project_key, version_name, label))
    
        if len(labels) == 0:
            self.send('No data !<br/>')
            continue

        self.send('Data Prepared !<br/>')

        try:
            X, y = (data, labels)
            DV = DictVectorizer(sparse=True)
            X = DV.fit_transform(X)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=.5, random_state=1)
            
            self.send('<h1>Training</h1>')

            for name, clf in classifiers.items():
                self.send('<h2>%s</h2>' % name)

                clf.fit(X_train, y_train)
                score = clf.score(X_test, y_test) * 100.0
                y_pred = clf.predict(X_test)
                accuracy = metrics.accuracy_score(y_test, y_pred) * 100
                cm = metrics.confusion_matrix(y_test, y_pred)
                report = metrics.classification_report(y_test, y_pred, target_names=['low', 'medium', 'high'])
                dimensionality = None
                d = None
                
                try:
                    if 'coef_' in dir(clf):
                        dimensionality = clf.coef_.shape[1]
                        d = density(clf.coef_)
                except Exception as e:
                    dimensionality = None
                    d = None

                self.send('''
                    Score: {score:.2f}%<br/>
                    Accuracy: {accuracy:.2f}%<br/>
                    Density: {density}<br/>
                    Dimensionality: {dimensionality}<br/>
                    Report: <br/>
                    <pre>{report}</pre>
                    <br/>
                    Confusion Matrix:<br/>
                    <pre>{cm}</pre>
                    <br/>
                    '''.format(
                        score = score,
                        accuracy = accuracy,
                        density = html.escape(str(d)),
                        dimensionality = html.escape(str(dimensionality)),
                        report = html.escape(str(report)),
                        cm = html.escape(str(cm))
                    )
                )

            feature_selections = [
                ("Low Variance Elimination", VarianceThreshold(threshold=(.8 * (1 - .8))), False),
                ("Chi Squared K-Best (10)", SelectKBest(chi2, k=10), False),
                ("L1-penalty", SelectFromModel(classifiers["Linear SVC"], prefit=True), True),
                ("Random Forest", SelectFromModel(classifiers["Random Forest"], prefit=True), True)
            ]

            self.send('<h1>Feature Selection</h1>')

            for name, fs, prefit in feature_selections:
                self.send('<h2>%s</h2>' % name)

                if not prefit:
                    fs.fit(X_train, y_train)

                support = fs.get_support(True)
                self.send('<h3>Included:</h3><ul>')
                for i in support:
                    self.send('<li>%s</li>' % DV.get_feature_names()[i])
                self.send('</ul>')

                self.send('<h3>Excluded:</h3><ul>')
                for i in set(range(len(DV.get_feature_names()))) ^ set(support):
                    self.send('<li>%s</li>' % DV.get_feature_names()[i])
                self.send('</ul>')

        except Exception as e:
            self.send(exception_html(e))
            continue

except Exception as e:
    self.send(exception_html(e))

self.send('</body></html>')

exports = {
    'classifiers': classifiers,
    'feature_selections': feature_selections
}
