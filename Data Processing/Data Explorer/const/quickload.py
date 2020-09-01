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
    'ml_debug_results'
]

from joblib import load

import sys

modules = ['change_requests', 'issues', 'machine_learning', 'debug']

for module in modules:
    if module in sys.modules:
        del sys.modules[module]

import issues
import change_requests
import debug

try:
    prefix = ''
    if len(querystring.keys()) > 0:
        prefix = list(querystring.keys())[0] + '_'

    exports = {}

    for s in state:
        self.send('%s..<br/>' % s)

        try:
            exports[s] = load(TEMP_DIR + '%s%s.joblib' % (prefix, s))
            self.send("loaded<br/>")
        except:
            self.send("didn't load<br/>")
except Exception as e:
    self.send(debug.exception_html(e))

try:
    self.send('<h2>Unpacking Change Request List Internal</h2>')
    issue_maps = []
    change_request_list = []
    change_request_list_state = load(TEMP_DIR + '%s%s.joblib' % (prefix, 'change_request_list_state'))
    for state in change_request_list_state:
        issue_map = issues.Issues(state['issue_map_universe_name'], state['issue_map_data_location'], state['issue_map_data_prefix'], state['issue_map_data_bulk_size'])
        issue_maps += [issue_map]
        c = change_requests.ChangeRequest(issue_map)

        self.send('<h3>%s</h3>' % c.get_issue_map().get_universe_name())

        c.features_values_map = state['features_values_map']
        c.projects_fixVersions_issue_map = state['projects_fixVersions_issue_map']
        c.projects_affectsVersions_issue_map = state['projects_affectsVersions_issue_map']
        c.change_request_meta_map = state['change_request_meta_map']
        c.projects_version_info_map = state['projects_version_info_map']

        change_request_list += [c]

    exports['issue_maps'] = issue_maps
    exports['change_request_list'] = change_request_list

except Exception as e:
    self.send(debug.exception_html(e))

self.send('Finished!</body></html>')
