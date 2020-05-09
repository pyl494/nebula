# Purpose
# This is a minimal example of working with the json data dumps

# Instructions
# This script requires the json data dumps

# Status
# This should run.

# Source
# Harun Delic

from jsonquery import query
import json

with open('../jsondumps.txt', 'r') as f:
    ROOT = f.readline()

with open(ROOT + 'ATLASSIAN_CLOV_0.json', 'r', encoding='UTF-8') as f:
    data = json.loads(f.read())

d = query(data, 'issues.fields.^summary')
print(json.dumps(d))
