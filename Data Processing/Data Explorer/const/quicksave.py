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
        <body>
            <h1>Saving State</h1>""")

state = [
    'classifiers',
    'feature_selections',
    'scalers',
    'samplers',
    'trained_models',
    'train_data_set',
    'test_data_set',
    'DV',
    'issue_maps',
    'change_request_list',
    'ml_debug_results'
]

from joblib import dump

try:
    prefix = ''
    if len(querystring.keys()) > 0:
        prefix = list(querystring.keys())[0] + '_'

    for s in state:
        self.send('%s..<br/>' % s)
        dump(eval(s), TEMP_DIR + '%s%s.joblib' % (prefix, s), compress=3)
except Exception as e:
    self.send(exception_html(e))

self.send('Finished!</body></html>')