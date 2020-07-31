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

    X_train, y_train = train_data_set
    X_test, y_test = test_data_set
    feature_names = np.array(list(DV.vocabulary_.keys()))

    for result in sorted(ml_debug_results, key=lambda x: 0 if x['avg%p'] != x['avg%p'] else -(x['avg%p'] + x['int']))[:10]:
        y_pred = classifier.predict(X_test_fselected)

        cm = metrics.confusion_matrix(y_test, y_pred)
        report = metrics.classification_report(y_test, y_pred)

        figfilename = TEMP_DIR + name + '_1.png'
        figfilename_roc = TEMP_DIR + name + '_roc.png'
        figfilename_3 = TEMP_DIR + name + '_prec_recall.png'
        figfilename_4 = TEMP_DIR + name + '_multi.png'

        self.send('<h1>%s</h1>' % name)
        self.send('<pre>%s</pre><br/>' % cm)
        self.send('<pre>%s</pre><br/>' % report)
        self.send('''
        <img src="static?filename=Data Processing/%s&contenttype=image/png"><br/>
        <img src="static?filename=Data Processing/%s&contenttype=image/png"><br/>
        <img src="static?filename=Data Processing/%s&contenttype=image/png"><br/>
        <img src="static?filename=Data Processing/%s&contenttype=image/png"><br/>
        ''' % (figfilename, figfilename_roc, figfilename_3, figfilename_4))
        
        self.send('Interestingness: {p:.2f}%<br/>'.format(p=result[0]))
        self.send('Low percent precision: {p:.2f}%<br/>'.format(p=result[1]))
        self.send('Medium percent precision: {p:.2f}%<br/>'.format(p=result[2]))
        self.send('High percent precision: {p:.2f}%<br/>'.format(p=result[3]))
        self.send('Average percent precision: {p:.2f}%<br/>'.format(p=result[4]))




except Exception as e:
    self.send(exception_html(e))

self.send('</body></html>')

exports = {
}
