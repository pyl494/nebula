# Purpose
# This lets us explore data through a web interface.
# Features:
# - integrates generate_change_requests.py

# Instructions
# This script requires the json data dumps

# Status
# Work in progress

# Source
# Harun Delic

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import traceback, sys
from generate_change_requests import GenerateChangeRequests

hostname = "localhost"
port = 8080

changeRequest = GenerateChangeRequests()

def exception_html(e):
    ex_type, ex_value, ex_traceback = sys.exc_info()
    trace_back = traceback.extract_tb(ex_traceback)
    stack_trace = list()
    for trace in trace_back:
        stack_trace.append("<b>@%s</b><br/>    line %d in  %s <br/>    %s" % (trace[0], trace[1], trace[2], trace[3]))
    
    return "<div>%s, %s<br/><pre>%s</pre></div>" % (ex_type, ex_value, json.dumps(stack_trace, indent=2))

class WebServer(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.middleware = [self.css, self.index, self.results, self.view, self.generate]

        super().__init__(*args, **kwargs)

    def css(self, route, querystring):
        if len(route) == 1 and route[0] == 'css':
            self.send_response(200)
            self.send_header("Content-type", "text/css")
            self.end_headers()

            with open('data_explorer.css', 'r', encoding='utf-8') as f:
                self.wfile.write(bytes(f.read(), encoding='utf-8'))

            return True

        return False

    def index(self, route, querystring):
        if len(route) == 0:
            self.send_response(301)
            self.send_header("Location", "/generate")
            self.end_headers()

            return True

        return False

    def results(self, route, querystring):
        if len(route) == 1:
            if route[0] == 'results':
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                
                versionMap = changeRequest.getVersionMap()
                projectsFixVersions = changeRequest.getProjectsFixVersions()
                projectsAffectsVersions = changeRequest.getProjectsAffectsVersions()
                
                out = ""
                for key, versions in versionMap.items():
                    out += "<h2>%s</h2>" % key
                    out += "<table><tr><th>Date</th><th>Project</th><th>Version</th><th># issues w/ FixVersion</th><th># issues w/ Affected Version</th></tr>"

                    for versionName, version in sorted(versions.items(), key=lambda v: v[1]['releaseDate'] if 'releaseDate' in v[1] else (' ' * 20) + 'unreleased' + v[0]):
                        fcount = 0
                        acount = 0

                        if key in projectsFixVersions:
                            fversions = projectsFixVersions[key]

                            if versionName in fversions:
                                fcount = len(fversions[versionName])

                        if key in projectsAffectsVersions:
                            aversions = projectsAffectsVersions[key]

                            if versionName in aversions:
                                acount = len(aversions[versionName])

                        releaseDate = "Unreleased"
                        if 'releaseDate' in version:
                            releaseDate = version['releaseDate']

                        out += """
                            <tr>
                                <td>{date}</td>
                                <td>{key}</td>
                                <td>{version}</td>
                                <td>
                                    <a href="/view?project={key}&version={version}&view=fixes">{fcount}</a>
                                </td>
                                <td>
                                    <a href="/view?project={key}&version={version}&view=affected">{acount}</a>
                                </td>
                            </tr>""".format(
                            date=releaseDate,
                            version=versionName,
                            key=key,
                            acount=acount,
                            fcount=fcount
                        )
                    out += "</table>"
                
                self.wfile.write(bytes(
                    """
                    <html>
                        <head>
                            <title>Explorer</title>
                            <link rel="stylesheet" href="/css" media="all">
                        </head>
                        <body>
                            <h1>Results</h1>
                            %s
                            
                        </body>
                    </html>"""  % out, "utf-8"))
                return True

        return False

    def view(self, route, querystring):
        if len(route) == 1:
            if route[0] == 'view':
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                
                out = ""

                try:
                    projectsFixVersions = changeRequest.getProjectsFixVersions()
                    projectsAffectsVersions = changeRequest.getProjectsAffectsVersions()

                    if querystring['view'] == 'fixes':

                        if querystring['project'] in projectsFixVersions:
                            versions = projectsFixVersions[querystring['project']]

                            if querystring['version'] in versions:
                                version = versions[querystring['version']]

                                out += '<table><tr><th>Created Date</th><th>Updated Date</th><th>Issue Key</th><th width="50%">Summary</th><th>Data</th><th>External Link</th></tr>'

                                for issuekey, issue in version.items():
                                    out += """
                                        <tr>
                                            <td>{cdate}</td>
                                            <td>{udate}</td>
                                            <td>{issuekey}</td>
                                            <td>{summary}</td>
                                            <td>
                                                <a href="/view?project={key}&version={version}&issuekey={issuekey}&view=fixesissue">View Issue</a>
                                            </td>
                                            <td>
                                                <a href="{external}">External Link</a>
                                            </td>
                                        </tr>
                                    """.format(
                                        cdate=issue['fields']['created'],
                                        udate=issue['fields']['updated'],
                                        key=querystring['project'],
                                        version=querystring['version'],
                                        issuekey=issuekey,
                                        summary=issue['fields']['summary'],
                                        external=issue['self']
                                    )

                                out += '</table>'

                    elif querystring['view'] == 'affected':

                        if querystring['project'] in projectsAffectsVersions:
                            versions = projectsAffectsVersions[querystring['project']]

                            if querystring['version'] in versions:
                                version = versions[querystring['version']]

                                out += '<table><tr><th>Created Date</th><th>Updated Date</th><th>Issue Key</th><th width="50%">Summary</th><th>Data</th><th>External Link</th></tr>'

                                for issuekey, issue in version.items():
                                    out += """
                                        <tr>
                                            <td>{cdate}</td>
                                            <td>{udate}</td>
                                            <td>{issuekey}</td>
                                            <td>{summary}</td>
                                            <td>
                                                <a href="/view?project={key}&version={version}&issuekey={issuekey}&view=fixesissue">View Issue</a>
                                            </td>
                                            <td>
                                                <a href="{external}">External Link</a>
                                            </td>
                                        </tr>
                                    """.format(
                                        cdate=issue['fields']['created'],
                                        udate=issue['fields']['updated'],
                                        key=querystring['project'],
                                        version=querystring['version'],
                                        issuekey=issuekey,
                                        summary=issue['fields']['summary'],
                                        external=issue['self']
                                    )

                                out += '</table>'

                    elif querystring['view'] == 'fixesissue':
                        if querystring['project'] in projectsFixVersions:
                            versions = projectsFixVersions[querystring['project']]

                            if querystring['version'] in versions:
                                version = versions[querystring['version']]

                                if querystring['issuekey'] in version:
                                    issue = version[querystring['issuekey']]
                                    out += '<pre>%s</pre>' % json.dumps(issue, indent=4)

                except Exception as e:
                    out += exception_html(e)
                    
                self.wfile.write(bytes(
                    """
                    <html>
                        <head>
                            <title>Explorer</title>
                            <link rel="stylesheet" href="/css" media="all">
                        </head>
                        <body>
                            <h1>%s - %s - version %s</h1>
                            %s
                            
                        </body>
                    </html>"""  % (querystring['project'], querystring['view'], querystring['version'], out), "utf-8"))
                
                return True

        return False

    def generate(self, route, querystring):
        if len(route) == 1:
            if route[0] == 'generate':
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
                            <h1>Generating</h1>""", "utf-8"))

                for file in changeRequest.generate():
                    self.wfile.write(bytes('%s<br/>' % file, "utf-8"))

                self.wfile.write(bytes('Complete !<br/><a href="/results">Go to results</a></body></html>', "utf-8"))

                return True

        return False


    def do_GET(self):
        parts = self.path.split('?')
        route = [x for x in parts[0].split('/') if len(x) > 0]
        querystring = {}

        if len(parts) == 2:
            qs = [x for x in parts[1].split('&') if len(x) > 0]
            for q in qs:
                qq = [x for x in q.split('=') if len(x) > 0]
                if len(qq) == 2:
                    querystring[qq[0]] = qq[1]
                else:
                    querystring[qq[0]] = ''
        
        found = False

        try:
            for m in self.middleware:
                found |= m(route, querystring)
                if found:
                    break

            if not found:
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                self.wfile.write(bytes(
                    """
                    <html>
                        <head>
                            <title>Error 404</title>
                        </head>
                        <body>
                            <h1>Page not found</h1>
                            <p>%s</p>
                            <pre>%s</pre>
                            <pre>%s</pre>
                        </body>
                    </html>""" % (self.path, json.dumps(route, indent=2), json.dumps(querystring, indent=2)), "utf-8"))

        except Exception as e:
            if not found:
                self.send_response(500)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                self.wfile.write(bytes(
                    """
                    <html>
                        <head>
                            <title>Error 500</title>
                        </head>
                        <body>
                            <h1>Server Error</h1>
                            %s
                        </body>
                    </html>""" % (exception_html(e)), "utf-8"))
            
        
if __name__ == "__main__":        
    webserver = HTTPServer((hostname, port), WebServer)
    print("Server started http://%s:%s" % (hostname, port))

    try:
        webserver.serve_forever()
    except KeyboardInterrupt:
        pass

    webserver.server_close()