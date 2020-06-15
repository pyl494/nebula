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

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import threading

import traceback, sys
from urllib.parse import unquote_plus

from io import StringIO
import contextlib

import html
import json

@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

def exception_html(e):
    ex_type, ex_value, ex_traceback = sys.exc_info()
    trace_back = traceback.extract_tb(ex_traceback)
    stack_trace = list()
    for trace in trace_back:
        stack_trace.append("<b>@%s</b><br/>    line %d in  %s <br/>    %s" % (html.escape(trace[0]), trace[1], html.escape(trace[2]), html.escape(trace[3])))
    
    return "<div>%s, %s<br/><pre>%s</pre></div>" % (ex_type, ex_value, json.dumps(stack_trace, indent=2))

hostname = "localhost"
port = 8080

STDOUT = sys.stdout

ROOT_DIR = '../'
TEMP_DIR = 'Data Explorer/temp/'

class WebServer(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.middleware = [self.css, self.index, self.const_views, self.mutable_views, self.serve_static]

        super().__init__(*args, **kwargs)

    def send(self, x):
        self.wfile.write(bytes(x, "utf-8"))

    def css(self, route, querystring):
        if len(route) == 1 and route[0] == 'css':
            self.send_response(200)
            self.send_header("Content-type", "text/css")
            self.end_headers()

            with open('./Data Explorer/data_explorer.css', 'r', encoding='utf-8') as f:
                self.send(f.read())

            return True

        return False

    def serve_static(self, route, querystring):
        if len(route) == 1 and route[0] == 'static':
            try:
                path = '../' + querystring['filename']
                print(path)

                with open(path, 'rb') as f:
                    self.send_response(200)
                    self.send_header("Content-type", querystring['contenttype'])
                    self.end_headers()

                    self.wfile.write(f.read())

            except Exception as e:
                print('error', e)
                return True

            return True
        
        return False

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
                    exec(f.read(), locals(), globals())
                
                return True
            except FileNotFoundError as e:
                sys.stdout = STDOUT
                return False
            except Exception as e:
                sys.stdout = STDOUT
                self.send(exception_html(e))
                return True

        return False

    def const_views(self, route, querystring):
        if len(route) == 1:
            try:
                d = dict(locals(), **globals())

                with open('./Data Explorer/const/{route}.py'.format(route = route[0]), 'r') as f:
                    exec(f.read(), d, d)
                    
                return True
            except FileNotFoundError as e:
                sys.stdout = STDOUT
                return False
            except Exception as e:
                sys.stdout = STDOUT
                self.send(exception_html(e))
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

                self.send(
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
                    </html>""" % (html.escape(self.path), html.escape(json.dumps(route, indent=2)), html.escape(json.dumps(querystring, indent=2))))

        except Exception as e:
            if not found:
                self.send_response(500)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                self.send(
                    """
                    <html>
                        <head>
                            <title>Error 500</title>
                        </head>
                        <body>
                            <h1>Server Error</h1>
                            %s
                        </body>
                    </html>""" % (exception_html(e)))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
        
if __name__ == "__main__":        
    webserver = ThreadedHTTPServer((hostname, port), WebServer)
    print("Server started http://%s:%s" % (hostname, port))

    try:
        webserver.serve_forever()
    except KeyboardInterrupt:
        pass

    webserver.server_close()