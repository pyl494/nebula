import datautil
import datetime
import jsonquery
import json
import debug

class Issues:
    def __init__(self, universe_name, data_location = None, data_prefix = None, data_bulk_size = None):
        from pymongo import MongoClient

        client = MongoClient()
        db = client['data-explorer']

        self.universe_name = universe_name
        self.data_location = data_location
        self.data_prefix = data_prefix
        self.data_bulk_size = data_bulk_size

        self.collection_issues = db['issues_' + universe_name]
        self.collection_features = db['features_' + universe_name]

        try:
            self.collection_issues.create_index([('self', 1), ('key', 1)], unique=True)
            self.collection_issues.create_index([('key', 1)], unique=True)
        except Exception as e:
            debug.exception_print(e)
            print('failed to set index on self and key')

        try:
            self.collection_features.create_index([('issue_key', 1), ('target_date', 1)], unique=True)
        except Exception as e:
            debug.exception_print(e)
            print('failed to set index on features')

    def read(self):
        count = 0
        while True:
            try:
                with open(self.data_location + self.data_prefix + str(count) + '.json', 'r', encoding='UTF-8') as f:
                    d = f.read()

                yield d

                count += self.data_bulk_size

            except Exception as e:
                debug.exception_print(e)
                break

    def add(self, issues):
        for issue in issues:
            self.collection_issues.update_one({'self': issue['self'], 'issue_key': issue['key']}, {'$set': issue}, upsert=True)

    def getUniverseName(self):
        return self.universe_name

    def getDataLocation(self):
        return self.data_location

    def getDataPrefix(self):
        return self.data_prefix

    def getIssueByKey(self, issue_key):
        return self.collection_issues.find_one({'key': issue_key})

    def getIssuesByKeys(self, issue_keys):
        return self.collection_issues.find({'key': {'$in': issue_keys}})

    def getIssueByQuery(self, query):
        return self.collection_issues.find_one(query)

    def getIssuesByQuery(self, query):
        return self.collection_issues.find(query)

    def getIssuesIterator(self):
        return self.collection_issues.find({})

    def getDateTimeFormat():
        return '%Y-%m-%dT%H:%M:%S.%f%z'

    def parseDateTime(datetime_string):
        try:
            return datetime.datetime.strptime(datetime_string, Issues.getDateTimeFormat()).replace(tzinfo=None)
        except ValueError:
            if datetime_string[-5] == ' ':
                datetime_string = datetime_string[:-5] + '+' + datetime_string[-4:]

            return datetime.datetime.strptime(datetime_string, Issues.getDateTimeFormat()).replace(tzinfo=None)

    def parseDateTimeSimple(datetime_string):
        return Issues.parseDateTime(datetime_string + "T0:0:0.000+0000")

    def getExtractedFeaturesMeta(self=None):
        out = {}
        out['change_map'] = {
            'status': {'toString': 'status_name'},
            'summary': {'toString': 'summary'},
            'assignee': {'toString': 'assignee_displayName', 'to': 'assignee_key'},
            'security': {'toString': 'security_name'},
            'issuetype': {'toString': 'issuetype_name'},
            'resolution': {'toString': 'resolution_name'},
            'priority': {'toString': 'priority_name'},
            'description': {'toString': 'description'},
            'project': {'toString': 'project_key'},
            'reporter': {'toString': 'reporter_displayName', 'to': 'reporter_key'},
            'Parent': {'toString': 'parent_key'},
            'Parent Issue': {'toString': 'parent_key'},
            'Project': {'toString': 'project_key'},
            'project': {'toString': 'project_key'},
            'duedate': {'toString': 'duedate_timestamp'},
            'timeoriginalestimate': {'to': 'timeoriginalestimate'},
            'timespent': {'to': 'timespent'},
            'timeestimate': {'to': 'timeestimate'},
        }

        out['change_map_lists'] = {
            'labels': 'labels',
            'components': 'components',
            'fixVersions': 'fixVersion_names',
            'versions': 'affectsVersion_names'
        }

        out['change_map_timestamps'] = {
            'resolution': 'resolutiondate_timestamp'
        }

        out['change_map_names'] = [x['toString'] if 'toString' in x else x['to'] for x in out['change_map'].values()] + list(out['change_map_lists'].values())

        return out

    def getExtractedFeatures(self, issue, versions, target_date):
        issue_key = issue['key']
        target_date = target_date.replace(tzinfo=None)

        out = self.collection_features.find_one({'issue_key': issue_key, 'target_date': target_date})

        if not out is None:
            return out

        out = {}

        out['issue_key'] = issue_key
        out['target_date'] = target_date

        out['created_timestamp'] = datautil.map_get(issue, ('fields', 'created'))
        out['created_date'] = Issues.parseDateTime(out['created_timestamp'])

        if out['created_date'] > target_date:
            return None

        out['summary'] = datautil.map_get(issue, ('fields', 'summary'))
        out['description'] = datautil.map_get(issue, ('fields', 'description'))
        out['resolution_name'] = datautil.map_get(issue, ('fields', 'resolution', 'name'))
        out['status_name'] = datautil.map_get(issue, ('fields', 'status', 'name'))
        out['issuetype_name'] = datautil.map_get(issue, ('fields', 'issuetype', 'name'))
        out['priority_name'] = datautil.map_get(issue, ('fields', 'priority', 'name'))
        out['components'] = datautil.map_get(issue, ('fields', 'components'), [])
        out['labels'] = datautil.map_get(issue, ('fields', 'labels'), [])
        out['assignee_displayName'] = datautil.map_get(issue, ('fields', 'assignee', 'displayName'))
        out['assignee_key'] = datautil.map_get(issue, ('fields', 'assignee', 'key'))
        out['assignee_accountId'] = datautil.map_get(issue, ('fields', 'assignee', 'accountId'))
        out['reporter_displayName'] = datautil.map_get(issue, ('fields', 'reporter', 'displayName'))
        out['reporter_accountId'] = datautil.map_get(issue, ('fields', 'reporter', 'accountId'))
        out['reporter_key'] = datautil.map_get(issue, ('fields', 'reporter', 'key'))

        out['updated_timestamp'] = datautil.map_get(issue, ('fields', 'updated'))
        out['duedate_timestamp'] = datautil.map_get(issue, ('fields', 'duedate'))
        out['resolutiondate_timestamp'] = datautil.map_get(issue, ('fields', 'resolutiondate'))

        out['parent_key'] = datautil.map_get(issue, ('fields', 'parent', 'key'))

        out['subtasks'] = datautil.map_get(issue, ('fields', 'subtasks'), [])

        out['number_of_subtasks'] = len(out['subtasks'])

        out['fixVersion_names'] = datautil.map_get(issue, ('fields', 'fixVersions', 'name'), [])
        out['affectsVersion_names'] = datautil.map_get(issue, ('fields', 'versions', 'name'), [])

        out['issuelinks'] = datautil.map_get(issue, ('fields', 'issuelinks'), [])

        out['updated_date'] = None
        out['resolutiondate_date'] = None

        meta = Issues.getExtractedFeaturesMeta()

        out['changes'] = {}

        for key in meta['change_map_names']:
            out['changes'][key] = []

        changes = datautil.map_get(issue, ('changelog', 'histories'), [])

        updated = {
            'updated_timestamp': False,
            'resolutiondate_timestamp': False
        }

        for change in sorted(changes, key=lambda x: Issues.parseDateTime(x['created']), reverse=True):
            change_timestamp = change['created']
            change_date = Issues.parseDateTime(change_timestamp)

            if change_date <= target_date and not updated['updated_timestamp'] :
                updated['updated_timestamp'] = True
                out['updated_timestamp'] = change_timestamp

            # reverse the changes
            for item in change['items']:
                changeFields = []
                if 'field' in item:
                    changeFields += [item['field']]

                if 'fieldId' in item:
                    changeFields += [item['fieldId']]

                for field in changeFields:
                    if change_date <= target_date:
                        matched = True

                        if field in meta['change_map']:
                            conv = meta['change_map'][field]
                            if 'toString' in conv:
                                out['changes'][conv['toString']] += [change]
                            else:
                                out['changes'][conv['to']] += [change]

                        elif field in meta['change_map_lists']:
                            out['changes'][meta['change_map_lists'][field]] += [change]

                        else:
                            matched = False

                        if field in meta['change_map_timestamps']:
                            out[meta['change_map_timestamps'][field]] = change_timestamp
                            updated[meta['change_map_timestamps'][field]] = True

                        if matched:
                            break

                    else:
                        matched = True

                        if field in meta['change_map']:
                            conv = meta['change_map'][field]
                            if 'toString' in conv:
                                out[conv['toString']] = item['fromString']

                            if 'to' in field:
                                out[conv['to']] = item['from']

                        elif field in meta['change_map_lists']:
                            conv = meta['change_map_lists'][field]

                            if not item['toString'] is None:
                                if item['toString'] in out[conv]:
                                    out[conv].remove(item['toString'])

                            if not item['fromString'] is None and not item['fromString'] in out[conv]:
                                out[conv] += [item['fromString']]

                        elif field == 'Link':
                            if not item['to'] is None:
                                for i in range(len(out['issuelinks'])):
                                    if len(jsonquery.query(out['issuelinks'][i], 'inwardIssue.key:%s' % item['to'])) > 0:
                                        out['issuelinks'] = out['issuelinks'][:i] + out['issuelinks'][i + 1:]
                                        break

                            if not item['from'] is None:
                                issue_summary = {
                                    "id": None,
                                    "key": item['from'],
                                    "self": None,
                                    "fields": {
                                        "summary": None,
                                        "status": {
                                            "self": None,
                                            "description": None,
                                            "iconUrl": None,
                                            "name": None,
                                            "id": None,
                                            "statusCategory": {
                                                "self": None,
                                                "id": None,
                                                "key": None,
                                                "colorName": None,
                                                "name": None
                                            }
                                        },
                                        "priority": {
                                            "self": None,
                                            "iconUrl": None,
                                            "name": None,
                                            "id": None
                                        },
                                        "issuetype": {
                                            "self": None,
                                            "id": None,
                                            "description": None,
                                            "iconUrl": None,
                                            "name": None,
                                            "subtask": None,
                                            "avatarId": None
                                        }
                                    }
                                }

                                from_issue = self.getIssueByKey(item['from'])
                                if not from_issue is None:
                                    issue_summary = from_issue

                                out['issuelinks'] += [{
                                    "id": None,
                                    "self": None,
                                    "type": {
                                        "id": None,
                                        "name": item['fromString'],
                                        "inward": item['fromString'],
                                        "outward": None,
                                        "self": None
                                    },
                                    "inwardIssue": issue_summary
                                }]
                        else:
                            matched = False

                        if matched:
                            if field in meta['change_map_timestamps']:
                                out[meta['change_map_timestamps'][field]] = change_timestamp

                            break

        for timestamp, value in updated.items():
            if not value:
                out[timestamp] = None

        out['number_of_fixVersions'] = len(out['fixVersion_names'])
        out['number_of_affectsversions'] = len(out['affectsVersion_names'])

        out['issuelinks_outward'] = jsonquery.query(out['issuelinks'], '$outwardIssue')
        out['issuelinks_inward'] = jsonquery.query(out['issuelinks'], '$inwardIssue')

        out['blocked_by_issuelinks'] = jsonquery.query(out['issuelinks'], '$type.outward:is blocked by')
        out['blocks_issuelinks'] = jsonquery.query(out['issuelinks'], '$type.outward:blocks')

        out['number_of_issuelinks'] = len(out['issuelinks'])
        out['number_of_blocked_by_issues'] = len(out['blocked_by_issuelinks'])
        out['number_of_blocks_issues'] = len(out['blocks_issuelinks'])

        out['parent_summary'] = None
        if not out['parent_key'] is None:
            parent_issue = self.getIssueByKey(out['parent_key'])
            if not parent_issue is None:
                out['parent_summary'] = datautil.map_get(parent_issue, ('fields', 'summary'))

        if not out['updated_timestamp'] is None:
            out['updated_date'] = Issues.parseDateTime(out['updated_timestamp'])

        if not out['resolutiondate_timestamp'] is None:
            out['resolutiondate_date'] = Issues.parseDateTime(out['resolutiondate_timestamp'])

        out['issue_duration'] = datetime.timedelta()
        if not out['updated_date'] is None:
            out['issue_duration'] = out['updated_date'] - out['created_date']

        out['duedate_date'] = None
        if not out['duedate_timestamp'] is None:
            out['duedate_date'] = Issues.parseDateTimeSimple(out['duedate_timestamp'])

        out['earliest_duedate'] = out['duedate_date']
        check_versions = []
        if len(out['changes']['fixVersion_names']) > 0:
            for change in out['changes']['fixVersion_names']:
                items = jsonquery.query(change, 'items.$field:Fix Version')
                for item in items:
                    item_from = item['fromString']
                    item_to = item['toString']

                    if not item_from is None:
                        check_versions += [item_from]

                    if not item_to is None:
                        check_versions += [item_to]

        if len(out['fixVersion_names']) > 0:
            check_versions += out['fixVersion_names']

        for version_name in check_versions:
            if version_name in versions:
                version = versions[version_name]
                if 'releaseDate' in version:
                    version_date = Issues.parseDateTimeSimple(version['releaseDate'])
                    if out['earliest_duedate'] is None or version_date < out['earliest_duedate']:
                        out['earliest_duedate'] = version_date

        out['delays'] = datetime.timedelta()
        if not out['earliest_duedate'] is None and not out['resolutiondate_date'] is None:
            out['delays'] = out['resolutiondate_date'] - out['earliest_duedate']

        comments = jsonquery.query(issue, 'fields.^comment')[0]['comments']

        out['comments'] = []

        for comment in comments:
            comment_created_timestamp = datautil.map_get(comment,('created',))
            comment_date =  Issues.parseDateTime(comment_created_timestamp)
            if comment_date <= target_date:
                out['comments'] += [{
                    'created_timestamp': datautil.map_get(comment, ('created',)),
                    'created_date': comment_date,
                    #updated time.. updated message?
                    'author_displayName' : datautil.map_get(comment, ('author', 'displayName')),
                    'author_accountId' : datautil.map_get(comment, ('author', 'accountId')),
                    'message': datautil.map_get(comment, ('body',))
                }]

        out['number_of_comments'] = len(out['comments'])

        out['discussion_time'] = datetime.timedelta()
        if out['number_of_comments'] > 0:
            out['first_comment_date'] = out['comments'][0]['created_date']
            out['last_comment_date'] = out['comments'][-1]['created_date']

            out['discussion_time'] = out['last_comment_date'] - out['first_comment_date']

        out['delays'] = out['delays'].total_seconds()
        out['issue_duration'] = out['issue_duration'].total_seconds()
        out['discussion_time'] = out['discussion_time'].total_seconds()

        self.collection_features.update_one({'issue_key': issue_key, 'target_date': target_date}, {'$set': out}, upsert=True)

        return out
