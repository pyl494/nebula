import urllib.parse
import urllib.request
import json

def add(scripts):
    if isinstance(scripts, list):
        data = urllib.parse.urlencode({'scripts': json.dumps(scripts)}).encode()
        req = urllib.request.Request('http://localhost:9000/add', data=data)
        with urllib.request.urlopen(req) as f:
            return f.read() == b'success!'

    else:
        scripts = urllib.parse.quote_plus(scripts)

        with urllib.request.urlopen('http://localhost:9000/add?script=' + scripts) as f:
            return f.read() == b'success!'

def run():
    with urllib.request.urlopen('http://localhost:9000/run') as f:
        return f.read() == b'success!'
