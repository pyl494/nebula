import json
from pymongo import MongoClient

client = MongoClient()
db = client['data-explorer']

with open('jsondumps.json', 'r') as f:
    DUMPS = json.loads(f.read())

for dump in DUMPS:
    issue_collection = db['issues_' + dump['universe']]
    print(dump['universe'])

    if dump['load']:
        data = None
        count = 0
        while True:
            print(count)
            try:
                with open(dump['location'] + dump['prefix'] + str(count) + '.json', 'r', encoding='UTF-8') as f:
                    d = json.JSONDecoder(parse_int=lambda x: x).decode(f.read())
                    try:
                        issue_collection.insert_many(d['issues'])
                    except Exception as e:
                        print('error', e)
                        pass

                count += dump['bulkSize']

            except Exception as e:
                print('error', e)
                break