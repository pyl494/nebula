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
from issues import Issues

class JSONDumper(json.JSONEncoder):
     def default(self, obj):
         return str(obj)

class ChangeRequest:
    features_values_map = {
        #feature: set(values)
    }

    def __init__(self, issue_map):
        self.issue_map = issue_map

        self.projects_fixVersions_issue_map = {
            # PROJECT: {fixVersion: [issue_keys]}
        }

        self.projects_affectsVersions_issue_map = {
            # PROJECT : {affectsVersion: [issue_keys]}
        }

        self.change_request_meta_map = {
            #issue_key: {
            #    project_key: project_key,
            #    release_date: Date(fixVersion.releaseDate),
            #    last_updated: Date(updated),
            #    fixVersion: fixVersion.name,
            #    linked_issues: [issue_keys],
            #    affected_issues: [issue_keys],
            #    last_predicted_date: Date(),
            #    last_predictions = {}
            # }
        }

        self.projects_version_info_map = {
            # PROJECT: {fixVersion: {data}}
        }

    def getChangeRequestMetaMap(self):
        return self.change_request_meta_map

    def getProjectsFixVersionIssueMap(self):
        return self.projects_fixVersions_issue_map
    
    def getProjectsAffectsVersionIssueMap(self):
        return self.projects_affectsVersions_issue_map

    def getProjectsVersionInfoMap(self):
        return self.projects_version_info_map

    def getIssueMap(self):
        return self.issue_map

    def getAutomaticRiskLabel(self, change_request_issue_key):
        change_request_meta = self.change_request_meta_map[change_request_issue_key]
        acount = len(change_request_meta['affected_issues'])

        fcomment_count = 0
        fvote_count = 0
        for issue_key in change_request_meta['linked_issues']:
            issue = self.issue_map.getIssueByKey(issue_key)
            fvote_count += int(issue['fields']['votes']['votes'])
            for comment in issue['fields']['comment']['comments']:
                if Issues.parseDateTime(comment['created']) >= change_request_meta['release_date']:
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
            project_key = self.change_request_meta_map[change_request_issue_key]['project_key']

            filename = '../Data Labels/' + self.issue_map.getUniverseName() + '_' + project_key + '.json'
            with open(filename, 'r') as f:
                labels = json.loads(f.read())
            
            return labels[change_request_issue_key]

        except Exception as e:
            return None

    def setManualRiskLabel(self, change_request_issue_key, label):
        try:
            project_key = self.change_request_meta_map[change_request_issue_key]['project_key']

            filename = '../Data Labels/' + self.issue_map.getUniverseName() + '_' + project_key + '.json'
            with open(filename, 'r') as f:
                labels = json.loads(f.read())
        except:
            labels = {}
            
        datautil.map(labels, (change_request_issue_key,), label)

        with open(filename, 'w') as f:
            f.write(json.dumps(labels, indent=4, sort_keys=True))
        
    def generate(self):
        issues = self.issue_map.getIssuesByQuery({'fields.fixVersions.name': {'$exists': True}})

        for issue in issues:
            project_key = issue['fields']['project']['key']
            issue_key = issue['key']
            versions = issue['fields']['fixVersions']
            for version in versions:
                version_name = version['name']
                datautil.map_set(self.projects_fixVersions_issue_map, (project_key, version_name), issue_key)
                datautil.map(self.projects_version_info_map, (project_key, version_name), version)
            
            for f_key, f_value in issue['fields'].items():
                if f_key in ['priority', 'status', 'resolution', 'issuetype']:
                    if isinstance(f_value, dict):
                        if 'name' in f_value:
                            datautil.map_set(self.features_values_map, ('%s_name' % f_key,), f_value['name'])
                    elif not isinstance(f_value, list):
                        datautil.map_set(self.features_values_map, (f_key,), f_value)

        issues = self.issue_map.getIssuesByQuery({'fields.versions.name': {'$exists': True}})

        for issue in issues:
            project_key = issue['fields']['project']['key']
            issue_key = issue['key']
            versions = issue['fields']['versions']
            for version in versions:
                version_name = version['name']
                datautil.map_set(self.projects_affectsVersions_issue_map, (project_key, version_name), issue_key)
                datautil.map(self.projects_version_info_map, (project_key, version_name), version)

        # Load real change requests
        change_request_issue_map = self.issue_map.getIssuesByQuery({'fields.issuetype.name': '/.*change.*/i'})
        change_request_issue_keys = []

        for change_request_issue in change_request_issue_map:
            change_request_project_key = change_request_issue['fields']['project']['key']
            change_request_issue_key = change_request_issue['key']
            change_request_issue_keys += [change_request_issue_key]
            change_request_linked_issues = jsonquery.query(change_request_issue, 'fields.issuelinks.inwardIssue.^key')
            change_request_release_date = Issues.parseDateTime(change_request_issue['fields']['created'])
            change_request_last_updated = None

            for issue in self.issue_map.getIssuesByKeys(change_request_linked_issues):
                issue_key = issue['key']
                change_request_issue_keys += [issue_key]

                issue_creation_date = Issues.parseDateTime(issue['fields']['created'])
                issue_updated_date = Issues.parseDateTime(issue['fields']['updated'])

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
            
            self.change_request_meta_map[change_request_issue_key] = {
                'project_key': change_request_project_key,
                'fixVersion': None,
                'last_updated': change_request_last_updated,
                'release_date': change_request_release_date,
                'linked_issues': change_request_linked_issues,
                'affected_issues': [],
                'last_predicted_date': None,
                'last_predictions': {}
            }

        # generate fake change requests
        for project_key, fixVersions_issue_map in self.projects_fixVersions_issue_map.items():
            
            i = 0
            for version_name, issue_map in fixVersions_issue_map.items():
                change_request_issue_key = project_key + '_gcr_-' + str(i)
                
                if change_request_issue_key in change_request_issue_keys:
                    continue

                i += 1

                last_updated = None

                change_request_version = self.projects_version_info_map[project_key][version_name]
                change_request_release_date = None

                debug_use_change_release_date = False
                if debug_use_change_release_date:
                    if 'releaseDate' in change_request_version:
                        change_request_release_date = Issues.parseDateTimeSimple(change_request_version['releaseDate'])
                    else:
                        continue
                else:
                    change_request_release_date = datetime.datetime.now(tz=datetime.timezone.utc)

                fixed_issues = []
                for issue in self.issue_map.getIssuesByKeys(list(issue_map)):
                    issue_key = issue['key']

                    if issue_key in change_request_issue_keys:
                        continue
                    
                    extracted_features = self.issue_map.getExtractedFeatures(issue, self.projects_version_info_map[project_key], change_request_release_date)
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
                    
                    is_fixed = resolution == 'Fixed'
                    is_chronological = issue_creation_date <= change_request_release_date
                    is_closed = status == 'Closed'
                    is_bug = issuetype == 'Bug'

                    #dates = []
                    #for version in issue['fields']['fixVersions']:
                    #    if 'releaseDate' in version:
                    #        version_date = Issues.parseDateTimeSimple(version['releaseDate'])
                    #        dates += [version_date]
                    
                    #is_earliest_version = min(dates) == change_request_release_date

                    if is_fixed and is_chronological and is_closed:# and is_earliest_version and is_bug:
                        fixed_issues += [issue_key]
                        #change_request_issue_keys += [issue_key]

                if len(fixed_issues) == 0:
                    continue

                affected_issues = datautil.map_get(self.projects_affectsVersions_issue_map, (project_key, version_name))
                if affected_issues is None:
                    affected_issues = []
                
                related_affected_issues = []
                for issue_key in affected_issues:
                    
                    if issue_key in change_request_issue_keys:
                        continue

                    issue = self.issue_map.getIssueByKey(issue_key)
                    issue_creation_date = Issues.parseDateTime(issue['fields']['created'])
                    
                    resolution = jsonquery.query(issue, 'fields.resolution.^name')
                    status = jsonquery.query(issue, 'fields.status.^name')
                    issuetype = jsonquery.query(issue, 'fields.issuetype.^name')
                    
                    is_chronological = not debug_use_change_release_date or issue_creation_date >= change_request_release_date
                    is_fixed = len(resolution) == 1 and resolution[0] == 'Fixed'
                    is_bug = len(issuetype) == 1 and issuetype[0] == 'Bug'

                    #dates = []
                    #for version in issue['fields']['versions']:
                    #    if 'releaseDate' in version:
                    #        version_date = Issues.parseDateTimeSimple(version['releaseDate'])
                    #        dates += [version_date]
                    
                    #is_earliest_version = True#len(dates) > 0 and (min(dates) == change_request_release_date)

                    if is_chronological and is_bug and is_fixed:#and is_earliest_version
                        related_affected_issues += [issue_key]

                self.change_request_meta_map[change_request_issue_key] = {
                    'project_key': project_key,
                    'fixVersion': version_name,
                    'last_updated': last_updated,
                    'release_date': change_request_release_date,
                    'linked_issues': fixed_issues,
                    'affected_issues': related_affected_issues,
                    'last_predicted_date': None,
                    'last_predictions': {}
                }

    def getExtractedFeaturesMeta(self=None):
        import statistics

        out = {
            'features_values_map': self.features_values_map,
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

        extracted_features_meta = Issues.getExtractedFeaturesMeta()

        for change in extracted_features_meta['change_map_names']:
            out['aggregated_features'] += ['number_of_changes_to_%s' % change]

        for feature_key, feature_values in self.features_values_map.items():
            for value in feature_values:
                out['aggregated_features'] += ['number_of_%s_%s' % (str(feature_key), value)]

        return out

    def getExtractedFeatures(self, change_request_issue_key, date):
        out = {}
        
        extracted_features_meta = self.getExtractedFeaturesMeta()
        extracted_issues_features_meta = Issues.getExtractedFeaturesMeta()
        change_request_meta = self.change_request_meta_map[change_request_issue_key]

        out['Meta'] = extracted_features_meta

        project_key = change_request_meta['project_key']
        version_name = change_request_meta['fixVersion']

        out['number_of_issues'] = len(change_request_meta['linked_issues'])
        out['number_of_bugs'] = 0#len(issues_bugs)
        out['number_of_features'] = 0#len(issues_features)
        out['number_of_improvements'] = 0
        out['number_of_other'] = 0
        
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
        
        for issue in self.issue_map.getIssuesByKeys(change_request_meta['linked_issues']):

            if project_key in self.projects_version_info_map:
                extracted_features = self.issue_map.getExtractedFeatures(issue, self.projects_version_info_map[project_key], date)

                if not extracted_features is None:
                    out['discussion_time']['data'] += [extracted_features['discussion_time'].total_seconds()]
                    out['number_of_comments']['data'] += [extracted_features['number_of_comments']]
                    
                    out['number_of_blocked_by_issues']['data'] += [extracted_features['number_of_blocked_by_issues']]
                    out['number_of_blocks_issues']['data'] += [extracted_features['number_of_blocks_issues']]

                    for change in extracted_issues_features_meta['change_map_names']:
                        out['number_of_changes_to_%s' % change]['data'] += [len(extracted_features['changes'][change])]

                    for feature_key, feature_values in self.features_values_map.items():
                        for value in feature_values:
                            out['number_of_%s_%s' % (str(feature_key), value)]['data'] += [len(jsonquery.query(issue, 'fields.%s:%s' % (feature_key.replace('_', '.'), value)))]
                    
                    out['number_of_bugs'] += len(jsonquery.query(issue, 'fields.issuetype.name:Bug'))
                    out['number_of_features'] += len(jsonquery.query(issue, 'fields.issuetype.name:New Feature'))
                    out['number_of_improvements'] += len(jsonquery.query(issue, 'fields.issuetype.name:Improvement'))

                    if extracted_features['delays'].total_seconds() >= 0:
                        out['delays']['data'] += [extracted_features['delays'].total_seconds()]
                    
                    if out['earliest_date'] is None or out['earliest_date'] > extracted_features['created_date']:
                        out['earliest_date'] = extracted_features['created_date']

                    if not extracted_features['assignee_key'] is None:
                        out['team_members'][extracted_features['assignee_key']] = extracted_features['assignee_displayName']
                        out['participants'][extracted_features['assignee_key']] = extracted_features['assignee_displayName']
                    
                    if not extracted_features['reporter_key'] is None:
                        out['reporters'][extracted_features['reporter_key']] = extracted_features['reporter_displayName']
                        out['participants'][extracted_features['reporter_key']] = extracted_features['reporter_displayName']

                    for comment in extracted_features['comments']:
                        out['participants'][comment['author_accountId']] = comment['author_displayName']

        out['number_of_other'] = out['number_of_issues'] - (out['number_of_bugs'] + out['number_of_features'] + out['number_of_improvements'])
        
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
        
        return out
