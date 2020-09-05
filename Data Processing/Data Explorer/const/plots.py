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
        self.send('<h1>%s</h2>' % change_request.get_issue_map().get_universe_name())

        d = []
        for change_request_meta in change_request.iterate_change_request_meta_map():
            project_key = change_request_meta['project_key']
            version_name = change_request_meta['fixVersion_name']
            change_request_issue_key = change_request_meta['issue_key']
            i = change_request.get_post_change_request_interactivity(change_request_issue_key)
            d += [(
                i['interactivity'],
                i['fixVersion_vote_count'],
                i['fixVersion_post_comment_count'],
                i['affectsVersion_issue_count'],
                i['affectsVersion_vote_count'],
                i['affectsVersion_comment_count']
            )]

        d = np.array(d)
        fig = plt.figure(figsize=[20, 10])
        r = plt.hist(d, bins=50, range=(0, 200), align='left', label=['interactivity', 'fixVersion_vote_count', 'fixVersion_post_comment_count', 'affectsVersion_issue_count', 'affectsVersion_vote_count', 'affectsVersion_comment_count'])
        plt.legend(loc='best')
        plt.yscale('log')

        fname_hist = TEMP_DIR + change_request.get_issue_map().get_universe_name() + '_interactivity_histogram.png'
        fig.savefig(fname_hist)
        self.send('<img src="static?filename=Data Processing/%s&contenttype=image/png"><br/>' % fname_hist)

        self.send('<h2>results - n</h2><pre>%s</pre><br/>' % str(r[0]))
        self.send('<h2>results - bins</h2><pre>%s</pre><br/>' % str(r[1]))
        self.send('<h2>results - patches</h2><pre>%s</pre><br/>' % str(r[2]))


except Exception as e:
    self.send(debug.exception_html(e))

self.send('</body></html>')

exports = {
}
