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

clf = None
try:
    import datetime
    import time
    import debug
    import datautil

    import datetime
    import numpy as np
    from sklearn.model_selection import train_test_split
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier

    from sklearn import metrics
    import json

    t0 = time.perf_counter()
    for change_request in change_request_list:
        issue_map = change_request.get_issue_map()

        t1 = time.perf_counter()
        universe_name = change_request.get_issue_map().get_universe_name()
        if universe_name != 'Atlassian Ecosystem':
            continue
        self.send('<h1>%s</h1>' % universe_name)

        try:
            if change_request.label_thresholds is None:
                self.send('<h2>Calculating thresholds</h2>')
                change_request.calc_label_thresholds()

            data = []
            labels = []

            for change_request_meta in change_request.iterate_change_request_meta_map():
                change_request_issue_key = change_request_meta['issue_key']
                change_request_project_key = change_request_meta['project_key']
                change_request_release_date = change_request_meta['release_date']
                change_request_project_key = change_request_meta['project_key']
                version_names = change_request.get_project_versions(change_request_project_key)

                mlabel = change_request.get_manual_risk_label(change_request_issue_key)
                alabel = change_request.get_automatic_risk_label(change_request_meta)

                label = alabel
                if not mlabel is None:
                    label = mlabel

                if not label is None and label != 'None':
                    text = []
                    for issue in issue_map.get_issues_by_keys(change_request_meta['linked_issues']):
                        issue_key = issue['key']

                        extracted_features = issue_map.get_extracted_features(issue, version_names, change_request_release_date)
                        if not extracted_features is None:
                            data += [datautil.default(extracted_features['summary'], '') + ' ' + datautil.default(extracted_features['description'], '')]
                            labels += [label]

                    added = False
                    #data += [' .\n\n'.join(text)]
                    #labels += [label]

            labels = np.array(labels)

            #vectorizer = CountVectorizer(stop_words='english', lowercase=False)
            vectorizer = TfidfVectorizer(
                #ngram_range=(1,5),
                smooth_idf = False,
                sublinear_tf = False,
                norm=None,
                analyzer = 'word',
                stop_words='english',
                max_features=100)

            self.send('<h2>Eliminating Uncertainty...</h2>')

            vectorizer.fit(data)
            data_vec = vectorizer.transform(data).toarray()

            clf = RandomForestClassifier(n_estimators = 100)
            clf.fit(data_vec, labels)
            y_pred = clf.predict(data_vec)
            y_pred_proba = clf.predict_proba(data_vec)

            y_test_l = labels.tolist()
            y_pred_l = y_pred.tolist()
            y_pred_proba_l = y_pred_proba.max(axis=1).tolist()
            for i in range(y_pred.shape[0]):
                if y_pred_proba_l[i] >= 0.7:
                    labels[i] = y_pred_l[i]

            self.send('<h2>Classification with certainty...</h2>')

            certain = (y_pred == labels) & (y_pred_proba.max(axis=1) > 0.9)
            certain_data = []
            uncertain_data = []
            for x in enumerate(certain):
                if x[1]:
                    certain_data += [data[x[0]]]
                else:
                    uncertain_data += [data[x[0]]]

            #self.send('<h1>Certain Text:</h1><pre>%s</pre><br/>' % html.escape(json.dumps(certain_data, indent = 2)))

            #self.send('<h1>Uncertain Text:</h1><pre>%s</pre><br/>' % html.escape(json.dumps(uncertain_data, indent = 2)))

            certain_labels = labels[certain]
            uncertain_labels = labels[~certain]

            X_train, X_test, y_train, y_test = train_test_split(certain_data, certain_labels,
                stratify=certain_labels,
                test_size = 0.50
            )

            certain_vectorizer = TfidfVectorizer(
                #ngram_range=(1,5),
                smooth_idf = False,
                sublinear_tf = False,
                norm = None,
                analyzer = 'word',
                stop_words = 'english',
                max_features = 100)
            try:
                certain_vectorizer.fit(certain_data)
                self.send('<h2>Certain Text Vocabulary:</h2>%s<br/>' % html.escape(str(certain_vectorizer.vocabulary_)))

                X_train_vec = certain_vectorizer.transform(X_train).toarray()
                X_test_vec = certain_vectorizer.transform(X_test).toarray()
            except ValueError:
                continue

            certain_clf = RandomForestClassifier(n_estimators = 100)
            certain_clf.fit(X_train_vec, y_train)

            self.send('<h3>Testing with test set:</h3>')
            score = certain_clf.score(X_test_vec, y_test)
            y_pred = certain_clf.predict(X_test_vec)
            report = metrics.classification_report(y_test, y_pred)
            cm = metrics.confusion_matrix(y_test, y_pred)
            self.send('Score: %s%%<br/>' % str(score * 100))
            self.send('<pre>%s</pre><br/>' % str(report))
            self.send('<pre>%s</pre><br/>' % str(cm))

            self.send('<h3>Testing with training set:</h3>')
            score = certain_clf.score(X_train_vec, y_train)
            y_pred = certain_clf.predict(X_train_vec)
            report = metrics.classification_report(y_train, y_pred)
            cm = metrics.confusion_matrix(y_train, y_pred)
            self.send('Score: %s%%<br/>' % str(score * 100))
            self.send('<pre>%s</pre><br/>' % str(report))
            self.send('<pre>%s</pre><br/>' % str(cm))

            X_train, X_test, y_train, y_test = train_test_split(uncertain_data, uncertain_labels,
                stratify=uncertain_labels,
                test_size = 0.50
            )

            uncertain_vectorizer = TfidfVectorizer(
                #ngram_range=(1,5),
                smooth_idf = False,
                sublinear_tf = False,
                norm = None,
                analyzer = 'word',
                stop_words = 'english',
                max_features = 100)
            try:
                uncertain_vectorizer.fit(uncertain_data)
                self.send('<h2>Uncertain Text Vocabulary:</h2>%s<br/>' % html.escape(str(uncertain_vectorizer.vocabulary_)))

                X_train_vec = uncertain_vectorizer.transform(X_train).toarray()
                X_test_vec = uncertain_vectorizer.transform(X_test).toarray()
            except ValueError:
                pass

            uncertain_clf = RandomForestClassifier(n_estimators = 100)
            uncertain_clf.fit(X_train_vec, y_train)

            self.send('<h3>Testing with test set:</h3>')
            score = uncertain_clf.score(X_test_vec, y_test)
            y_pred = uncertain_clf.predict(X_test_vec)
            report = metrics.classification_report(y_test, y_pred)
            cm = metrics.confusion_matrix(y_test, y_pred)
            self.send('Score: %s%%<br/>' % str(score * 100))
            self.send('<pre>%s</pre><br/>' % str(report))
            self.send('<pre>%s</pre><br/>' % str(cm))

            self.send('<h3>Testing with training set:</h3>')
            score = uncertain_clf.score(X_train_vec, y_train)
            y_pred = uncertain_clf.predict(X_train_vec)
            report = metrics.classification_report(y_train, y_pred)
            cm = metrics.confusion_matrix(y_train, y_pred)
            self.send('Score: %s%%<br/>' % str(score * 100))
            self.send('<pre>%s</pre><br/>' % str(report))
            self.send('<pre>%s</pre><br/>' % str(cm))

            self.send('<h2>Predictions of uncertain set with certain model</h2>')
            score = certain_clf.score(X_test_vec, y_test)
            y_pred = certain_clf.predict(X_test_vec)
            report = metrics.classification_report(y_test, y_pred)
            cm = metrics.confusion_matrix(y_test, y_pred)
            self.send('Score: %s%%<br/>' % str(score * 100))
            self.send('<pre>%s</pre><br/>' % str(report))
            self.send('<pre>%s</pre><br/>' % str(cm))

            uncertain_data_vec = uncertain_vectorizer.transform(data).toarray()
            y_pred = uncertain_clf.predict(uncertain_data_vec)
            y_pred_proba = uncertain_clf.predict_proba(uncertain_data_vec)

            y_pred_zip = []
            y_test_l = labels.tolist()
            y_pred_l = y_pred.tolist()
            y_pred_proba_l = y_pred_proba.max(axis=1).tolist()
            for i in range(y_pred.shape[0]):
                y_pred_zip += [(y_test_l[i], y_pred_l[i], y_pred_proba_l[i])]
                if y_pred_proba_l[i] >= 0.7:
                    labels[i] = y_pred_l[i]

            self.send('<pre>%s</pre><br/>' % json.dumps(y_pred_zip, indent=2))

            X_train, X_test, y_train, y_test = train_test_split(data, labels,
                stratify=labels,
                test_size = 0.50
            )

            fudge_vectorizer = TfidfVectorizer(
                #ngram_range=(1,5),
                smooth_idf = False,
                sublinear_tf = False,
                norm = None,
                analyzer = 'word',
                stop_words = 'english',
                max_features = 100)
            try:
                fudge_vectorizer.fit(data)
                self.send('<h2>Fudge Text Vocabulary:</h2>%s<br/>' % html.escape(str(fudge_vectorizer.vocabulary_)))

                X_train_vec = fudge_vectorizer.transform(X_train).toarray()
                X_test_vec = fudge_vectorizer.transform(X_test).toarray()
            except ValueError:
                pass

            fudge_clf = RandomForestClassifier(n_estimators = 100)
            fudge_clf.fit(X_train_vec, y_train)

            self.send('<h2>Predictions of fudge model</h2>')

            score = certain_clf.score(X_test_vec, y_test)
            y_pred = certain_clf.predict(X_test_vec)
            report = metrics.classification_report(y_test, y_pred)
            cm = metrics.confusion_matrix(y_test, y_pred)
            self.send('Score: %s%%<br/>' % str(score * 100))
            self.send('<pre>%s</pre><br/>' % str(report))
            self.send('<pre>%s</pre><br/>' % str(cm))

        except Exception as e:
            self.send(debug.exception_html(e))

        self.send('Timer: %s s<br/>' % str(time.perf_counter() - t0))

except Exception as e:
    self.send(debug.exception_html(e))

self.send('</body></html>')

