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

for issueMap in issueMaps:
    for status in issueMap.load():
        self.wfile.write(bytes('%s<br/>' % html.escape(status), "utf-8"))

self.wfile.write(bytes('<h2>Generating Change Requests</h2>', "utf-8"))

for changeRequest in changeRequests:
    issueMap = changeRequest.getIssueMap()
    changeRequest.generate()
    self.wfile.write(bytes('%s<br/>' % html.escape(issueMap.getDataLocation() + issueMap.getDataPrefix()), "utf-8"))


self.wfile.write(bytes('Complete !<br/><a href="/results">Go to results</a></body></html>', "utf-8"))
