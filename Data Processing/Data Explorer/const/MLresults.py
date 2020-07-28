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

    results = []

    for scaling_name, scalings_ in trained_models.items():
        if not isinstance(scalings_, dict):
            continue
            
        X_test_scaled = X_test
        if 'scaler' in scalings_:
            X_test_scaled = scalings_['scaler'].transform(X_test)
        
        for sampling_name, samplings_ in scalings_.items():
            if not isinstance(samplings_, dict):
                continue
            
            X_test_sampled = X_test_scaled
            
            for fselection_name, fselections_ in samplings_.items():
                if not isinstance(fselections_, dict):
                    continue
                    
                X_test_fselected = X_test_sampled
                if 'selector' in fselections_:
                    X_test_fselected = fselections_['selector'].transform(X_test_sampled)
                
                self.send('<br/>')

                for classifier_name, classifier in fselections_.items():
                    if classifier_name == 'selector':
                        continue

                    self.send('.')

                    try:
                        y_pred = classifier.predict(X_test_fselected)

                        cm = metrics.confusion_matrix(y_test, y_pred)
                        report = metrics.classification_report(y_test, y_pred, target_names=['low', 'medium', 'high'])

                        interestingness = (
                            1 * (cm[0][0] * 10 + cm[0][1] * 1 + cm[0][2] * 0) / (11 * (cm[0][0] + cm[0][1] + cm[0][2])) +
                            2 * (cm[1][0] * 0.5 + cm[1][1] * 10 + cm[1][2] * 0.5) / (11 * (cm[1][0] + cm[1][1] + cm[1][2])) +
                            3 * (cm[2][0] * 0 + cm[2][1] * 1 + cm[2][2] * 10) / (11 * (cm[2][0] + cm[2][1] + cm[2][2]))
                        ) / (3 + 2 + 1) * 100

                        low_percent_precision = (
                            pow(cm[0][0] / (cm[0][0] + cm[0][1] + cm[0][2]), 2) /
                                (cm[0][0] / (cm[0][0] + cm[0][1] + cm[0][2]) +
                                cm[1][0] / (cm[1][0] + cm[1][1] + cm[1][2]) +
                                cm[2][0] / (cm[2][0] + cm[2][1] + cm[2][2])) * 100
                        )
                        
                        med_percent_precision = ( 
                                pow(cm[1][1] / (cm[1][0] + cm[1][1] + cm[1][2]), 2) /
                                (cm[0][1] / (cm[0][0] + cm[0][1] + cm[0][2]) +
                                cm[1][1] / (cm[1][0] + cm[1][1] + cm[1][2]) +
                                cm[2][1] / (cm[2][0] + cm[2][1] + cm[2][2])) * 100
                        )
                        
                        high_percent_precision = (
                                pow(cm[2][2] / (cm[2][0] + cm[2][1] + cm[2][2]), 2) /
                                (cm[0][2] / (cm[0][0] + cm[0][1] + cm[0][2]) +
                                cm[1][2] / (cm[1][0] + cm[1][1] + cm[1][2]) +
                                cm[2][2] / (cm[2][0] + cm[2][1] + cm[2][2])) * 100
                        )

                        results += [(
                            interestingness,
                            low_percent_precision,
                            med_percent_precision,
                            high_percent_precision,
                            '<h1>%s - %s - %s - %s</h1>' % (scaling_name, sampling_name, fselection_name, classifier_name),
                            '<pre>%s</pre><br/>' % cm,
                            'interestingness: {interestingness:.2f} %%<br/>'.format(interestingness = interestingness),
                            '<pre>%s</pre><br/>' % report,
                            'low percent precision: %s %%<br/>' % low_percent_precision,
                            'med percent precision: %s %%<br/>' % med_percent_precision,
                            'high percent precision: %s %%<br/>' % high_percent_precision
                        )]

                    except Exception as e:
                        self.send(exception_html(e))
    
    for result in sorted(results, key=lambda x:x[0]):

        self.send(result[4])
        self.send(result[5])
        self.send(result[6])
        self.send(result[7])
        self.send(result[8])
        self.send(result[9])
        self.send(result[10])
        self.send('Average percent precision: {p:.2f}%<br/>'.format(p=(result[1] + result[2] + result[3]) / 3))

except Exception as e:
    self.send(exception_html(e))

self.send('</body></html>')

exports = {
}
