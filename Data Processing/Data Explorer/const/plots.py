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

    histograms = {}
    histoinput = {}

    for change_request in change_request_list:
        universe_name = change_request.get_issue_map().get_universe_name()
        self.send('<h1>%s</h2>' % universe_name)

        try:
            r = change_request.calc_label_thresholds()
            d = r['data']
            histoinput[universe_name] = d

            fig = plt.figure(figsize=[20, 10])
            histograms[universe_name] = plt.hist(d, bins=50, range=(0, 200), align='left', label=r['vocabulary_index'])
            plt.legend(loc='best')
            plt.yscale('log')

            fname_hist = TEMP_DIR + universe_name + '_interactivity_histogram.png'
            fig.savefig(fname_hist)
            self.send('<img src="static?filename=Data Processing/%s&contenttype=image/png"><br/>' % fname_hist)

            self.send('<h2>results - n</h2><pre>%s</pre><br/>' % str(histograms[universe_name][0]))
            self.send('<h2>results - bins</h2><pre>%s</pre><br/>' % str(histograms[universe_name][1]))
            self.send('<h2>results - patches</h2><pre>%s</pre><br/>' % str(histograms[universe_name][2]))

            self.send('<h2>r</h2><pre>%s</pre><br/>' % str(r))
        except Exception as e:
            self.send(debug.exception_html(e))


except Exception as e:
    self.send(debug.exception_html(e))

self.send('</body></html>')

exports = {
    'histograms': histograms,
    'histoinput': histoinput
}
