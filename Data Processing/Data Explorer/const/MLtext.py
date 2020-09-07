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

    t0 = time.perf_counter()
    for change_request in change_request_list:
        issue_map = change_request.get_issue_map()

        t1 = time.perf_counter()
        universe_name = change_request.get_issue_map().get_universe_name()
        self.send('<h1>%s</h1>' % universe_name)
        try:
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
                            text += [datautil.default(extracted_features['summary'], '') + ' ' + datautil.default(extracted_features['description'], '')]

                    added = False
                    data += [' .\n\n'.join(text)]
                    labels += [label]

            #vectorizer = CountVectorizer(stop_words='english', lowercase=False)
            vectorizer = TfidfVectorizer(
                #ngram_range=(3,5),
                smooth_idf = False,
                sublinear_tf = False,
                norm=None,
                analyzer = 'word',
                max_features=10)

            X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size = 0.5)

            try:
                vectorizer.fit(data)
                X_train_vec = vectorizer.transform(X_train).toarray()
                X_test_vec = vectorizer.transform(X_test).toarray()
            except ValueError:
                continue

            forest = RandomForestClassifier(n_estimators = 100)
            clf=forest.fit(X_train_vec, y_train)
            score = clf.score(X_test_vec, y_test)
            y_pred = clf.predict(X_test_vec)
            report = metrics.classification_report(y_test, y_pred)
            self.send('Score: %s%%<br/>' % str(score * 100))
            self.send('<pre>%s</pre><br/>' % str(report))

        except Exception as e:
            self.send(debug.exception_html(e))

        self.send('Timer: %s s<br/>' % str(time.perf_counter() - t0))

except Exception as e:
    self.send(debug.exception_html(e))

self.send('</body></html>')

exports = {
}
