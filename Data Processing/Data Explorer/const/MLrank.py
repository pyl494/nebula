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

        ml_debug_results = {}
        try:
            for key, value in change_request.get_machine_learning_model().calc_score().items():
                ml_debug_results[key] = value
        except Exception as e:
            self.send(debug.exception_html(e))
            continue

        model = change_request.get_machine_learning_model()
        rank = 1
        for result in sorted([{'name': key, **value} for key, value in ml_debug_results.items()], key=lambda x: 0 if x['average_proportional_score'] != x['average_proportional_score'] else -(x['average_proportional_score'] + x['interestingness'] / 4)):
            self.send('<h2>%s - %s</h1>' % (str(rank), result['name']))
            rank += 1

            self.send('<pre>%s</pre>' % html.escape(str(result['cm'])))
            self.send('Classes: %s<br/>' % str(list(enumerate(result['classes']))))
            self.send('Interestingness: %s%%<br/>' % str(result['interestingness']))
            self.send('Proportional score: %s%%<br/>' % str(list(zip(result['classes'], result['proportional_score']))))
            self.send('Average proportional score: %s%%<br/>' % str(result['average_proportional_score']))


except Exception as e:
    self.send(debug.exception_html(e))

self.send('</body></html>')

exports = {
}
