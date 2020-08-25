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
    'ml_debug_results',
    'change_request_list_state'
]

from joblib import dump

self.send('<h2>Packing Change Request List Internal</h2>')
change_request_list_state = []
for oc in change_request_list:
    c = {}

    self.send('<h3>%s</h3>' % oc.getIssueMap().getUniverseName())

    c['issue_map_universe_name'] = oc.issue_map.universe_name
    c['issue_map_data_location'] = oc.issue_map.data_location
    c['issue_map_data_prefix'] = oc.issue_map.data_prefix
    c['issue_map_data_bulk_size'] = oc.issue_map.data_bulk_size

    c['features_values_map'] = oc.features_values_map
    c['projects_fixVersions_issue_map'] = oc.projects_fixVersions_issue_map
    c['projects_affectsVersions_issue_map'] = oc.projects_affectsVersions_issue_map
    c['change_request_meta_map'] = oc.change_request_meta_map
    c['projects_version_info_map'] = oc.projects_version_info_map

    change_request_list_state += [c]

try:
    prefix = ''
    if len(querystring.keys()) > 0:
        prefix = list(querystring.keys())[0] + '_'

    for s in state:
        self.send('%s..<br/>' % s)
        try:
            dump(eval(s), TEMP_DIR + '%s%s.joblib' % (prefix, s), compress=3)
            self.send("saved<br/>")
        except Exception as e:
            self.send("didn't save<br/>")
            self.send(exception_html(e))

except Exception as e:
    self.send(exception_html(e))

self.send('Finished!</body></html>')