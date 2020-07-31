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

    X_test, y_test = test_data_set
    lowi = 1
    medi = 2
    highi = 0

    try:
        if ml_debug_results == None:
            raise 'reloading'
    except:
        ml_debug_results = []
    
        for scaling_name, scalings_ in trained_models.items():
            if not isinstance(scalings_, dict):
                continue
                
            X_test_scaled = X_test
            scaler = None
            if 'scaler' in scalings_:
                scaler = scalings_['scaler']
                X_test_scaled = scaler.transform(X_test)
            
            for sampling_name, samplings_ in scalings_.items():
                if not isinstance(samplings_, dict):
                    continue
                
                X_test_sampled = X_test_scaled
                sampler = None
                if 'sampler' in samplings_:
                    sampler = samplings_['sampler']
                
                for fselection_name, fselections_ in samplings_.items():
                    if not isinstance(fselections_, dict):
                        continue
                        
                    X_test_fselected = X_test_sampled
                    selector = None
                    if 'selector' in fselections_:
                        selector = fselections_['selector']
                        X_test_fselected = selector.transform(X_test_sampled)
                    
                    self.send('<br/>')

                    for classifier_name, classifier in fselections_.items():
                        if classifier_name == 'selector':
                            continue

                        self.send('.')

                        try:
                            name = '%s - %s - %s - %s' % (scaling_name, sampling_name, fselection_name, classifier_name)

                            y_pred = classifier.predict(X_test_fselected)

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

                            ml_debug_results += [{
                                'int': interestingness,
                                'low%p': low_percent_precision,
                                'med%p': med_percent_precision,
                                'high%p': high_percent_precision,
                                'avg%p': average_percent_precision,
                                'cm': cm,
                                'classifier': classifier,
                                'name': name,
                                'selector': selector,
                                'scaler': scaler,
                                'sampler': sampler
                            }]
                            
                        except Exception as e:
                            self.send(exception_html(e))

    from collections import defaultdict

    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.stats import spearmanr
    from scipy.cluster import hierarchy

    from sklearn.datasets import load_breast_cancer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.inspection import permutation_importance
    from sklearn.model_selection import train_test_split

    import copy

    X_train, y_train = train_data_set
    X_test, y_test = test_data_set
    feature_names = np.array(list(DV.vocabulary_.keys()))

    for result in sorted(ml_debug_results, key=lambda x: 0 if x['avg%p'] != x['avg%p'] else -(x['avg%p'] + x['int']))[:10]:
        self.send('<h1>%s</h1>' % result['name'])

        X_train_, X_test_ = X_train, X_test
        y_train_ = y_train
        if not result['scaler'] is None:
            X_train_ = result['scaler'].transform(X_train_)
            X_test_ = result['scaler'].transform(X_test_)

        if not result['sampler'] is None:
            X_train_, y_train_ = result['sampler'].fit_resample(X_train_, y_train_)
        
        selected_feature_name_list = feature_names
        if not result['selector'] is None:
            X_train_ = result['selector'].transform(X_train_)
            X_test_ = result['selector'].transform(X_test_)

            selected_feature_name_list = []
            for x, y in zip(feature_names, result['selector'].get_support()):
                if y == 1:
                    selected_feature_name_list += [x]
            selected_feature_name_list = np.array(selected_feature_name_list)

        try:
            pimp = permutation_importance(result['classifier'], X_train_, y_train_, n_repeats=10,
                                            random_state=42)
            perm_sorted_idx = pimp.importances_mean.argsort()

            tree_importance_sorted_idx = np.argsort(result['classifier'].feature_importances_)
            tree_indices = np.arange(0, len(result['classifier'].feature_importances_)) + 0.5

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, len(selected_feature_name_list) / 4.0))
            ax1.barh(tree_indices,
                    result['classifier'].feature_importances_[tree_importance_sorted_idx], height=0.7)
            ax1.set_yticklabels(selected_feature_name_list[tree_importance_sorted_idx])
            ax1.set_yticks(tree_indices)
            ax1.set_ylim((0, len(result['classifier'].feature_importances_)))
            ax2.boxplot(pimp.importances[perm_sorted_idx].T, vert=False,
                        labels=selected_feature_name_list[perm_sorted_idx])
            fig.tight_layout()

            fname_pimp = TEMP_DIR + result['name'] + 'featimp.png'
            fig.savefig(fname_pimp)

            self.send('<img src="static?filename=Data Processing/%s&contenttype=image/png"><br/>' % fname_pimp)
        except:
            pass

        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(len(selected_feature_name_list) / 4.0, 8))
            corr = np.nan_to_num(spearmanr(X_train_).correlation)
            corr_linkage = hierarchy.ward(corr)
            dendro = hierarchy.dendrogram(corr_linkage, ax=ax1,
                                        #labels=selected_feature_name_list,
                                        leaf_rotation=90)
            dendro_idx = np.arange(0, len(dendro['ivl']))

            ax2.imshow(corr[dendro['leaves'], :][:, dendro['leaves']])
            ax2.set_xticks(dendro_idx)
            ax2.set_yticks(dendro_idx)
            ax2.set_xticklabels(dendro['ivl'], rotation='vertical')
            ax2.set_yticklabels(dendro['ivl'])
            fig.tight_layout()

            fname_dendo = TEMP_DIR + result['name'] + 'dendo.png'
            fig.savefig(fname_dendo)

            self.send('<img src="static?filename=Data Processing/%s&contenttype=image/png"><br/>' % fname_dendo)
        except Exception as e:
            self.send(exception_html(e))

        try:
            cluster_ids = hierarchy.fcluster(corr_linkage, 3, criterion='distance')
            cluster_id_to_feature_ids = defaultdict(list)
            for idx, cluster_id in enumerate(cluster_ids):
                cluster_id_to_feature_ids[cluster_id].append(idx)
            selected_features = [v[0] for v in cluster_id_to_feature_ids.values()]
            self.send('Selected Features:<br/>%s<br/>' % str(selected_features))

            X_train_sel = X_train_[:, selected_features]
            X_test_sel = X_test_[:, selected_features]

            self.send("Accuracy on test data: {:.2f}<br/>".format(
                result['classifier'].score(X_test_, y_test)))

            clf = copy.deepcopy(result['classifier'])
            clf.fit(X_train_sel, y_train_)
            self.send("Accuracy on test data with features removed: {:.2f}<br/>".format(
                clf.score(X_test_sel, y_test)))

            y_pred = clf.predict(X_test_sel)
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
            
            self.send('<table><tr><th>Before Feature Clustering</th><th>After Feature Clustering</th></tr>')
            self.send('<tr><td>')
            self.send('<pre>%s</pre><br/>' % result['cm'])
            self.send('Interestingness: {p:.2f}%<br/>'.format(p=result['int']))
            self.send('Low percent precision: {p:.2f}%<br/>'.format(p=result['low%p']))
            self.send('Medium percent precision: {p:.2f}%<br/>'.format(p=result['med%p']))
            self.send('High percent precision: {p:.2f}%<br/>'.format(p=result['high%p']))
            self.send('Average percent precision: {p:.2f}%<br/>'.format(p=result['avg%p']))
            self.send('</td><td>')
            self.send('<pre>%s</pre><br/>' % str(cm))
            self.send('Interestingness: {p:.2f}%<br/>'.format(p=interestingness))
            self.send('Low percent precision: {p:.2f}%<br/>'.format(p=low_percent_precision))
            self.send('Medium percent precision: {p:.2f}%<br/>'.format(p=med_percent_precision))
            self.send('High percent precision: {p:.2f}%<br/>'.format(p=high_percent_precision))
            self.send('Average percent precision: {p:.2f}%<br/>'.format(p=average_percent_precision))
            self.send('</td></tr></table>')

        except Exception as e:
            self.send(exception_html(e))


except Exception as e:
    self.send(exception_html(e))

self.send('</body></html>')

exports = {
    'ml_debug_results': ml_debug_results
}
