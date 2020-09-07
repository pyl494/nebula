import debug

def process_run(script, queue):
    try:
        d = {**globals(), **locals()}
        exec(script, d, d)
        work = d['work']
        return work(queue)
    except Exception as e:
        print('!' * 20)
        print('Process Exception !')
        print("Script:")
        print('-' * 20)
        print(script)
        print('-' * 20)
        debug.exception_print(e)
        print('!' * 20)
        return None

if __name__ == '__main__':
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn

    import cgi

    import sys
    from urllib.parse import unquote_plus
    from urllib.parse import parse_qs

    import json

    PORT = 9000

    from multiprocessing import Manager, Queue, set_start_method
    set_start_method('spawn')
    manager = Manager()
    script_queue = Queue()
    work_queue = manager.Queue()

    class Wormhole(BaseHTTPRequestHandler):
        def parse_querystring(self, qs):
            if isinstance(qs, str) or isinstance(qs, bytes):
                qs = parse_qs(qs, keep_blank_values=True, encoding='utf-8')

            out = {}
            for key, value in qs.items():
                if isinstance(key, bytes):
                    key = key.decode('utf-8')

                if len(value) > 0:
                    out[key] = value[-1]
                    if isinstance(value[-1], bytes):
                        out[key] = out[key].decode('utf-8')
                else:
                    out[key] = ''

            return out

        def send(self, x):
            self.wfile.write(bytes(x, "utf-8"))

        def do_POST(self):
            postvars = {}
            length = int(self.headers.get('content-length'))
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))

            if ctype == 'multipart/form-data':
                content = cgi.parse_multipart(self.rfile, pdict)
                postvars = self.parse_querystring(content)
                postvars['raw'] = content

            elif ctype == 'application/x-www-form-urlencoded':
                content = self.rfile.read(length)
                postvars = self.parse_querystring(content)
                postvars['raw'] = content

            else:
                postvars['raw'] = self.rfile.read(length)

            parts = self.path.split('?')
            route = [x for x in parts[0].split('/') if len(x) > 0]
            querystring = {}

            if len(parts) == 2:
                querystring = self.parse_querystring(parts[1])

            self.send_response(200)
            self.end_headers()

            try:
                if len(route) == 1:
                    if route[0] == 'add':
                        print(postvars)
                        scripts = json.loads(postvars['scripts'])
                        queue = json.loads(postvars['queue'])
                        print('#scripts', len(scripts))
                        print('#work', len(queue))
                        print(scripts[0])
                        print(queue[0])

                        script_queue.put(scripts)

                        for item in queue:
                            work_queue.put(item)

                    self.send('success!')
            except Exception as e:
                debug.exception_print(e)
                self.send('error!')

        def do_GET(self):
            parts = self.path.split('?')
            route = [x for x in parts[0].split('/') if len(x) > 0]
            querystring = {}

            if len(parts) == 2:
                querystring = self.parse_querystring(parts[1])

            self.send_response(200)
            self.end_headers()

            try:
                if len(route) == 1:
                    if route[0] == 'add':
                        script_queue.put((querystring['script'],))
                    elif route[0] == 'run':
                        from multiprocessing import Pool, cpu_count
                        from functools import partial
                        with Pool(processes=cpu_count()) as p:
                            scripts = []
                            global work_queue
                            queue = work_queue
                            work_queue = manager.Queue()
                            while not script_queue.empty():
                                scripts += script_queue.get()

                            results = [x for x in p.map(partial(process_run, queue=queue), scripts)]
                            self.send(json.dumps(results))


            except Exception as e:
                debug.exception_print(e)
                self.send('error!')

    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        """Handle requests in a separate thread."""

    server = ThreadedHTTPServer(('', PORT), Wormhole)

    server.serve_forever()
