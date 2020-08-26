
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
            <h1>Updating</h1>""")

import json
import sys

modules = ['change_requests', 'issues', 'machine_learning', 'debug']

for module in modules:
    if module in sys.modules:
        del sys.modules[module]

import issues
import change_requests
import debug

def load():
    global json, issues, change_requests
    with open('../jsondumps.json', 'r') as f:
        DUMPS = json.loads(f.read())

    issue_maps = [issues.Issues('Microservice Demo')]

    for dump in DUMPS:
        if dump['load']:
            issue_maps += [issues.Issues(dump['universe'], dump['location'], dump['prefix'], dump['bulkSize'])]

    change_request_list = [change_requests.ChangeRequest(x) for x in issue_maps]

    return issue_maps, change_request_list

self.send('<h2>Initiating Fresh Change Request List</h2>')
issue_maps, change_request_list = load()

exports = {
    'issue_maps': issue_maps,
    'change_request_list': change_request_list
}
