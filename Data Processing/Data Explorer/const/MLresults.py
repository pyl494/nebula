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
    from sklearn import metrics

    from sklearn.preprocessing import label_binarize
    from sklearn.multiclass import OneVsRestClassifier

    from sklearn.metrics import precision_recall_curve
    from sklearn.metrics import roc_curve
    from sklearn.metrics import average_precision_score

    import matplotlib.pyplot as plt

    import copy

    import debug

    for change_request in change_request_list:
        self.send('<h1>%s</h1>' % change_request.get_issue_map().get_universe_name())

        ml_debug_results = {}
        try:
            for key, value in change_request.get_machine_learning_model().calc_score().items():
                ml_debug_results[key] = value
        except Exception as e:
            self.send(debug.exception_html(e))
            continue

        model = change_request.get_machine_learning_model()

        X_train, y_train, X_test, y_test = ([],[],[],[])
        for X, y in model.get_dataset_training():
            X_train += X
            y_train += y

        for X, y in model.get_dataset_test():
            X_test += X
            y_test += y

        X_train, y_train, X_test, y_test = ( np.array(X_train), np.array(y_train), np.array(X_test), np.array(y_test))

        feature_names = model.get_feature_names_list()

        for result in sorted([{'name': key, **value} for key, value in ml_debug_results.items()], key=lambda x: 0 if x['average_proportional_score'] != x['average_proportional_score'] else -(x['average_proportional_score'] + x['interestingness'] / 4))[:2]:
            self.send('<h2>%s</h2>' % result['name'])

            classes_ = result['classes']
            n_classes = len(classes_)

            class_padding =  ['#PADDING#1#'] if n_classes == 2 else [] # when there are two classes, there will only be one column in the one-hot encoding. That breaks things.

            y_test_binarized = label_binarize(y_test, classes=classes_ + class_padding)

            if n_classes == 2:
                y_test_binarized = y_test_binarized[:,0:2]

            DV = result['DV']

            X_train_ = DV.transform(X_train)
            X_test_ = DV.transform(X_test)
            y_train_ = y_train

            if not result['scaler'] is None:
                X_train_ = result['scaler'].transform(X_train_)
                X_test_ = result['scaler'].transform(X_test_)

            if not result['sampler'] is None:
                X_train_, y_train_ = result['sampler'].fit_resample(X_train_, y_train)
                y_train_binarized = label_binarize(y_train_, classes=classes_)
            else:
                y_train_binarized = label_binarize(y_train_, classes=classes_)

            if not result['selector'] is None:
                X_train_ = result['selector'].transform(X_train_)
                X_test_ = result['selector'].transform(X_test_)

            if not result['reducer'] is None:
                X_train_ = result['reducer'].transform(X_train_)
                X_test_ = result['reducer'].transform(X_test_)

            y_pred = result['classifier'].predict(X_test_)

            cm = result['cm']
            report = metrics.classification_report(y_test, y_pred)

            self.send('Classes: %s<br/>' % str(list(enumerate(classes_))))
            self.send('Interestingness: %s<br/>' % str(result['interestingness']))
            self.send('Proportional score: %s%%<br/>' % str(list(zip(classes_, result['proportional_score']))))
            self.send('Average proportional score: %s%%<br/>' % str(result['average_proportional_score']))

            classifier = result['classifier']

            score = classifier.score(X_test_, y_test) * 100.0
            accuracy = metrics.accuracy_score(y_test, y_pred) * 100

            dimensionality = None
            d = None

            roc_score_ovr = -1
            roc_score_ovo = -1

            figfilename = TEMP_DIR + change_request.get_issue_map().get_universe_name() + result['name'] + '_1.png'
            figfilename_roc = TEMP_DIR + change_request.get_issue_map().get_universe_name() + result['name'] + '_roc.png'
            figfilename_3 = TEMP_DIR + change_request.get_issue_map().get_universe_name() + result['name'] + '_prec_recall.png'
            figfilename_4 = TEMP_DIR + change_request.get_issue_map().get_universe_name() + result['name'] + '_multi.png'

            try:
                y_prob = classifier.predict_proba(X_test_)

                try:
                    roc_score_ovr = metrics.roc_auc_score(y_test_binarized, y_prob, average='weighted', multi_class='ovr')
                    roc_score_ovo = metrics.roc_auc_score(y_test_binarized, y_prob, average='weighted', multi_class='ovo')
                except Exception as e:
                    self.send(debug.exception_html(e))

                try:
                    ovr = OneVsRestClassifier(copy.deepcopy(classifier))
                    ovr.fit(X_train_, y_train_)

                    y_score = np.nan_to_num(ovr.predict_proba(X_test_))

                    precision = dict()
                    recall = dict()
                    plt.figure()
                    for i in range(n_classes):
                        precision[i], recall[i], _ = precision_recall_curve(y_test_binarized[:, i], y_score[:, i])
                        plt.plot(recall[i], precision[i], lw=2, label=classes_[i])

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
                        fpr[i], tpr[i], _ = roc_curve(y_test_binarized[:, i], y_score[:, i])
                        plt.plot(fpr[i], tpr[i], lw=2, label=classes_[i])

                    plt.xlabel("false positive rate")
                    plt.ylabel("true positive rate")
                    plt.legend(loc="best")
                    plt.title("ROC curve")
                    plt.savefig(figfilename_roc)

                except Exception as e:
                    self.send(debug.exception_html(e))

                try:
                    #
                    #try:
                    #    y_score = np.nan_to_num(ovr.decision_function(X_test_))
                    #except:
                    #    y_score = np.nan_to_num(ovr.predict_proba(X_test_))

                    precision = dict()
                    recall = dict()
                    average_precision = dict()

                    plt.figure()
                    for i in range(n_classes):
                        precision[i], recall[i], _ = precision_recall_curve(y_test_binarized[:, i], y_score[:, i])
                        average_precision[i] = average_precision_score(y_test_binarized[:, i], y_score[:, i])

                    # A "micro-average": quantifying score on all classes jointly
                    precision["micro"], recall["micro"], _ = precision_recall_curve(y_test_binarized.ravel(), y_score.ravel())
                    average_precision["micro"] = average_precision_score(y_test_binarized, y_score, average="micro")

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
                    labels.append('micro-average Precision-recall (area = {0:0.2f})'.format(average_precision["micro"]))

                    for i, color in zip(range(n_classes), colors):
                        l, = plt.plot(recall[i], precision[i], color=color, lw=2)
                        lines.append(l)
                        labels.append('Precision-recall for class {0} (area = {1:0.2f})'
                                    ''.format(classes_[i], average_precision[i]))

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
                    self.send(debug.exception_html(e))

            except Exception as e:
                    self.send(debug.exception_html(e))

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


except Exception as e:
    self.send(debug.exception_html(e))

self.send('</body></html>')

exports = {
}
