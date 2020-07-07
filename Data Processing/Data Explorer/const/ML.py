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

    names = [
        "Nearest Neighbors", 
        #"Linear SVM", 
        "RBF SVM", 
        #"Gaussian Process",
        "Decision Tree", 
        "Random Forest", 
        "Neural Net", 
        "AdaBoost",
        #"Naive Bayes", 
        #"QDA"
        ]
    
    # ghetto way to initialise
    try:
        if classifiers != None:
            pass
    except Exception as e:
        classifiers = [
            KNeighborsClassifier(3),
            #SVC(kernel="linear", C=0.025),
            SVC(gamma=2, C=1),
            #GaussianProcessClassifier(1.0 * RBF(1.0)),
            DecisionTreeClassifier(max_depth=5),
            RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1),
            MLPClassifier(alpha=1, max_iter=1000),
            AdaBoostClassifier(),
            #GaussianNB(),
            #QuadraticDiscriminantAnalysis()
            ]

    for change_request in change_request_list:
        projects_fixVersion_issue_map = change_request.getProjectsFixVersionIssueMap()
        projects_affectsVersion_issue_map = change_request.getProjectsAffectsVersionIssueMap()
        issue_map = change_request.getIssueMap()
        projects_version_info_map = change_request.getProjectsVersionInfoMap()

        self.send('<h1>%s</h1>' % html.escape(issue_map.getUniverseName()))

        self.send('Preparing data<br/>')
        data = []
        labels = []
        datasets = []

        for project_key, version_info_map in projects_version_info_map.items():
            #break
            if project_key in projects_fixVersion_issue_map:
                    version_issue_map = projects_fixVersion_issue_map[project_key]
                    for version_name, issue in version_issue_map.items():
                        mlabel = change_request.getManualRiskLabel(project_key, version_name)
                        alabel = change_request.getAutomaticRiskLabel(project_key, version_name)
                        label = alabel
                        if not mlabel is None:
                            label = mlabel
                        
                        if not label is None and label != 'None' and version_name in version_issue_map:
                            features = change_request.getExtractedFeatures(project_key, version_name, version_issue_map[version_name])

                            data += [{
                                'number_of_issues': features['number_of_issues'],
                                'number_of_bugs': features['number_of_bugs'],
                                'number_of_features': features['number_of_features'],
                                'number_of_improvements': features['number_of_improvements'],
                                'number_of_other': features['number_of_other'],
                                'number_of_comments': features['number_of_comments'],
                                'discussion_time': features['discussion_time'].days,
                                'number_of_blocked_by_issues': features['number_of_blocked_by_issues'],
                                'number_of_blocks_issues': features['number_of_blocks_issues'],
                                'number_of_participants': features['number_of_participants'],
                                'elapsed_time': features['elapsed_time'].days,
                                'delays': features['delays'].days
                            }]

                            lowlabel = label.lower()
                            if 'low' in lowlabel:
                                labels += [0]
                            elif 'medium' in lowlabel:
                                labels += [1]
                            elif 'high' in lowlabel:
                                labels += [2]
                            else:
                                raise Exception('unexpected label %s %s %s' % (project_key, version_name, label))
        
        if len(labels) == 0:
            self.send('No data !<br/>')
            continue

        datasets = [(data, labels)]

        self.send('Data Prepared !<br/>')

        for ds_cnt, ds in enumerate(datasets):
            try:
                X, y = ds
                X = DictVectorizer(sparse=True).fit_transform(X)
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y,
                    test_size=.5, random_state=1)

                for name, clf in zip(names, classifiers):
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
            except Exception as e:
                self.send(exception_html(e))
                continue

except Exception as e:
    self.send(exception_html(e))

self.send('</body></html>')

exports = {
    'classifiers': classifiers,
    'names': names
}
