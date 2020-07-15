
import datautil
import datetime
import jsonquery
import json

class Issues:
    def __init__(self, universe_name, data_location = None, data_prefix = None, data_bulk_size = None):
        self.universe_name = universe_name
        self.data_location = data_location
        self.data_prefix = data_prefix
        self.data_bulk_size = data_bulk_size
        self.issue_map = {}

    def load(self):
        count = 0
        while True:
            try:
                with open(self.data_location + self.data_prefix + str(count) + '.json', 'r', encoding='UTF-8') as f:
                    self.add(f.read())
                
                yield self.data_prefix + str(count)

                count += self.data_bulk_size

            except Exception as e:
                print('error', e)
                break

    def add(self, issues_json):
        issues = json.loads(issues_json)
        for issue in issues['issues']:
            datautil.map(self.issue_map, (issue['key'],), issue)
    
    def getUniverseName(self):
        return self.universe_name

    def getDataLocation(self):
        return self.data_location

    def getDataPrefix(self):
        return self.data_prefix

    def get(self, issue_key = None):
        if issue_key is None:
            return self.issue_map
        else:
            return self.issue_map[issue_key]

    def getDateTimeFormat():
        return '%Y-%m-%dT%H:%M:%S.%f%z'

    def parseDateTime(datetime_string):
        try:
            return datetime.datetime.strptime(datetime_string, Issues.getDateTimeFormat())
        except ValueError as e:
            if datetime_string[-5] == ' ':
                datetime_string = datetime_string[:-5] + '+' + datetime_string[-4:]

            return datetime.datetime.strptime(datetime_string, Issues.getDateTimeFormat())

    def parseDateTimeSimple(datetime_string):
        return Issues.parseDateTime(datetime_string + "T0:0:0.000+0000")

    def getExtractedFeatures(self, issue_key, versions, date):
        out = {}

        issue = self.issue_map[issue_key]

        out['created_timestamp'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^created'))
        out['created_date'] = Issues.parseDateTime(out['created_timestamp'])

        if out['created_date'] > date:
            return None
        
        out['summary'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^summary'))
        out['description'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^description'))
        out['resolution_name'] = datautil.unlist_one(jsonquery.query(issue, 'fields.resolution.^name'))
        out['status_name'] = datautil.unlist_one(jsonquery.query(issue, 'fields.status.^name'))
        out['issuetype_name'] = datautil.unlist_one(jsonquery.query(issue, 'fields.issuetype.^name'))
        out['priority_name'] = datautil.unlist_one(jsonquery.query(issue, 'fields.priority.^name'))
        out['components'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^components'))
        out['labels'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^labels'))
        out['assignee_displayName'] = datautil.unlist_one(jsonquery.query(issue, 'fields.assignee.^displayName'))
        out['assignee_accountId'] = datautil.unlist_one(jsonquery.query(issue, 'fields.assignee.^accountId'))
        out['reporter_displayName'] = datautil.unlist_one(jsonquery.query(issue, 'fields.reporter.^displayName'))
        out['reporter_accountId'] = datautil.unlist_one(jsonquery.query(issue, 'fields.reporter.^accountId'))
        
        out['updated_timestamp'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^updated'))
        out['duedate_timestamp'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^duedate'))
        out['resolutiondate_timestamp'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^resolutiondate'))

        out['parent_key'] = datautil.unlist_one(jsonquery.query(issue, 'fields.parent.^key'))

        out['subtasks'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^subtasks'))

        out['number_of_subtasks'] = len(out['subtasks'])
        
        out['fixversion_names'] = jsonquery.query(issue, 'fields.fixVersions.^name')
        out['affectversion_names'] = jsonquery.query(issue, 'fields.versions.^name')

        out['issuelinks'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^issuelinks'))

        out['updated_date'] = None
        out['resolutiondate_date'] = None
        
        change_map_strings = {
            'status': 'status_name',
            'summary': 'summary',
            'assignee': 'assignee_name',
            'security': 'security_name',
            'issuetype': 'issuetype_name',
            'resolution': 'resolution_name',
            'priority': 'priority_name',
            'description': 'description',
            'project': 'project_key',
            'reporter': 'reporter_name',
            'Parent': 'parent_key',
            'Parent Issue': 'parent_key',
            'Project': 'project_key',
            'project': 'project_key',
            'duedate': 'duedate_timestamp'
        }

        change_map_values = {
            'timeoriginalestimate': 'timeoriginalestimate',
            'timespent': 'timespent',
            'timeestimate': 'timeestimate',
        }

        change_map_lists = {
            'labels': 'labels',
            'components': 'components',
            'fixVersions': 'fixversion_names',
            'versions': 'affectversion_names'
        }

        change_map_timestamps = {
            'resolution': 'resolutiondate_timestamp'
        }

        out['changes'] = {}
        for key in list(change_map_strings.values()) + list(change_map_values.values()) + list(change_map_lists.values()):
            out['changes'][key] = []
        
        changes = datautil.map_get(issue, ('changelog', 'histories'))
        if changes is None:
            changes = []

        updated = {
            'updated_timestamp': False,
            'resolutiondate_timestamp': False
        }

        for change in sorted(changes, key=lambda x: Issues.parseDateTime(x['created']), reverse=True):
            change_timestamp = change['created']
            change_date = Issues.parseDateTime(change_timestamp)

            if change_date <= date and not updated['updated_timestamp'] :
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
                    if change_date <= date:
                        matched = True

                        if field in change_map_strings:
                            out['changes'][change_map_strings[field]] += [change]

                        elif field in change_map_values:
                            out['changes'][change_map_values[field]] += [change]
                            
                        elif field in change_map_lists:
                            out['changes'][change_map_lists[field]] += [change]

                        else:
                            matched = False

                        if field in change_map_timestamps:
                            out[change_map_timestamps[field]] = change_timestamp
                            updated[change_map_timestamps[field]] = True

                        if matched:
                            break
                        
                    else:
                        matched = True

                        if field in change_map_strings:
                            out[change_map_strings[field]] = item['fromString']

                        elif field in change_map_values:
                            out[change_map_values[field]] = item['from']
                            
                        elif field in change_map_lists:
                            if not item['toString'] is None:
                                if item['toString'] in out[change_map_lists[field]]:
                                    out[change_map_lists[field]].remove(item['toString'])
                            
                            if not item['fromString'] is None and not item['fromString'] in out[change_map_lists[field]]:
                                out[change_map_lists[field]] += [item['fromString']]
                        
                        elif field == 'Link':
                            if not item['to'] is None:
                                for i in range(len(out['issuelinks'])):
                                    if len(jsonquery.query(out['issuelinks'][i], 'inwardIssue.key:%s' % item['to'])) > 0:
                                        break
                                if i < len(out['issuelinks']):
                                    out['issuelinks'] = out['issuelinks'][:i] + out['issuelinks'][i + 1:]

                            if not item['from'] is None:
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
                                    "inwardIssue": self.get(item['from'])
                                }]
                        else:
                            matched = False
                        
                        if matched:
                            if field in change_map_timestamps:
                                out[change_map_timestamps[field]] = change_timestamp

                            break
        
        for timestamp, value in updated.items():
            if not value:
                out[timestamp] = None

        out['number_of_fixversions'] = len(out['fixversion_names'])
        out['number_of_affectsversions'] = len(out['affectversion_names'])

        out['issuelinks_outward'] = jsonquery.query(out['issuelinks'], '$outwardIssue')
        out['issuelinks_inward'] = jsonquery.query(out['issuelinks'], '$inwardIssue')
        
        out['blocked_by_issuelinks'] = jsonquery.query(out['issuelinks'], '$type.outward:is blocked by')
        out['blocks_issuelinks'] = jsonquery.query(out['issuelinks'], '$type.outward:blocks')

        out['number_of_issuelinks'] = len(out['issuelinks'])
        out['number_of_blocked_by_issues'] = len(out['blocked_by_issuelinks'])
        out['number_of_blocks_issues'] = len(out['blocks_issuelinks'])

        out['parent_summary'] = None
        if not out['parent_key'] is None:
            out['parent_summary'] = self.get(out['parent_key'])['fields']['summary']

        if not out['updated_timestamp'] is None:
            out['updated_date'] = Issues.parseDateTime(out['updated_timestamp'])

        if not out['resolutiondate_timestamp'] is None:
            out['resolutiondate_date'] = Issues.parseDateTime(out['resolutiondate_timestamp'])

        out['issue_duration'] = None
        if not out['updated_date'] is None:
            out['issue_duration'] = out['updated_date'] - out['created_date']

        out['duedate_date'] = None
        if not out['duedate_timestamp'] is None:
            out['duedate_date'] = Issues.parseDateTimeSimple(out['duedate_timestamp'])
        
        out['earliest_duedate'] = out['duedate_date']
        check_versions = []
        if len(out['changes']['fixversion_names']) > 0:
            for change in out['changes']['fixversion_names']:
                items = jsonquery.query(change, 'items.$field:Fix Version')
                for item in items:
                    item_from = item['fromString']
                    item_to = item['toString'] 

                    if not item_from is None:
                        check_versions += [item_from]

                    if not item_to is None:
                        check_versions += [item_to]
                        
        if len(out['fixversion_names']) > 0:
            check_versions += out['fixversion_names']

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

        out['comments'] = jsonquery.query(issue, 'fields.^comment')[0]['comments']
        out['number_of_comments'] = len(out['comments'])
        out['comments_extracted'] = []

        for comment in out['comments']:
            out['comments_extracted'] += [{
                'created_timestamp': comment['created'],
                'created_date': Issues.parseDateTime(comment['created']),
                #updated time.. updated message?
                'author_displayName' : comment['author']['displayName'],
                'author_accountId' : comment['author']['accountId'],
                'message': comment['body']
            }]

        out['discussion_time'] = datetime.timedelta()
        if len(out['comments']) > 0:
            out['first_comment_timestamp'] = out['comments'][0]['created']
            out['last_comment_timestamp'] = out['comments'][len(out['comments']) - 1]['created']

            out['first_comment_date'] = Issues.parseDateTime(out['first_comment_timestamp'])
            out['last_comment_date'] = Issues.parseDateTime(out['last_comment_timestamp'])

            out['discussion_time'] = out['last_comment_date'] - out['first_comment_date']

        return out
