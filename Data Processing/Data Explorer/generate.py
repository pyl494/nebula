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

    issue_maps = []

    for dump in DUMPS:
        if dump['load']:
            issue_maps += [issues.Issues(dump['universe'], dump['location'], dump['prefix'], dump['bulkSize'])]

    change_request_list = [change_request.ChangeRequest(x) for x in issue_maps]

    return issue_maps, change_request_list

issue_maps, change_request_list = load()

for issue_map in issue_maps:
    for status in issue_map.load():
        self.send('%s<br/>' % html.escape(status))

self.send('<h2>Generating Change Requests</h2>')

for change_request in change_request_list:
    issue_map = change_request.getIssueMap()
    change_request.generate()
    self.send('%s<br/>' % html.escape(issue_map.getDataLocation() + issue_map.getDataPrefix()))

self.send('Complete !<br/><a href="/results">Go to results</a></body></html>')
