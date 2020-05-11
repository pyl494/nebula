# Purpose
# This script extracts fields from clover issues 
# so they can be inserted with the push_issues.js

# Instructions
# This script requires the json data dumps

# Status
# This should run

# Source
# Harun Delic

with open('../jsondumps.txt', 'r') as f:
    ROOT = f.readline()

import json

count = 0
issues = []

while True:
    try:
        with open(ROOT + 'ATLASSIAN_CLOV_' + str(count) +'.json', 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
        print('ATLASSIAN_CLOV_' + str(count) + '.json')
        
        for x in data['issues']:
            fields = x['fields']

            issue = {}

            t = fields['summary'] 
            if not t is None:
                issue['summary'] = t

            t = fields['description'] 
            if not t is None:
                issue['description'] = t

            t = fields['issuetype'] 
            if not t is None:
                issue['issuetype'] = t['name']

            t = fields['assignee'] 
            if not t is None:
                issue['assignee'] = t['name']

            #t = fields['priority'] 
            #if not t is None:
            #    issue['priority'] = t['name']

            t = fields['resolution'] 
            if not t is None:
                issue['resolution'] = t['name']
            
            issues += [issue]

        count += 1000
    except Exception as e:
        print('error', e)
        break

with open(ROOT + 'ATLASSIAN_fields.json', 'w', encoding='utf-8') as out:
    json.dump({'issues': issues}, out, indent=2)

print('done')