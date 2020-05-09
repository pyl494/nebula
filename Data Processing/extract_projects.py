# Purpose
# This searches through the multi-project dumps and extracts a single project.
# Sometimes you will find they don't match with the dumps of specific projects.

# Instructions
# This script requires the json data dumps

# Status
# This should run.

# Source
# Harun Delic

ROOT = 'F:/jsondumps/atlassian/'

from jsonquery import query
import json

def extract_project(project):
    r = []
    sum = 0
    count = 0
    while True:
        try:
            with open(ROOT + 'ATLASSIAN_' + str(count) +'.json', 'r') as f:
                data = json.loads(f.read())
            print('ATLASSIAN_' + str(count) + '.json')
            print(len(data['issues']))
            issues = query(data, 'issues.$project.key:' + project)
            r += issues
            
            sum += len(issues)
            print('count', len(issues))

            count += 1000
        except Exception as e:
            print('error', e)
            break

    print('total', sum)

    j = json.dumps({'issues': r}, indent=4)

    with open(ROOT + 'ATLASSIAN_' + project + '.json', 'w') as f:
        f.write(j)

extract_project('CLOV')