
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

if 'issues' in sys.modules:
    del sys.modules['issues']

if 'change_requests' in sys.modules:
    del sys.modules['change_requests']

import issues
import change_requests

self.send('<h2>Updating Change Request List</h2>')
new_issue_maps = []
new_change_request_list = []
for oc in change_request_list:
    
    issue_map = issues.Issues(oc.issue_map.universe_name, oc.issue_map.data_location, oc.issue_map.data_prefix, oc.issue_map.data_bulk_size)
    new_issue_maps += [issue_map]

    c = change_requests.ChangeRequest(issue_map)
    new_change_request_list += [c]

    self.send('<h3>%s</h3>' % oc.getIssueMap().getUniverseName())

    c.features_values_map = oc.features_values_map
    c.projects_fixVersions_issue_map = oc.projects_fixVersions_issue_map
    c.projects_affectsVersions_issue_map = oc.projects_affectsVersions_issue_map
    c.change_request_meta_map = oc.change_request_meta_map
    c.projects_version_info_map = oc.projects_version_info_map

self.send('<h1>Complete!</h1>')
self.send('</body></html>')

exports = {
    'issue_maps': new_issue_maps,
    'change_request_list': new_change_request_list
}
