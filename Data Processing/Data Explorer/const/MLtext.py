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
    import html

    import datetime
    import numpy as np
    from sklearn.model_selection import train_test_split
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.decomposition import LatentDirichletAllocation, NMF

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

            change_request_data = []
            change_request_labels = []

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
                    change_request_text = []
                    for issue in issue_map.get_issues_by_keys(change_request_meta['linked_issues']):
                        issue_key = issue['key']

                        extracted_features = issue_map.get_extracted_features(issue, version_names, change_request_release_date)
                        if not extracted_features is None:
                            change_request_text += [(datautil.default(extracted_features['summary'], '') + ' ' + datautil.default(extracted_features['description'], '')).replace("'", '')]

                    added = False
                    change_request_data += [change_request_text]
                    change_request_labels += [label]

            g_X_train, g_X_test, g_y_train, g_y_test = train_test_split(change_request_data, change_request_labels,
                stratify=change_request_labels,
                test_size = 0.50
            )

            data = []
            labels = []

            for d, l in zip(g_X_train, g_y_train):
                for x in d:
                    data += [x]
                    labels += [l]

            labels = np.array(labels)

            def train_vec(title, data, labels):
                global train_test_split
                global TfidfVectorizer
                global RandomForestClassifier
                global metrics
                global html

                self.send('<h2>%s Classification</h2>' % title)
                X_train, X_test, y_train, y_test = train_test_split(data, labels,
                    stratify=labels,
                    test_size = 0.50
                )

                #vectorizer = CountVectorizer(stop_words='english', lowercase=False)
                vectorizer = TfidfVectorizer(
                    #ngram_range=(1,5),
                    smooth_idf = False,
                    sublinear_tf = False,
                    norm=None,
                    analyzer = 'word',
                    stop_words='english',
                    strip_accents='unicode',
                    max_df=1.0,
                    min_df=0.0,
                    token_pattern='[a-z][a-z0-9]*',
                    max_features = 200)

                try:
                    global html
                    vectorizer.fit(data)
                    self.send('<h2>%s Text Vocabulary:</h2>%s<br/>' % (title, html.escape(str(vectorizer.vocabulary_))))

                    X_train_vec = vectorizer.transform(X_train).toarray()
                    X_test_vec = vectorizer.transform(X_test).toarray()
                except ValueError:
                    return None

                clf = RandomForestClassifier(n_estimators = 100, max_features='auto', max_depth=200, min_samples_leaf=1,  n_jobs=-1)
                clf.fit(X_train_vec, y_train)

                self.send('<h3>Testing with test set:</h3>')
                score = clf.score(X_test_vec, y_test)
                y_pred = clf.predict(X_test_vec)
                report = metrics.classification_report(y_test, y_pred)
                cm = metrics.confusion_matrix(y_test, y_pred)
                self.send('Score: %s%%<br/>' % str(score * 100))
                self.send('<pre>%s</pre><br/>' % str(report))
                self.send('<pre>%s</pre><br/>' % str(cm))

                self.send('<h3>Testing with training set:</h3>')
                score = clf.score(X_train_vec, y_train)
                y_pred = clf.predict(X_train_vec)
                report = metrics.classification_report(y_train, y_pred)
                cm = metrics.confusion_matrix(y_train, y_pred)
                self.send('Score: %s%%<br/>' % str(score * 100))
                self.send('<pre>%s</pre><br/>' % str(report))
                self.send('<pre>%s</pre><br/>' % str(cm))

                return {'X_train': X_train, 'y_train': y_train, 'X_test': X_test, 'y_test': y_test, 'X_train_vec': X_train_vec, 'X_test_vec': X_test_vec, 'vectorizer': vectorizer, 'clf': clf}

            def test_change_request_vec(title, change_request_data, change_request_labels, vec):
                global train_test_split
                global TfidfVectorizer
                global RandomForestClassifier
                global metrics
                global html
                global np
                global json

                self.send('<h2>%s Change Request Voting</h2>' % title)

                targets = []
                y_pred = []

                for X_test, y_test in zip(change_request_data, change_request_labels):
                    try:
                        X_test_vec = vec['vectorizer'].transform(X_test).toarray()
                    except ValueError:
                        continue

                    pred, count = np.unique(vec['clf'].predict(X_test_vec), return_counts=True)
                    pp = None
                    if count.shape[0] >= 2:
                        count_s = np.argsort(count)

                        count_1 = count[count_s[-1]]
                        count_i = None
                        for i, p in enumerate(pred):
                            if p == y_test:
                                count_i = count[i]
                                break

                        if count_1 == count_i:
                            pp = y_test
                        else:
                            pp = pred[count_s[-1]]
                    else:
                        pp = pred[0]

                    targets += [y_test]
                    y_pred += [pp]

                    #self.send('expected: %s<br/>Most frequent: %s<br/>results:<pre>%s</pre>' % (y_test, pp, str(list(zip(pred, count)))))

                #self.send('<h3>blah</h3>: <pre>%s</pre><br/>' % json.dumps(list(zip(targets, y_pred)), indent=2))

                targets = np.array(targets)
                y_pred = np.array(y_pred)

                report = metrics.classification_report(targets, y_pred)
                cm = metrics.confusion_matrix(targets, y_pred)
                self.send('<pre>%s</pre><br/>' % str(report))
                self.send('<pre>%s</pre><br/>' % str(cm))

            normal = train_vec('Normal', data, labels)

            self.send('<h2>Eliminating Uncertainty...</h2>')

            vectorizer_full = TfidfVectorizer(
                #ngram_range=(1,5),
                smooth_idf = False,
                sublinear_tf = False,
                norm=None,
                analyzer = 'word',
                stop_words='english',
                strip_accents='unicode',
                max_df=1.0,
                min_df=0.0,
                token_pattern='[a-z][a-z0-9]*',
                max_features = 200)

            vectorizer_full.fit(data)
            data_vec = vectorizer_full.transform(data).toarray()

            clf_full = RandomForestClassifier(n_estimators = 200, max_features=100, max_depth=200, min_samples_leaf=1, n_jobs=-1)
            clf_full.fit(data_vec, labels)
            y_pred = clf_full.predict(data_vec)
            y_pred_proba = clf_full.predict_proba(data_vec)

            self.send('<h3>Testing:</h3>')
            score = clf_full.score(data_vec, labels)
            y_pred = clf_full.predict(data_vec)
            report = metrics.classification_report(labels, y_pred)
            cm = metrics.confusion_matrix(labels, y_pred)
            self.send('Score: %s%%<br/>' % str(score * 100))
            self.send('<pre>%s</pre><br/>' % str(report))
            self.send('<pre>%s</pre><br/>' % str(cm))

            self.send('<h2>Classification with certainty...</h2>')

            certain = (y_pred == labels) & (y_pred_proba.max(axis=1) >= 0.7)
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

            certain = train_vec('Certain', certain_data, certain_labels)
            uncertain = train_vec('Uncertain', uncertain_data, uncertain_labels)

            self.send('<h2>Predictions of uncertain set with certain model</h2>')
            score = certain['clf'].score(uncertain['X_test_vec'], uncertain['y_test'])
            y_pred = certain['clf'].predict(uncertain['X_test_vec'])
            report = metrics.classification_report(uncertain['y_test'], y_pred)
            cm = metrics.confusion_matrix(uncertain['y_test'], y_pred)
            self.send('Score: %s%%<br/>' % str(score * 100))
            self.send('<pre>%s</pre><br/>' % str(report))
            self.send('<pre>%s</pre><br/>' % str(cm))

            uncertain_data_vec = uncertain['vectorizer'].transform(data).toarray()
            y_pred = uncertain['clf'].predict(uncertain_data_vec)
            y_pred_proba = uncertain['clf'].predict_proba(uncertain_data_vec)

            y_pred_zip = []
            y_test_l = labels.tolist()
            y_pred_l = y_pred.tolist()
            y_pred_proba_l = y_pred_proba.max(axis=1).tolist()
            labels_f = labels
            for i in range(y_pred.shape[0]):
                y_pred_zip += [(y_test_l[i], y_pred_l[i], y_pred_proba_l[i])]
                if y_pred_proba_l[i] >= 0.7:
                    labels_f[i] = y_pred_l[i]

            #self.send('<pre>%s</pre><br/>' % json.dumps(y_pred_zip, indent=2))

            fudge = train_vec('Fudge', data, labels_f)

            self.send('<h2>Majority Voting of Issue Predictions in Change Requests</h2>')

            test_change_request_vec('Normal', g_X_test, g_y_test, normal)
            test_change_request_vec('Fudge', g_X_test, g_y_test, fudge)

        except Exception as e:
            self.send(debug.exception_html(e))

        try:
            self.send('<h2>Topic Extraction</h2>')
            X_train, X_test, y_train, y_test = train_test_split(data, labels,
                stratify=labels,
                test_size = 0.50
            )

            vectorizer_topics = TfidfVectorizer(
                #ngram_range=(1,5),
                smooth_idf = False,
                sublinear_tf = False,
                norm=None,
                analyzer = 'word',
                stop_words='english',
                strip_accents='unicode',
                max_df=1.0,
                min_df=0.0,
                token_pattern='[a-z][a-z0-9]*',
                max_features = 200)

            vectorizer_topics.fit(X_train)

            X_train_vec = vectorizer_topics.transform(X_train)
            X_test_vec = vectorizer_topics.transform(X_test)

            LDA = LatentDirichletAllocation(
                n_components=100,
                random_state=42,
                n_jobs=-1)#,
            #    learning_method='online',
            #    learning_decay=1.0,
            #    batch_size=500,
            #    max_iter=20,
            #    total_samples=1000000000)
            LDA_X_train_topics = LDA.fit_transform(X_train_vec.todense())

            LDA_clf = RandomForestClassifier(n_estimators = 100, max_features='auto', max_depth=200, min_samples_leaf=1,  n_jobs=-1)
            LDA_clf.fit(LDA_X_train_topics, y_train)

            LDA_X_test_topics = LDA.transform(X_test_vec)

            nmf = NMF(n_components=100, random_state=1,
                beta_loss='kullback-leibler', solver='mu', max_iter=1000, alpha=.1,
                l1_ratio=.5)
            nmf_X_train_topics = nmf.fit_transform(X_train_vec.todense())

            nmf_clf = RandomForestClassifier(n_estimators = 100, max_features='auto', max_depth=200, min_samples_leaf=1,  n_jobs=-1)
            nmf_clf.fit(nmf_X_train_topics, y_train)

            nmf_X_test_topics = nmf.transform(X_test_vec)

            self.send('<h3>Top topics (LDA)</h3>')
            first_topic = LDA.components_[0]
            top_topic_words = first_topic.argsort()[-20:]
            for i in top_topic_words:
                self.send('%s<br/>' % vectorizer_topics.get_feature_names()[i])

            self.send('<h3>Top topics (NMF)</h3>')
            first_topic = nmf.components_[0]
            top_topic_words = first_topic.argsort()[-20:]
            for i in top_topic_words:
                self.send('%s<br/>' % vectorizer_topics.get_feature_names()[i])

            self.send('<h3>Top words per topic (LDA)</h3>')
            topics = []
            for i, topic in enumerate(LDA.components_):
                t = []
                for i in topic.argsort()[-20:]:
                    t += [vectorizer_topics.get_feature_names()[i]]
                topics += [set(t)]
                self.send(f'Top 20 words for topic #{i}:')
                self.send('<pre>%s</pre>' % json.dumps(t, indent=2))
                self.send('<br/>')

            self.send('<h3>Top words per topic (NMF)</h3>')
            topics = []
            for i, topic in enumerate(nmf.components_):
                t = []
                for i in topic.argsort()[-20:]:
                    t += [vectorizer_topics.get_feature_names()[i]]
                topics += [set(t)]
                self.send(f'Top 20 words for topic #{i}:')
                self.send('<pre>%s</pre>' % json.dumps(t, indent=2))
                self.send('<br/>')

            self.send('<h3>Predictions (LDA)</h3>')
            score = LDA_clf.score(LDA_X_test_topics, y_test)
            y_pred = LDA_clf.predict(LDA_X_test_topics)
            report = metrics.classification_report(y_test, y_pred)
            cm = metrics.confusion_matrix(y_test, y_pred)
            self.send('Score: %s%%<br/>' % str(score * 100))
            self.send('<pre>%s</pre><br/>' % str(report))
            self.send('<pre>%s</pre><br/>' % str(cm))

            self.send('<h3>Predictions (NMF)</h3>')
            score = nmf_clf.score(nmf_X_test_topics, y_test)
            y_pred = nmf_clf.predict(nmf_X_test_topics)
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

