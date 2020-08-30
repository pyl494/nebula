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

    for change_request in change_request_list:
        self.send('<h1>%s</h2>' % change_request.getIssueMap().getUniverseName())

        ml_debug_results = {}
        try:
            for key, value in change_request.getMachineLearningModel().calc_score().items():
                ml_debug_results[key] = value
        except Exception as e:
            self.send(exception_html(e))
            continue

        model = change_request.getMachineLearningModel()
        rank = 1
        for result in sorted([{'name': key, **value} for key, value in ml_debug_results.items()], key=lambda x: 0 if x['avg%p'] != x['avg%p'] else -(x['avg%p'] + x['int'])):
            self.send('<h2>%s - %s</h1>' % (str(rank), result['name']))
            rank += 1

            self.send('<pre>%s</pre>' % html.escape(str(result['cm'])))
            self.send('Interestingness: {p:.2f}%<br/>'.format(p=result['int']))
            self.send('Low percent precision: {p:.2f}%<br/>'.format(p=result['low%p']))
            self.send('Medium percent precision: {p:.2f}%<br/>'.format(p=result['med%p']))
            self.send('High percent precision: {p:.2f}%<br/>'.format(p=result['high%p']))
            self.send('Average percent precision: {p:.2f}%<br/>'.format(p=result['avg%p']))


except Exception as e:
    self.send(exception_html(e))

self.send('</body></html>')

exports = {
}
