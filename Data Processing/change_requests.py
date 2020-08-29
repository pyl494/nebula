# Purpose
# This scans jira issues and tries to generate change requests from fix versions and affects versions

# Instructions
# This script requires the json data dumps

# Source
# Harun Delic

import jsonquery
import json
import datetime
import datautil
import wormhole
import debug

import issues
from machine_learning import MachineLearningModel

class JSONDumper(json.JSONEncoder):
     def default(self, obj):
         return str(obj)

class ChangeRequest:
    def __init__(self, issue_map):
        self.issue_map = issue_map

        from pymongo import MongoClient

        client = MongoClient()
        db = client['data-explorer']
        self.collection_projects_fixVersions_issue_map = db[self.issue_map.getUniverseName() + '_projects_fixVersions_issue_map']
        self.collection_projects_affectsVersions_issue_map = db[self.issue_map.getUniverseName() + '_projects_affectsVersions_issue_map']
        self.collection_projects_versions_release_date_map = db[self.issue_map.getUniverseName() + '_projects_versions_release_date_map']
        self.collection_projects_versions_map = db[self.issue_map.getUniverseName() + '_projects_versions_map']
        self.collection_feature_names = db[self.issue_map.getUniverseName() + '_feature_names']
        self.collection_change_request_meta_map = db[self.issue_map.getUniverseName() + '_change_request_meta_map']

        try:
            self.collection_change_request_meta_map.create_index([('issue_key', 1)], unique=True)
        except Exception as e:
            debug.exception_print(e)
            print('failed to set index on features')

        self.machine_learning_model = MachineLearningModel(self)

    def get_change_request_meta(self, change_request_issue_key):
        return self.collection_change_request_meta_map.find_one({'issue_key': change_request_issue_key})

    def iterate_change_request_meta_map(self, sorted=False, start=None, limit=None):
        commands = []

        if sorted:
            commands += [{'$sort': {'project_key': 1, 'fixVersion_name': 1}}]

        if not start is None:
            commands += [{'$skip': start}]

        if not limit is None:
            commands += [{'$limit': limit}]

        cursor = self.collection_change_request_meta_map.aggregate(commands)

        for result in cursor:
            yield result

    def getIssueMap(self):
        return self.issue_map

    def getMachineLearningModel(self):
        return self.machine_learning_model

    def getAutomaticRiskLabel(self, change_request_issue_key):
        change_request_meta = self.get_change_request_meta(change_request_issue_key)
        acount = len(change_request_meta['affected_issues'])

        fcomment_count = 0
        fvote_count = 0
        for issue_key in change_request_meta['linked_issues']:
            issue = self.issue_map.getIssueByKey(issue_key)
            fvote_count += int(issue['fields']['votes']['votes'])
            for comment in issue['fields']['comment']['comments']:
                if issues.Issues.parseDateTime(comment['created']) >= change_request_meta['release_date'].replace(tzinfo=None):
                    fcomment_count += 1

        acomment_count = 0
        avote_count = 0
        for issue_key in change_request_meta['affected_issues']:
            issue = self.issue_map.getIssueByKey(issue_key)
            acomment_count += len(issue['fields']['comment']['comments'])
            avote_count += int(issue['fields']['votes']['votes'])

        interactivity = fcomment_count + fvote_count + acomment_count + avote_count + acount

        if interactivity >= 50:
            return 'high'
        elif acount >= 5:
            return 'medium'
        else:
            return 'low'

    def getManualRiskLabel(self, change_request_issue_key):
        try:
            project_key = self.get_change_request_meta(change_request_issue_key)['project_key']

            filename = '../Data Labels/' + self.issue_map.getUniverseName() + '_' + project_key + '.json'
            with open(filename, 'r') as f:
                labels = json.loads(f.read())

            return labels[change_request_issue_key]

        except Exception as e:
            return None

    def setManualRiskLabel(self, change_request_issue_key, label):
        try:
            project_key = self.get_change_request_meta(change_request_issue_key)['project_key']

            filename = '../Data Labels/' + self.issue_map.getUniverseName() + '_' + project_key + '.json'
            with open(filename, 'r') as f:
                labels = json.loads(f.read())
        except:
            labels = {}

        datautil.map(labels, (change_request_issue_key,), label)

        with open(filename, 'w') as f:
            f.write(json.dumps(labels, indent=4, sort_keys=True))

    def add(self, issues):
        change_request_issue_map = []
        for issue in issues:
            if 'change' in datautil.map_get(issue, ('fields', 'issuetype', 'name'), ''):
                change_request_issue_map += issue
            self.issue_map.collection_issues.update_one({'self': issue['self'], 'issue_key': issue['key']}, {'$set': issue}, upsert=True)

        self.generate_change_request_meta(change_request_issue_map)

    def generate_change_request_meta(self, change_request_issue_map):
        for change_request_issue in change_request_issue_map:
            change_request_project_key = change_request_issue['fields']['project']['key']
            change_request_issue_key = change_request_issue['key']
            change_request_linked_issues = jsonquery.query(change_request_issue, 'fields.issuelinks.inwardIssue.^key')
            change_request_release_date = issues.Issues.parseDateTime(change_request_issue['fields']['created'])
            change_request_last_updated = None

            for issue in self.issue_map.getIssuesByKeys(change_request_linked_issues):
                issue_key = issue['key']

                issue_creation_date = issues.Issues.parseDateTime(issue['fields']['created'])
                issue_updated_date = issues.Issues.parseDateTime(issue['fields']['updated'])

                if change_request_last_updated is None:
                    if not issue_updated_date is None:
                        change_request_last_updated = issue_updated_date
                    elif not issue_creation_date is None:
                        change_request_last_updated = issue_creation_date
                else:
                    if not issue_updated_date is None and issue_updated_date > change_request_last_updated:
                        change_request_last_updated = issue_updated_date
                    elif not issue_creation_date is None and issue_updated_date > change_request_last_updated:
                        change_request_last_updated = issue_creation_date

            self.collection_change_request_meta_map.update_one(
                {'issue_key': issue['key']}, {'$set':
                    {
                        'issue_key': issue['key'],
                        'project_key': change_request_project_key,
                        'fixVersion_name': None,
                        'last_updated': change_request_last_updated,
                        'release_date': change_request_release_date,
                        'linked_issues': change_request_linked_issues,
                        'affected_issues': [],
                        'last_predicted_date': None,
                        'last_predictions': {}
                    }
                }, upsert=True)

    def iterate_projects_fixVersions_issue_map(self, splits=1, split_index=0):
        cursor = self.collection_projects_fixVersions_issue_map.find({})
        count = cursor.count()
        split_size = int(count / splits + 0.5)
        cursor = cursor.skip(split_index * split_size).limit(split_size)
        try:
            for result in cursor:
                yield result
        except:
            pass

    def iterate_projects_affectsVersions_issue_map(self, project_key, version_name):
        for result in self.collection_projects_affectsVersions_issue_map.find(
                {
                    '_id': {
                        'project_key': project_key,
                        'affectsVersion_name': version_name
                    }
                },
                {'_id': 0}
            ):

            yield result['issue_keys']

    def get_project_versions(self, project_key):
        return datautil.map_get(self.collection_projects_versions_map.find_one(
            {
                '_id.project_key': project_key
            }), ('version_names',), [])

    def generate(self):
        universe_name = self.issue_map.getUniverseName()
        scripts = [
            '''
from pymongo import MongoClient

client = MongoClient()
db = client['data-explorer']

collection_issues = db['issues_{universe_name}']

collection_issues.aggregate(
    [
        {{'$unwind': '$fields.fixVersions'}},
        {{'$group':
            {{
                '_id':{{
                    'project_key': '$fields.project.key',
                    'fixVersion_name': '$fields.fixVersions.name',
                    'issue_key': '$key'
                }}
            }}
        }},
        {{
            '$group': {{
                '_id': {{
                    'project_key': '$_id.project_key',
                    'fixVersion_name': '$_id.fixVersion_name'
                }},
                'issue_keys': {{
                    '$addToSet': '$_id.issue_key'
                }}
            }}
        }},
        {{
            '$out': '{universe_name}_projects_fixVersions_issue_map'
        }}
    ],
    allowDiskUse=True
)
'''.format(universe_name=universe_name),
            '''
from pymongo import MongoClient

client = MongoClient()
db = client['data-explorer']

collection_issues = db['issues_{universe_name}']

collection_issues.aggregate(
    [
        {{'$unwind': '$fields.versions'}},
        {{'$group':
            {{
                '_id':{{
                    'project_key': '$fields.project.key',
                    'affectsVersion_name': '$fields.versions.name',
                    'issue_key': '$key'
                }}
            }}
        }},
        {{
            '$group': {{
                '_id': {{
                    'project_key': '$_id.project_key',
                    'affectsVersion_name': '$_id.affectsVersion_name'
                }},
                'issue_keys': {{
                    '$addToSet': '$_id.issue_key'
                }}
            }}
        }},
        {{
            '$out': '{universe_name}_projects_affectsVersions_issue_map'
        }}
    ],
    allowDiskUse=True)
'''.format(universe_name=universe_name),
            '''
from pymongo import MongoClient

client = MongoClient()
db = client['data-explorer']

collection_issues = db['issues_{universe_name}']
collection_projects_versions_release_date_map = db['{universe_name}_projects_versions_release_date_map']

collection_issues.aggregate(
    [
        {{
            '$project': {{
                'fields.project.key': 1,
                'versions': {{
                    '$function': {{
                        'body': """function(L,R){{
                            let A = [];
                            if (L !== undefined && L !== null) {{
                                for (let x of L) A.push(x);
                            }}
                            if (R !== undefined && R !== null) {{
                                for (let x of R) A.push(x);
                            }}

                            return A;
                        }}""",
                        'args': [
                            '$fields.fixVersions',
                            '$fields.versions'
                        ],
                        'lang': 'js'
                    }}
                }}
            }}
        }},
        {{
            '$unwind': '$versions'
        }},
        {{
            '$group':{{
                '_id':{{
                    'project_key': '$fields.project.key',
                    'version_name': '$versions.name'
                }},
                'release_date': {{
                    '$addToSet': '$versions.releaseDate'
                }}
            }}
        }},
        {{
            '$out': '{universe_name}_projects_versions_release_date_map'
        }}
    ],
    allowDiskUse=True
)

collection_projects_versions_release_date_map.aggregate(
    [
        {{
            '$group': {{
                '_id': '$_id.project_key',
                'version_names': {{
                    '$addToSet': '$_id.version_name'
                }}
            }}
        }},
        {{
            '$out': '{universe_name}_projects_versions_map'
        }}
    ],
    allowDiskUse=True
)
'''.format( universe_name=universe_name),
            '''
from pymongo import MongoClient

client = MongoClient()
db = client['data-explorer']

collection_issues = db['issues_{universe_name}']

collection_issues.aggregate(
    [
        {{
            '$project': {{
                '_id': 0,
                'priority_name': '$fields.priority.name',
                'status_name': '$fields.status.name',
                'resolution_name': '$fields.resolution.name',
                'issuetype_name': '$fields.issuetype.name'
            }}
        }},
        {{
            '$group': {{
                '_id':{{}},
                'priority_name': {{
                    '$addToSet': '$priority_name'
                }},
                'status_name': {{
                    '$addToSet': '$status_name'
                }},
                'resolution_name': {{
                    '$addToSet': '$resolution_name'
                }},
                'issuetype_name': {{
                    '$addToSet': '$issuetype_name'
                }}
            }}
        }},
        {{
            '$out': '{universe_name}_feature_names'
        }}
    ],
    allowDiskUse=True
)
'''.format( universe_name=universe_name)
        ]
        print(wormhole.add(scripts))
        print(wormhole.run())

        from multiprocessing import cpu_count
        processes = cpu_count() * cpu_count()

        # generate fake change requests
        scripts = []

        for i in range(processes):
            scripts += ['''
import issues
import change_requests
import jsonquery
import datautil
import datetime

issue_map = issues.Issues('{universe_name}')
change_request = change_requests.ChangeRequest(issue_map)

i = 100000 * {split_index}
for result in change_request.iterate_projects_fixVersions_issue_map({split_count}, {split_index}):
    project_key = result['_id']['project_key']
    version_name = result['_id']['fixVersion_name']
    issue_keys = result['issue_keys']

    change_request_issue_key = project_key + '_gcr_-' + str(i)

    i += 1

    last_updated = None

    change_request_version = change_request.collection_projects_versions_release_date_map.find_one(
        {{
            '_id.project_key': project_key,
            '_id.version_name': version_name
        }}
    )
    target_release_date = None

    debug_use_change_release_date = False
    if debug_use_change_release_date:
        if len(change_request_version['release_date']) > 0:
            target_release_date = issues.Issues.parseDateTimeSimple(change_request_version['release_date'][0])
        else:
            target_release_date = datetime.datetime.now(tz=datetime.timezone.utc)
    else:
        target_release_date = datetime.datetime.now(tz=datetime.timezone.utc)

    target_release_date = target_release_date.replace(tzinfo=None)

    fixed_issues = []
    for issue in change_request.issue_map.getIssuesByKeys(issue_keys):
        issue_key = issue['key']

        extracted_features = change_request.issue_map.getExtractedFeatures(issue, change_request.get_project_versions(project_key), target_release_date)
        if extracted_features is None:
            continue

        issue_creation_date = extracted_features['created_date']
        issue_updated_date = extracted_features['updated_date']

        if last_updated is None:
            if not issue_updated_date is None:
                last_updated = issue_updated_date
            elif not issue_creation_date is None:
                last_updated = issue_creation_date
        else:
            if not issue_updated_date is None and issue_updated_date > last_updated:
                last_updated = issue_updated_date
            elif not issue_creation_date is None and issue_creation_date > last_updated:
                last_updated = issue_creation_date

        resolution = extracted_features['resolution_name']
        status = extracted_features['status_name']
        issuetype = extracted_features['issuetype_name']

        is_chronological = issue_creation_date <= target_release_date

        if is_chronological:
            fixed_issues += [issue_key]

    if len(fixed_issues) == 0:
        continue

    related_affected_issues = []
    for issue_keys in change_request.iterate_projects_affectsVersions_issue_map(project_key, version_name):
        for issue in change_request.issue_map.getIssuesByKeys(issue_keys):
            issue_key = issue['key']

            issue_creation_date = issues.Issues.parseDateTime(issue['fields']['created'])

            resolution = jsonquery.query(issue, 'fields.resolution.^name')
            status = jsonquery.query(issue, 'fields.status.^name')
            issuetype = jsonquery.query(issue, 'fields.issuetype.^name')

            is_chronological = not debug_use_change_release_date or issue_creation_date >= target_release_date

            if is_chronological:
                related_affected_issues += [issue_key]

    if len(change_request_version['release_date']) > 0:
        change_request_release_date = issues.Issues.parseDateTimeSimple(change_request_version['release_date'][0])
    else:
        change_request_release_date = last_updated

    change_request.collection_change_request_meta_map.update_one(
        {{'issue_key': change_request_issue_key}}, {{'$set':
            {{
                'issue_key': change_request_issue_key,
                'project_key': project_key,
                'fixVersion_name': version_name,
                'last_updated': last_updated,
                'release_date': change_request_release_date,
                'linked_issues': fixed_issues,
                'affected_issues': related_affected_issues,
                'last_predicted_date': None,
                'last_predictions': {{}}
            }}
        }}, upsert=True
    )
    '''.format(
                universe_name=universe_name,
                split_index = i,
                split_count = processes
            )]

        print(wormhole.add(scripts))
        print(wormhole.run())

    def getExtractedFeaturesMeta(self=None):
        import statistics

        out = {
            'feature_values_map': self.collection_feature_names.find_one({}, {'_id': 0}),
            'aggregators': {
                'sum': sum,
                'max': max,
                'mean': statistics.mean,
                'stdev': statistics.stdev,
                'median': statistics.median,
                'variance': statistics.variance
            },
            'aggregated_features': [
                'number_of_blocked_by_issues',
                'number_of_blocks_issues',
                'number_of_comments',
                'discussion_time',
                'delays'
            ]
        }

        extracted_features_meta = issues.Issues.getExtractedFeaturesMeta()

        for change in extracted_features_meta['change_map_names']:
            out['aggregated_features'] += ['number_of_changes_to_%s' % change]

        for feature_key, feature_values in out['feature_values_map'].items():
            for value in feature_values:
                out['aggregated_features'] += ['number_of_%s_%s' % (str(feature_key), value.replace('.', ''))]

        return out

    def getExtractedFeatures(self, change_request_issue_key, target_date):
        target_date = target_date.replace(tzinfo=None)

        extracted_issues_features_meta = issues.Issues.getExtractedFeaturesMeta()
        extracted_features_meta = self.getExtractedFeaturesMeta()

        out = self.issue_map.collection_features.find_one({'issue_key': change_request_issue_key, 'target_date': target_date})

        if not out is None:
            out['Meta'] = extracted_features_meta

            return out

        out = {}

        out['issue_key'] = change_request_issue_key
        out['target_date'] = target_date

        change_request_meta = self.collection_change_request_meta_map.find_one({'issue_key': change_request_issue_key})

        project_key = change_request_meta['project_key']
        version_name = change_request_meta['fixVersion_name']

        out['number_of_issues'] = len(change_request_meta['linked_issues'])

        out['number_of_comments'] = 0

        out['number_of_blocked_by_issues'] = 0
        out['number_of_blocks_issues'] = 0

        out['participants'] = {}
        out['team_members'] = {}
        out['reporters'] = {}

        out['number_of_participants'] = 0
        out['number_of_team_members'] = 0
        out['number_of_reporters'] = 0

        out['elapsed_time'] = datetime.timedelta()
        out['earliest_date'] = None

        for feature in extracted_features_meta['aggregated_features']:
            out[feature] = {
                'data': []
            }

        out['release_date'] = change_request_meta['release_date'].replace(tzinfo=None)

        for issue in self.issue_map.getIssuesByKeys(change_request_meta['linked_issues']):
            version_names = self.get_project_versions(project_key)
            extracted_features = self.issue_map.getExtractedFeatures(issue, version_names, target_date)

            if not extracted_features is None:
                out['discussion_time']['data'] += [extracted_features['discussion_time']]
                out['number_of_comments']['data'] += [extracted_features['number_of_comments']]

                out['number_of_blocked_by_issues']['data'] += [extracted_features['number_of_blocked_by_issues']]
                out['number_of_blocks_issues']['data'] += [extracted_features['number_of_blocks_issues']]

                for change in extracted_issues_features_meta['change_map_names']:
                    out['number_of_changes_to_%s' % change]['data'] += [len(extracted_features['changes'][change])]

                for feature_key, feature_values in extracted_features_meta['feature_values_map'].items():
                    for value in feature_values:
                        out['number_of_%s_%s' % (str(feature_key), value.replace('.', ''))]['data'] += [len(jsonquery.query(issue, 'fields.%s:%s' % (feature_key.replace('_', '.'), value)))]

                if extracted_features['delays'] >= 0:
                    out['delays']['data'] += [extracted_features['delays']]

                if out['earliest_date'] is None or out['earliest_date'] > extracted_features['created_date']:
                    out['earliest_date'] = extracted_features['created_date']

                # Bug: Sometimes key/accountId can be None but displayName is available.
                if not extracted_features['assignee_key'] is None:
                    out['team_members'][extracted_features['assignee_key']] = extracted_features['assignee_displayName']
                    out['participants'][extracted_features['assignee_key']] = extracted_features['assignee_displayName']

                if not extracted_features['reporter_key'] is None:
                    out['reporters'][extracted_features['reporter_key']] = extracted_features['reporter_displayName']
                    out['participants'][extracted_features['reporter_key']] = extracted_features['reporter_displayName']

                for comment in extracted_features['comments']:
                    if not comment['author_accountId'] is None:
                        out['participants'][comment['author_accountId']] = comment['author_displayName']

        out['number_of_participants'] = len(out['participants'].keys())
        out['number_of_team_members'] = len(out['team_members'].keys())
        out['number_of_reporters'] = len(out['reporters'].keys())

        if not out['earliest_date'] is None and not out['release_date'] is None:
            out['elapsed_time'] = out['release_date'] - out['earliest_date']

        for feature in extracted_features_meta['aggregated_features']:
            L = len(out[feature]['data'])

            for aggregator_name, aggregator in extracted_features_meta['aggregators'].items():
                out[feature][aggregator_name] = 0

                if L > 0:
                    try:
                        out[feature][aggregator_name] = aggregator(out[feature]['data'])
                    except:
                        out[feature][aggregator_name] = out[feature]['data'][0]

        out['elapsed_time'] = out['elapsed_time'].total_seconds()

        self.issue_map.collection_features.update_one({
            'issue_key': change_request_issue_key,
            'target_date': target_date
            }, {'$set': out}, upsert=True)

        out['Meta'] = extracted_features_meta

        return out
