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
            <h1>Generating</h1><h2>Loading issues</h2>""")

def load():
    import json
    import importlib.util
    jsonquery_spec = importlib.util.spec_from_file_location('jsonquery', '../Data Processing/jsonquery.py')
    jsonquery = importlib.util.module_from_spec(jsonquery_spec)
    jsonquery_spec.loader.exec_module(jsonquery)

    change_requests_spec = importlib.util.spec_from_file_location('change_requests', '../Data Processing/change_requests.py')
    change_request = importlib.util.module_from_spec(change_requests_spec)
    change_requests_spec.loader.exec_module(change_request)

    issues_spec = importlib.util.spec_from_file_location('issues', '../Data Processing/issues.py')
    issues = importlib.util.module_from_spec(issues_spec)
    issues_spec.loader.exec_module(issues)

    with open('../jsondumps.json', 'r') as f:
        DUMPS = json.loads(f.read())

    issue_maps = [issues.Issues('Microservice Demo')]

    for dump in DUMPS:
        if dump['load']:
            issue_maps += [issues.Issues(dump['universe'], dump['location'], dump['prefix'], dump['bulkSize'])]

    change_request_list = [change_request.ChangeRequest(x) for x in issue_maps]

    return issue_maps, change_request_list

issue_maps, change_request_list = load()

self.send('<h2>Generating Change Requests</h2>')

for change_request in change_request_list:
    issue_map = change_request.get_issue_map()
    self.send('<h2>%s</h2>' % issue_map.get_universe_name())
    change_request.generate()
    self.send('%s<br/>' % html.escape(str(issue_map.get_data_location()) + str(issue_map.get_data_prefix())))

self.send('Complete !<br/><a href="/results">Go to results</a></body></html>')

exports = {
    'issue_maps': issue_maps,
    'change_request_list': change_request_list
}
