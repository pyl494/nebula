import json
import pprint
import datautil
from pymongo import MongoClient

client = MongoClient()
db = client['data-explorer']
issue_collection = db['issues_Atlassian Ecosystem']

issue = issue_collection.find_one()

out = {}

out['summary'] = datautil.map_get(issue, ('fields', 'summary'))
out['description'] = datautil.map_get(issue, ('fields', 'description'))
out['resolution_name'] = datautil.map_get(issue, ('fields', 'resolution', 'name'))
out['status_name'] = datautil.map_get(issue, ('fields', 'status', 'name'))
out['issuetype_name'] = datautil.map_get(issue, ('fields', 'issuetype', 'name'))
out['priority_name'] = datautil.map_get(issue, ('fields', 'priority', 'name'))
out['components'] = datautil.map_get(issue, ('fields', 'components'), [])
out['labels'] = datautil.map_get(issue, ('fields', 'labels'), [])
out['assignee_displayName'] = datautil.map_get(issue, ('fields', 'assignee'))
out['assignee_accountId'] = datautil.map_get(issue, ('fields', 'assignee', 'accountId'))
out['reporter_displayName'] = datautil.map_get(issue, ('fields', 'reporter', 'displayName'))
out['reporter_accountId'] = datautil.map_get(issue, ('fields', 'reporter', 'accountId'))

print('Extraction')
print('-' * 10)
print(json.dumps(out, indent=2))
print('-' * 10)