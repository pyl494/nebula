self.send_response(200)
self.send_header("Content-type", "text/html")
self.end_headers()

out = ""

try:
    projectsFixVersions = None
    projectsAffectsVersions = None
    issueMap = None
    versionMap = None

    for changeRequest in changeRequests:
        if changeRequest.getIssueMap().getUniverseName() == querystring['universe']:
            if querystring['type'] == 'change request':
                # querystring['project']
                # querystring['version']
                changeRequest.setManualRiskLabel(querystring['project'], querystring['version'], querystring['label'])
                out = changeRequest.getManualRiskLabel(querystring['project'], querystring['version'])

            break

except Exception as e:
    out += exception_html(e)
    
self.wfile.write(bytes(
    out, "utf-8"))
