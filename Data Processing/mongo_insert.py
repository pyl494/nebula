import json
import wormhole

with open('jsondumps.json', 'r') as f:
    DUMPS = json.loads(f.read())

scripts = []

from pymongo import MongoClient

client = MongoClient(tz_aware=True)
db = client['data-explorer']

for dump in DUMPS:
    if dump['load']:
        print(dump['universe'])
        db['issues_' + dump['universe']].create_index([('self', 1), ('key', 1)], unique=True)
        db['issues_' + dump['universe']].create_index([('key', 1)], unique=True)
        data = None
        count = 0
        while True:
            print(count)
            try:
                filename = dump['location'] + dump['prefix'] + str(count) + '.json'
                with open(filename, 'r', encoding='UTF-8') as f:
                    pass
                scripts += ['''
import json
from pymongo import MongoClient

client = MongoClient(tz_aware=True)
db = client['data-explorer']

issue_collection = db['issues_{universe_name}']

with open('{filename}', 'r', encoding='UTF-8') as f:
    d = json.JSONDecoder(parse_int=lambda x: x).decode(f.read())
    try:
        issue_collection.insert_many(d['issues'], ordered=False)
    except Exception as e:
        print('>>', '!' * 20)
        print('Process Exception !')
        print("Script:")
        print('-' * 20)
        print(s)
        print('-' * 20)
        debug.exception_print(e)
        print('>>', '!' * 20)
                '''.format(
                    universe_name=dump['universe'],
                    filename=filename
                )]
                count += dump['bulkSize']
            except Exception as e:
                print('error', e)
                break

wormhole.add(scripts)
wormhole.run()
