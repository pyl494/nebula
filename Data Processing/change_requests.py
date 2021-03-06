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

        client = MongoClient(tz_aware=True)
        db = client['data-explorer']
        self.collection_projects_fixVersions_issue_map = db[self.issue_map.get_universe_name() + '_projects_fixVersions_issue_map']
        self.collection_projects_affectsVersions_issue_map = db[self.issue_map.get_universe_name() + '_projects_affectsVersions_issue_map']
        self.collection_projects_versions_release_date_map = db[self.issue_map.get_universe_name() + '_projects_versions_release_date_map']
        self.collection_projects_versions_map = db[self.issue_map.get_universe_name() + '_projects_versions_map']
        self.collection_feature_names = db[self.issue_map.get_universe_name() + '_feature_names']
        self.collection_change_request_meta_map = db[self.issue_map.get_universe_name() + '_change_request_meta_map']

        try:
            self.collection_change_request_meta_map.create_index([('issue_key', 1)], unique=True)
        except Exception as e:
            debug.exception_print(e)
            print('failed to set index on features')

        self.machine_learning_model = MachineLearningModel(self)
        self.label_thresholds = [{'label': 'low', 'threshold': 10}, {'label': 'medium', 'threshold': 25}, {'label': 'high', 'threshold': 40}]
        self.label_threshold_metric = None
        self.label_buckets = None
        self.label_data = None
        self.label_splits = None

    def get_change_request_meta(self, change_request_issue_key):
        return self.collection_change_request_meta_map.find_one({'issue_key': change_request_issue_key})

    def iterate_change_request_meta_map(self, sorted=False, start=None, limit=None, splits = 1, split_index = 0):
        cursor = None

        commands = []

        if sorted:
            commands += [{'$sort': {'project_key': 1, 'fixVersion_name': 1}}]

        if not start is None:
            commands += [{'$skip': start}]

        if not limit is None:
            commands += [{'$limit': limit}]

        cursor = self.collection_change_request_meta_map.aggregate(commands)

        try:
            for result in cursor:
                yield result
        except:
            pass

    def get_issue_map(self):
        return self.issue_map

    def get_machine_learning_model(self):
        return self.machine_learning_model

    def get_post_change_request_interactivity(self, change_request_meta):
        acount = len(change_request_meta['affected_issues'])

        fcomment_count = 0
        fvote_count = 0
        for issue in self.issue_map.get_issues_by_keys(change_request_meta['linked_issues']):
            fvote_count += int(issue['fields']['votes']['votes'])
            for comment in issue['fields']['comment']['comments']:
                if issues.Issues.parse_date_time(comment['created']) >= change_request_meta['release_date']:
                    fcomment_count += 1

        acomment_count = 0
        avote_count = 0
        abug_count = 0
        for issue in self.issue_map.get_issues_by_keys(change_request_meta['affected_issues']):
            acomment_count += len(issue['fields']['comment']['comments'])
            avote_count += int(issue['fields']['votes']['votes'])
            abug_count += int(1 if issue['fields']['issuetype']['name'] == 'Bug' else 0)

        interactivity = fcomment_count + fvote_count + acomment_count + avote_count + acount

        return {
            'interactivity': interactivity,
            'fixVersion_vote_count': fvote_count,
            'fixVersion_post_comment_count': fcomment_count,
            'affectsVersion_issue_count': acount,
            'affectsVersion_vote_count': avote_count,
            'affectsVersion_comment_count': acomment_count,
            'affectsVersion_bugs_count': abug_count
        }

    def get_automatic_risk_label(self, change_request_meta):
        interactivity = self.get_post_change_request_interactivity(change_request_meta)['interactivity']

        thresholds = self.label_thresholds[1:]
        thresholds.reverse()

        for threshold in thresholds:
            if interactivity >= threshold['threshold']:
                return threshold['label']

        return self.label_thresholds[0]['label']

    def calc_label_thresholds(self, split_proportions = [0.0, 0.85, 0.95, 1.0], split_labels = ['low', 'medium', 'high'], threshold_metric = 'interactivity'):
        import numpy as np
        from sklearn.feature_extraction import DictVectorizer

        d = []
        DV = DictVectorizer(sparse=False)
        for change_request_meta in self.iterate_change_request_meta_map():
            i = self.get_post_change_request_interactivity(change_request_meta)
            d += [i]

        d = DV.fit_transform(d)
        self.label_vocabulary_index = datautil.vocabulary_index(DV.vocabulary_)
        self.label_data = d

        splits = [[] for x in range(len(split_proportions) - 1)]

        counts = [np.unique(d[:,i], return_counts=True) for i in range(d.shape[1])]

        N = [0 for x in range(d.shape[1])]
        N_1 = N[:]

        for p in range(len(split_proportions) - 1):
            pdiff = split_proportions[p + 1] - split_proportions[p]
            a = []
            for i in range(d.shape[1]):
                if N[i] >= counts[i][1].shape[0]:
                    a += [[]]
                    continue

                sum_  = counts[i][1][N[i]]
                while sum_ / d.shape[0] < pdiff and N_1[i] < counts[i][1].shape[0] - 1:
                    N_1[i] += 1
                    sum_ += counts[i][1][N_1[i]]

                d_ = d[ d[:, i].argsort(), i ]
                d_ = d_[ d_ >= counts[i][0][N[i]] ]
                d_ = d_[ d_ <= counts[i][0][N_1[i]] ]
                a += [d_]

                N_1[i] += 1
                N[i] = N_1[i]

            splits[p] += [a]

        splits = np.array(splits)
        self.label_split = splits

        self.label_buckets = [dict([(
                self.label_vocabulary_index[y[0]], {
                    'mean': y[1].mean(),
                    'min': y[1].min()
                }
            ) for y in enumerate(x[1][0])]) for x in enumerate(splits)]

        self.label_threshold_metric = threshold_metric
        self.label_thresholds = [{'label': split_labels[x[0]], 'threshold': x[1][threshold_metric]['min']} for x in enumerate(self.label_buckets)]

        return {
            'vocabulary_index': self.label_vocabulary_index,
            'data': self.label_data,
            'splits': self.label_splits,
            'buckets': self.label_buckets,
            'thresholds': self.label_thresholds,
            'threshold_metric': self.label_threshold_metric,
        }

    def get_manual_risk_label(self, change_request_issue_key):
        try:
            project_key = self.get_change_request_meta(change_request_issue_key)['project_key']

            filename = '../Data Labels/' + self.issue_map.get_universe_name() + '_' + project_key + '.json'
            with open(filename, 'r') as f:
                labels = json.loads(f.read())

            return labels[change_request_issue_key]

        except Exception as e:
            return None

    def set_manual_risk_label(self, change_request_issue_key, label):
        try:
            project_key = self.get_change_request_meta(change_request_issue_key)['project_key']

            filename = '../Data Labels/' + self.issue_map.get_universe_name() + '_' + project_key + '.json'
            with open(filename, 'r') as f:
                labels = json.loads(f.read())
        except:
            labels = {}

        datautil.map(labels, (change_request_issue_key,), label)

        with open(filename, 'w') as f:
            f.write(json.dumps(labels, indent=4, sort_keys=True))

    def add(self, issues):
        issue_keys = []
        change_request_issue_map = []
        for issue in issues:
            issue_keys += issue['key']
            if 'change' in datautil.map_get(issue, ('fields', 'issuetype', 'name'), '').lower():
                change_request_issue_map += [issue]
            self.issue_map.collection_issues.update_one({'self': issue['self'], 'issue_key': issue['key']}, {'$set': issue}, upsert=True)

        self.generate_change_request_meta(change_request_issue_map)

        cursor = self.issue_map.collection_issues.aggregate(
        [
            {   '$match': {
                    'key': {'$in': issue_keys}
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'priority_name': '$fields.priority.name',
                    'status_name': '$fields.status.name',
                    'resolution_name': '$fields.resolution.name',
                    'issuetype_name': '$fields.issuetype.name'
                }
            },
            {
                '$group': {
                    '_id':{},
                    'priority_name': {
                        '$addToSet': '$priority_name'
                    },
                    'status_name': {
                        '$addToSet': '$status_name'
                    },
                    'resolution_name': {
                        '$addToSet': '$resolution_name'
                    },
                    'issuetype_name': {
                        '$addToSet': '$issuetype_name'
                    }
                }
            },
        ],
        allowDiskUse=True)

        feature_names_map = datautil.default(self.collection_feature_names.find_one({}, {'_id': 0}), {})

        for item in cursor:
            for key, value in item.items():
                feature_names_map[key].add(value)

        if len(feature_names_map) > 0:
            self.collection_feature_names.update_one({}, feature_names_map)

    def generate_change_request_meta(self, change_request_issue_map):
        for change_request_issue in change_request_issue_map:
            change_request_project_key = change_request_issue['fields']['project']['key']
            change_request_issue_key = change_request_issue['key']
            change_request_linked_issues = jsonquery.query(change_request_issue, 'fields.issuelinks.inwardIssue.^key')
            change_request_release_date = issues.Issues.parse_date_time(change_request_issue['fields']['created'])
            change_request_last_updated = datetime.datetime.now(tz=datetime.timezone.utc)

            for issue in self.issue_map.get_issues_by_keys(change_request_linked_issues):
                issue_key = issue['key']

                issue_creation_date = issues.Issues.parse_date_time(issue['fields']['created'])
                issue_updated_date = issues.Issues.parse_date_time(issue['fields']['updated'])

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

            test = self.get_change_request_meta(change_request_issue)
            if test is None or not 'last_predicted_date' in test or not 'last_predictions' in test:
                self.collection_change_request_meta_map.update_one(
                    {'issue_key': change_request_issue_key}, {'$set':
                        {
                            'issue_key': change_request_issue_key,
                            'last_predicted_date': None,
                            'last_predictions': {}
                        }
                    }, upsert=True)

            self.collection_change_request_meta_map.update_one(
                {'issue_key': change_request_issue_key}, {'$set':
                    {
                        'issue_key': change_request_issue_key,
                        'project_key': change_request_project_key,
                        'fixVersion_name': None,
                        'last_updated': change_request_last_updated,
                        'release_date': change_request_last_updated, #change_request_release_date,
                        'linked_issues': change_request_linked_issues,
                        'affected_issues': []
                    }
                }, upsert=True)

    def update_change_request_predictions(self, change_request_issue_key, predictions):
        self.collection_change_request_meta_map.update_one(
                {'issue_key': change_request_issue_key}, {'$set':
                    {
                        'last_predicted_date': datetime.datetime.now(tz=datetime.timezone.utc),
                        'last_predictions': predictions
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
        universe_name = self.issue_map.get_universe_name()
        scripts = [
            '''
def work(queue):
    from pymongo import MongoClient

    client = MongoClient(tz_aware=True)
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

    return True
'''.format(universe_name=universe_name),
            '''
def work(queue):
    from pymongo import MongoClient

    client = MongoClient(tz_aware=True)
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

        return True
'''.format(universe_name=universe_name),
            '''
def work(queue):
    from pymongo import MongoClient

    client = MongoClient(tz_aware=True)
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

    return True
'''.format( universe_name=universe_name),
            '''
def work(queue):
    from pymongo import MongoClient

    client = MongoClient(tz_aware=True)
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

    return True
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
def work(queue):
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
                target_release_date = issues.Issues.parse_date_time(change_request_version['release_date'][0])
            else:
                target_release_date = datetime.datetime.now(tz=datetime.timezone.utc)
        else:
            target_release_date = datetime.datetime.now(tz=datetime.timezone.utc)

        fixed_issues = []
        for issue in change_request.issue_map.get_issues_by_keys(issue_keys):
            issue_key = issue['key']

            extracted_features = change_request.issue_map.get_extracted_features(issue, change_request.get_project_versions(project_key), target_release_date)
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
            for issue in change_request.issue_map.get_issues_by_keys(issue_keys):
                issue_key = issue['key']

                issue_creation_date = issues.Issues.parse_date_time(issue['fields']['created'])

                resolution = jsonquery.query(issue, 'fields.resolution.^name')
                status = jsonquery.query(issue, 'fields.status.^name')
                issuetype = jsonquery.query(issue, 'fields.issuetype.^name')

                is_chronological = not debug_use_change_release_date or issue_creation_date >= target_release_date

                if is_chronological:
                    related_affected_issues += [issue_key]

        if len(change_request_version['release_date']) > 0:
            change_request_release_date = issues.Issues.parse_date_time(change_request_version['release_date'][0])
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

    return True
    '''.format(
                universe_name=universe_name,
                split_index = i,
                split_count = processes
            )]

        print(wormhole.add(scripts))
        print(wormhole.run())

    def get_extracted_features_meta(self=None):
        import statistics

        out = {
            'feature_values_map': datautil.default(self.collection_feature_names.find_one({}, {'_id': 0}), {}),
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

        extracted_features_meta = issues.Issues.get_extracted_features_meta()

        for change in extracted_features_meta['change_map_names']:
            out['aggregated_features'] += ['number_of_changes_to_%s' % change]

        for feature_key, feature_values in out['feature_values_map'].items():
            for value in feature_values:
                out['aggregated_features'] += ['number_of_%s_%s' % (str(feature_key), value.replace('.', ''))]

        return out

    def get_extracted_features(self, change_request_issue_key, target_date):
        extracted_issues_features_meta = issues.Issues.get_extracted_features_meta()
        extracted_features_meta = self.get_extracted_features_meta()

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

        out['release_date'] = change_request_meta['release_date']

        for issue in self.issue_map.get_issues_by_keys(change_request_meta['linked_issues']):
            version_names = self.get_project_versions(project_key)
            extracted_features = self.issue_map.get_extracted_features(issue, version_names, target_date)

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
