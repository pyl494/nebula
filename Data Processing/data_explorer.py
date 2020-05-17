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
from urllib.parse import unquote_plus

from jsonquery import query

from io import StringIO
import contextlib

import html

@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

hostname = "localhost"
port = 8080

STDOUT = sys.stdout

changeRequest = GenerateChangeRequests()

def exception_html(e):
    ex_type, ex_value, ex_traceback = sys.exc_info()
    trace_back = traceback.extract_tb(ex_traceback)
    stack_trace = list()
    for trace in trace_back:
        stack_trace.append("<b>@%s</b><br/>    line %d in  %s <br/>    %s" % (html.escape(trace[0]), trace[1], html.escape(trace[2]), html.escape(trace[3])))
    
    return "<div>%s, %s<br/><pre>%s</pre></div>" % (ex_type, ex_value, json.dumps(stack_trace, indent=2))

class WebServer(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.middleware = [self.css, self.index, self.results, self.view, self.generate, self.repl, self.serve_static]

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

    def serve_static(self, route, querystring):
        try:
            rr = []
            for r in route:
                rr += [unquote_plus(r)]

            path = '../' + '/'.join(rr)
            print(path)
            type = rr[-1].split('.')[1]

            with open(path, encoding = 'utf-8') as f:
                self.send_response(200)
                self.send_header("Content-type", "text/%s" % type)
                self.end_headers()

                self.wfile.write(bytes(f.read(), 'utf-8'))

        except Exception as e:
            print('error', e)
            return False

        return True

    def index(self, route, querystring):
        if len(route) == 0:
            self.send_response(301)
            self.send_header("Location", "/generate")
            self.end_headers()

            return True

        return False

    def repl(self, route, querystring):
        if len(route) == 1:
            if route[0] == 'repl':
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                
                versionMap = changeRequest.getVersionMap()
                projectsFixVersions = changeRequest.getProjectsFixVersions()
                projectsAffectsVersions = changeRequest.getProjectsAffectsVersions()

                result = ""
                htmlinjection = ""
                d = dict(locals(), **globals())
                
                variables = "<table><tr><th>Variable</th><th>Value</th></tr>"

                for key, value in d.items():
                    v = ''

                    if isinstance(value, list):
                        v = '[...] len: %s, size: %s bytes' % (html.escape(str(len(value))), html.escape(str(sys.getsizeof(value))))
                    elif isinstance(value, tuple):
                        v = '(...) len: %s, size: %s bytes' % (html.escape(str(len(value))), html.escape(str(sys.getsizeof(value))))
                    elif isinstance(value, dict):
                        v = '{...} size: %s bytes' % html.escape(str(sys.getsizeof(value)))
                    else:
                        v = str(value)
                    
                    variables += "<tr><td>{variable}</td><td>{value}</td></tr>".format(
                        variable = html.escape(key),
                        value = html.escape(v)
                    )
                
                variables += "</table>"

                default = """
print("Hello world!")
result = "Hello world !"
                    """

                out = ["""
                    <h2>Enter code</h2>
                    <div class="columncontainer">
                        <div class="column" style="flex-basis: 200%; flex-grow: 2;">
                            <form action="/repl" method="GET">
                                <textarea id="myTextArea" name="source" rows="12" cols="120">{default}</textarea> <br/>
                                <button type="submit">Submit</button>
                            </form>
                        </div>
                        <div class="column">
                            <div class="variableinspector">
                                {variables}
                            </div>
                        </div>
                    </div>
                    <br/>
                    """]

                if 'source' in querystring:
                    source = querystring['source']
                    default = source

                    out += ["<hr><br/><h2>Source</h2><pre>{source}</pre><br/><hr><br/><h2>Output</h2>".format(source=source)]
                    
                    try:
                        with stdoutIO() as o:
                            exec(source, d, d)

                            out += ["<pre>%s</pre><br/>" % html.escape(o.getvalue())]
                            
                    except Exception as e:
                        sys.stdout = STDOUT
                        out += [exception_html(e)]

                    out += ["<hr><br/><h2>Result:</h2><pre>{result}</pre>".format(
                        result = html.escape(str(d['result']))
                    )]

                    out += [str(d['htmlinjection'])]

                out[0] = out[0].format(
                    default = html.escape(default),
                    variables = variables
                )

                self.wfile.write(bytes(
                    """
                    <html>
                        <head>
                            <title>Explorer</title>
                            <link rel="stylesheet" href="/css" media="all">
                            <link rel="stylesheet" href="/Third Party/codemirror.css">
                            <script src="/Third Party/codemirror.js"></script>
                            <script src="/Third Party/codemirror_python.js"></script>
                        </head>
                        <body>
                            <h1>Python REPL</h1>
                            You can interact with the python without restarting the server.<br/>""", 'utf-8'))
                
                for line in out:
                    self.wfile.write(bytes(line, 'utf-8'))

                self.wfile.write(bytes("""
                            <script>
                            var myTextArea = document.getElementById('myTextArea');
                            var myCodeMirror = CodeMirror.fromTextArea(myTextArea, { 
                                value: myTextArea.value,
                                lineNumbers: true
                            });
                            </script>
                        </body>
                    </html>""", 'utf-8'))
                    
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
                    out += "<h2>%s</h2>" % html.escape(key)
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
                            date = html.escape(releaseDate),
                            version = html.escape(versionName),
                            key = html.escape(key),
                            acount = acount,
                            fcount = fcount
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

                    if querystring['view'] == 'fixes' or querystring['view'] == 'affected':
                        versions = {}

                        if querystring['view'] == 'fixes':
                            versions = projectsFixVersions[querystring['project']]
                        else:
                            versions = projectsAffectsVersions[querystring['project']]

                        if querystring['version'] in versions:
                            version = versions[querystring['version']]

                            out += '<table><tr><th>Created Date</th><th>Updated Date</th><th>Priority</th><th>Issue Type</th><th>Status</th><th>Resolution</th><th>Issue Key</th><th width="50%">Summary</th><th>Data</th><th>External Link</th></tr>'

                            for issuekey, issue in version.items():
                                priority = ' :: '.join(query(issue, 'fields.priority.^name'))
                                status = ' :: '.join(query(issue, 'fields.status.^name'))
                                resolution = ' :: '.join(query(issue, 'fields.resolution.^name'))
                                issuetype = ' :: '.join(query(issue, 'fields.issuetype.^name'))

                                out += """
                                    <tr>
                                        <td>{cdate}</td>
                                        <td>{udate}</td>
                                        <td>{priority}</td>
                                        <td>{issuetype}</td>
                                        <td>{status}</td>
                                        <td>{resolution}</td>
                                        <td>{issuekey}</td>
                                        <td>{summary}</td>
                                        <td>
                                            <a href="/view?project={key}&version={version}&issuekey={issuekey}&view={view}issue">View Issue</a>
                                        </td>
                                        <td>
                                            <a href="{external}">External Link</a>
                                        </td>
                                    </tr>
                                """.format(
                                    view = html.escape(querystring['view']),
                                    cdate = html.escape(issue['fields']['created']),
                                    udate = html.escape(issue['fields']['updated']),
                                    key = html.escape(querystring['project']),
                                    priority = html.escape(priority),
                                    status = html.escape(status),
                                    resolution = html.escape(resolution),
                                    issuetype = html.escape(issuetype),
                                    version = html.escape(querystring['version']),
                                    issuekey = html.escape(issuekey),
                                    summary = html.escape(issue['fields']['summary']),
                                    external = html.escape(issue['self'])
                                )

                            out += '</table>'

                    elif querystring['view'] == 'fixesissue' or querystring['view'] == 'affectedissue':
                        
                        versions = []
                        if querystring['view'] == 'fixesissue':
                            versions = projectsFixVersions[querystring['project']]
                        else: 
                            versions = projectsAffectsVersions[querystring['project']]

                        if querystring['version'] in versions:
                            version = versions[querystring['version']]

                            if querystring['issuekey'] in version:
                                issue = version[querystring['issuekey']]
                                out += '<pre>%s</pre>' % html.escape(json.dumps(issue, indent=4))

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
                    </html>"""  % (html.escape(querystring['project']), html.escape(querystring['view']), html.escape(querystring['version']), out), "utf-8"))
                
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
                    self.wfile.write(bytes('%s<br/>' % html.escape(file), "utf-8"))

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
                    querystring[qq[0]] = unquote_plus(qq[1])
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
                    </html>""" % (html.escape(self.path), html.escape(json.dumps(route, indent=2)), html.escape(json.dumps(querystring, indent=2)), "utf-8")))

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