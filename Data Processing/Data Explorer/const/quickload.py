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
            <h1>Loading State</h1>""")

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
    'change_request_list'
]

from joblib import load

try:
    prefix = ''
    if len(querystring.keys()) > 0:
        prefix = list(querystring.keys())[0] + '_'

    exports = {}

    for s in state:
        self.send('%s..<br/>' % s)
        globals()[s] = load(TEMP_DIR + '%s%s.joblib' % (prefix, s))

        exports[s] = eval(s)
except Exception as e:
    self.send(exception_html(e))

self.send('Finished!</body></html>')
