self.send_response(200)
self.send_header("Content-type", "text/html")
self.end_headers()

self.wfile.write(bytes(
    """
    <html>
        <head>
            <title>Explorer</title>
        </head>
        <body>
            <h1>Generating</h1><h2>Loading issues</h2>""", "utf-8"))

def load():
    import json
    import importlib.util
    jsonquery_spec = importlib.util.spec_from_file_location('jsonquery', '../Data Processing/jsonquery.py')
    jsonquery = importlib.util.module_from_spec(jsonquery_spec)
    jsonquery_spec.loader.exec_module(jsonquery)

    generate_change_requests_spec = importlib.util.spec_from_file_location('generate_change_requests', '../Data Processing/generate_change_requests.py')
    generate_change_requests = importlib.util.module_from_spec(generate_change_requests_spec)
    generate_change_requests_spec.loader.exec_module(generate_change_requests)

    issues_spec = importlib.util.spec_from_file_location('issues', '../Data Processing/issues.py')
    issues = importlib.util.module_from_spec(issues_spec)
    issues_spec.loader.exec_module(issues)

    with open('../jsondumps.json', 'r') as f:
        DUMPS = json.loads(f.read())

    issueMaps = []

    for dump in DUMPS:
        if dump['load']:
            issueMaps += [issues.Issues(dump['universe'], dump['location'], dump['prefix'], dump['bulkSize'])]

    changeRequests = [generate_change_requests.GenerateChangeRequests(x) for x in issueMaps]

    return issueMaps, changeRequests

issueMaps, changeRequests = load()

for issueMap in issueMaps:
    for status in issueMap.load():
        self.wfile.write(bytes('%s<br/>' % html.escape(status), "utf-8"))

self.wfile.write(bytes('<h2>Generating Change Requests</h2>', "utf-8"))

for changeRequest in changeRequests:
    issueMap = changeRequest.getIssueMap()
    changeRequest.generate()
    self.wfile.write(bytes('%s<br/>' % html.escape(issueMap.getDataLocation() + issueMap.getDataPrefix()), "utf-8"))

self.wfile.write(bytes('Complete !<br/><a href="/results">Go to results</a></body></html>', "utf-8"))
