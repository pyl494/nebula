
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
                #if count > self.data_bulk_size:
                #    break######### REMOVE THIS TO PROCESS ALL FILES

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
        return datetime.datetime.strptime(datetime_string, Issues.getDateTimeFormat())

    def parseDateTimeSimple(datetime_string):
        return datetime.datetime.strptime(datetime_string + "T0:0:0.000+0000", Issues.getDateTimeFormat())

    def getExtractedFeatures(self, issue_key, versions):
        out = {}

        issue = self.issue_map[issue_key]

        out['summary'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^summary'))
        out['resolution_name'] = datautil.unlist_one(jsonquery.query(issue, 'fields.resolution.^name'))
        out['issuetype_name'] = datautil.unlist_one(jsonquery.query(issue, 'fields.issuetype.^name'))
        out['priority_name'] = datautil.unlist_one(jsonquery.query(issue, 'fields.priority.^name'))
        out['assignee_displayName'] = datautil.unlist_one(jsonquery.query(issue, 'fields.assignee.^displayName'))
        out['assignee_accountId'] = datautil.unlist_one(jsonquery.query(issue, 'fields.assignee.^accountId'))
        out['reporter_displayName'] = datautil.unlist_one(jsonquery.query(issue, 'fields.reporter.^displayName'))
        out['reporter_accountId'] = datautil.unlist_one(jsonquery.query(issue, 'fields.reporter.^accountId'))
        out['fixversion_names'] = jsonquery.query(issue, 'fields.fixVersions.^name')
        out['affectversion_names'] = jsonquery.query(issue, 'fields.versions.^name')
        out['created_timestamp'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^created'))
        out['updated_timestamp'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^updated'))
        out['duedate_timestamp'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^duedate'))
        out['resolutiondate_timestamp'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^resolutiondate'))

        out['assignee_changes'] = jsonquery.query(issue, 'changelog.histories.$items.field:assignee')
        out['status_changes'] = jsonquery.query(issue, 'changelog.histories.$items.field:status')
        out['resolution_changes'] = jsonquery.query(issue, 'changelog.histories.$items.field:resolution')
        out['priority_changes'] = jsonquery.query(issue, 'changelog.histories.$items.field:priority')
        out['issuetype_changes'] = jsonquery.query(issue, 'changelog.histories.$items.field:issuetype')
        out['fixversion_changes'] = jsonquery.query(issue, 'changelog.histories.$items.field:Fix Version')
        out['affectsversion_changes'] = jsonquery.query(issue, 'changelog.histories.$items.field:Version')
        out['description_changes'] = jsonquery.query(issue, 'changelog.histories.$items.field:description')

        out['created_date'] = Issues.parseDateTime(out['created_timestamp'])
        
        out['updated_date'] = None
        if not out['updated_timestamp'] is None:
            out['updated_date'] = Issues.parseDateTime(out['updated_timestamp'])
        
        out['resolutiondate_date'] = None
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
        if len(out['fixversion_changes']) > 0:
            for change in out['fixversion_changes']:
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

        out['number_of_fixversions'] = len(out['fixversion_names'])
        out['number_of_affectsversions'] = len(out['affectversion_names'])

        out['description'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^description'))

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

        out['issuelinks'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^issuelinks'))
        out['issuelinks_outward'] = jsonquery.query(issue, 'fields.issuelinks.$outwardIssue')
        out['issuelinks_inward'] = jsonquery.query(issue, 'fields.issuelinks.$inwardIssue')
        
        out['blocked_by_issuelinks'] = jsonquery.query(out['issuelinks'], '$type.outward:is blocked by')
        out['blocks_issuelinks'] = jsonquery.query(out['issuelinks'], '$type.outward:blocks')

        out['number_of_issuelinks'] = len(out['issuelinks'])
        out['number_of_blocked_by_issues'] = len(out['blocked_by_issuelinks'])
        out['number_of_blocks_issues'] = len(out['blocks_issuelinks'])

        out['parent_key'] = datautil.unlist_one(jsonquery.query(issue, 'fields.parent.^key'))
        out['parent_summary'] = datautil.unlist_one(jsonquery.query(issue, 'fields.parent.fields.^summary'))

        out['subtasks'] = datautil.unlist_one(jsonquery.query(issue, 'fields.^subtasks'))

        out['number_of_subtasks'] = len(out['subtasks'])

        return out
