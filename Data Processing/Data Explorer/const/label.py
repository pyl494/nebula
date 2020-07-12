self.send_response(200)
self.send_header("Content-type", "text/html")
self.end_headers()

out = ""

try:
    projects_fixVersions_issue_map = None
    projects_affectsVersions_issue_map = None
    issue_map = None
    projects_version_info_map = None

    for change_request in change_request_list:
        if change_request.getIssueMap().getUniverseName() == querystring['universe']:
            if querystring['type'] == 'change request':
                # querystring['project']
                # querystring['version']
                change_request.setManualRiskLabel(querystring['change_request'], querystring['label'])
                out = change_request.getManualRiskLabel(querystring['change_request'])

            break

except Exception as e:
    out += exception_html(e)
    
self.send(out)
