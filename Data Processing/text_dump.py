# Purpose
# This script extracts all strings from the json dumps and saves them in a separate files

# Instructions
# This script requires the json data dumps

# Status
# This should run.

# Source
# Harun Delic

with open('../jsondumps.txt', 'r') as f:
    ROOT = f.readline()

import importlib.util
spec = importlib.util.spec_from_file_location('jsonquery', 'jsonquery.py')
jsonquery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jsonquery)

import json

count = 0

with open(ROOT + 'ATLASSIAN_strings.txt', 'w', encoding='UTF-8') as out:
    try:
        while True:
            with open(ROOT + 'ATLASSIAN_' + str(count) +'.json', 'r', encoding='UTF-8') as f:
                data = json.loads(f.read())
            print('ATLASSIAN_' + str(count) + '.json')
            
            d = jsonquery.query(data, 'issues.fields.^description')
            
            for i in d:
                if not i is None:
                    out.write(i)

            t = jsonquery.query(data, 'issues.fields.^summary')
            for i in t:
                if not i is None:
                    out.write(i)

            c = jsonquery.query(data, 'issues.fields.comments.comment.^comment')
            for i in c:
                if not i is None:
                    out.write(i)

            count += 1000
    except Exception as e:
        print('error', e)

print('done')