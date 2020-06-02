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
from urllib.parse import unquote_plus

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

with open('../jsondumps.txt', 'r') as f:
    ROOT = f.readline()

issueMaps = [
    issues.Issues('Atlassian Projects', ROOT, 'ATLASSIAN_', 1000),
    issues.Issues('Atlassian Ecosystem', 'f:/jsondumps/atlassian_eco/', 'ATLASSIAN_ECO_', 100)
]

changeRequests = [generate_change_requests.GenerateChangeRequests(x) for x in issueMaps]

def exception_html(e):
    ex_type, ex_value, ex_traceback = sys.exc_info()
    trace_back = traceback.extract_tb(ex_traceback)
    stack_trace = list()
    for trace in trace_back:
        stack_trace.append("<b>@%s</b><br/>    line %d in  %s <br/>    %s" % (html.escape(trace[0]), trace[1], html.escape(trace[2]), html.escape(trace[3])))
    
    return "<div>%s, %s<br/><pre>%s</pre></div>" % (ex_type, ex_value, json.dumps(stack_trace, indent=2))

class WebServer(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.middleware = [self.css, self.index, self.const_views, self.mutable_views, self.serve_static]

        super().__init__(*args, **kwargs)

    def css(self, route, querystring):
        if len(route) == 1 and route[0] == 'css':
            self.send_response(200)
            self.send_header("Content-type", "text/css")
            self.end_headers()

            with open('./Data Explorer/data_explorer.css', 'r', encoding='utf-8') as f:
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

    def mutable_views(self, route, querystring):
        if len(route) == 1:
            try:
                with open('./Data Explorer/{route}.py'.format(route = route[0]), 'r') as f:
                    with stdoutIO() as o:
                        exec(f.read(), locals(), globals())
                
                return True
            except FileNotFoundError as e:
                sys.stdout = STDOUT
                return False
            except Exception as e:
                sys.stdout = STDOUT
                self.wfile.write(bytes(exception_html(e), "utf-8"))

        return False

    def const_views(self, route, querystring):
        if len(route) == 1:
            try:
                d = dict(locals(), **globals())

                with open('./Data Explorer/const/{route}.py'.format(route = route[0]), 'r') as f:
                    with stdoutIO() as o:
                        exec(f.read(), d, d)
                
                return True
            except FileNotFoundError as e:
                sys.stdout = STDOUT
                return False
            except Exception as e:
                sys.stdout = STDOUT
                self.wfile.write(bytes(exception_html(e), "utf-8"))

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