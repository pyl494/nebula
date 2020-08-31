import urllib.parse
import urllib.request
import json

def add(scripts, queue=[]):
    if not isinstance(scripts, list):
        scripts = [scripts]

    data = urllib.parse.urlencode({'scripts': json.dumps(scripts), 'queue': json.dumps(queue)}).encode()
    req = urllib.request.Request('http://localhost:9000/add', data=data)
    with urllib.request.urlopen(req) as f:
        return f.read()

def run():
    with urllib.request.urlopen('http://localhost:9000/run') as f:
        return f.read()
