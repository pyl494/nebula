import debug

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
        if change_request.get_issue_map().get_universe_name() == querystring['universe']:
            if querystring['type'] == 'change request':
                # querystring['project']
                # querystring['version']
                change_request.set_manual_risk_label(querystring['change_request'], querystring['label'])
                out = change_request.get_manual_risk_label(querystring['change_request'])

            break

except Exception as e:
    out += debug.exception_html(e)

self.send(out)
