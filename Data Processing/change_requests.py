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

class ChangeRequest:
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
            issue = self.issue_map.get(issue_key)
            fvote_count += issue['fields']['votes']['votes']
            for comment in issue['fields']['comment']['comments']:
                if Issues.parseDateTime(comment['created']) >= change_request_meta['release_date']:
                    fcomment_count += 1

        acomment_count = 0
        avote_count = 0
        for issue_key in change_request_meta['affected_issues']:
            issue = self.issue_map.get(issue_key)
            acomment_count += len(issue['fields']['comment']['comments'])
            avote_count += issue['fields']['votes']['votes']

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
        except Exception as e:
            labels = {}
            
        datautil.map(labels, (change_request_issue_key,), label)

        with open(filename, 'w') as f:
            f.write(json.dumps(labels, indent=4, sort_keys=True))
        
    def generate(self):
        issues = jsonquery.query(list(self.issue_map.get().values()), '$fields.fixVersions.name')
        for issue in issues:
            project_key = issue['fields']['project']['key']
            issue_key = issue['key']
            versions = issue['fields']['fixVersions']
            for version in versions:
                version_name = version['name']
                datautil.map_set(self.projects_fixVersions_issue_map, (project_key, version_name), issue_key)
                datautil.map(self.projects_version_info_map, (project_key, version_name), version)

        issues = jsonquery.query(list(self.issue_map.get().values()), '$fields.versions.name')
        for issue in issues:
            project_key = issue['fields']['project']['key']
            issue_key = issue['key']
            versions = issue['fields']['versions']
            for version in versions:
                version_name = version['name']
                datautil.map_set(self.projects_affectsVersions_issue_map, (project_key, version_name), issue_key)
                datautil.map(self.projects_version_info_map, (project_key, version_name), version)

        # Load real change requests
        issueList = list(self.issue_map.get().values())
        change_request_issue_map = []

        for x in issueList:
            if 'change' in x['fields']['issuetype']['name'].lower():
                change_request_issue_map.append(x)

        change_request_issue_keys = jsonquery.query(issues, 'fields.^key')

        for change_request_issue in change_request_issue_map:
            change_request_project_key = change_request_issue['fields']['project']['key']
            change_request_issue_key = change_request_issue['key']
            change_request_linked_issues = jsonquery.query(change_request_issue, 'fields.issuelinks.inwardIssue.^key')
            change_request_release_date = Issues.parseDateTime(change_request_issue['fields']['created'])
            change_request_last_updated = None

            for issue_key in change_request_linked_issues:
                change_request_issue_keys += [issue_key]

                issue = self.issue_map.get(issue_key)
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
                if 'releaseDate' in change_request_version:
                     change_request_release_date = Issues.parseDateTimeSimple(change_request_version['releaseDate'])
                else:
                    continue

                fixed_issues = []
                for issue_key in issue_map:
                    
                    if issue_key in change_request_issue_keys:
                        continue

                    extracted_features = self.issue_map.getExtractedFeatures(issue_key, [], change_request_release_date)
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

                    issue = self.issue_map.get(issue_key)
                    issue_creation_date = Issues.parseDateTime(issue['fields']['created'])
                    
                    resolution = jsonquery.query(issue, 'fields.resolution.^name')
                    status = jsonquery.query(issue, 'fields.status.^name')
                    issuetype = jsonquery.query(issue, 'fields.issuetype.^name')
                    
                    is_chronological = issue_creation_date >= change_request_release_date
                    is_fixed = len(resolution) == 1 and resolution[0] == 'Fixed'
                    is_bug = len(issuetype) == 1 and issuetype[0] == 'Bug'

                    dates = []
                    for version in issue['fields']['versions']:
                        if 'releaseDate' in version:
                            version_date = Issues.parseDateTimeSimple(version['releaseDate'])
                            dates += [version_date]
                    
                    is_earliest_version = min(dates) == change_request_release_date

                    if is_earliest_version and is_chronological and is_bug and is_fixed:
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

    def getExtractedFeatures(self, change_request_issue_key, date):
        out = {}
        
        import statistics

        out['Meta'] = {
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

        change_request_meta = self.change_request_meta_map[change_request_issue_key]
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

        for feature in out['Meta']['aggregated_features']:
            out[feature] = {
                'data': []
            }

        out['release_date'] = change_request_meta['release_date']

        for issue_key in change_request_meta['linked_issues']:
            issue = self.issue_map.get(issue_key)

            if project_key in self.projects_version_info_map:
                extracted_features = self.issue_map.getExtractedFeatures(issue_key, self.projects_version_info_map[project_key], date)
                
                if not extracted_features is None:
                    out['discussion_time']['data'] += [extracted_features['discussion_time'].total_seconds()]
                    out['number_of_comments']['data'] += [extracted_features['number_of_comments']]
                    
                    out['number_of_blocked_by_issues']['data'] += [extracted_features['number_of_blocked_by_issues']]
                    out['number_of_blocks_issues']['data'] += [extracted_features['number_of_blocks_issues']]
                    
                    out['number_of_bugs'] += len(jsonquery.query(issue, 'fields.issuetype.name:Bug'))
                    out['number_of_features'] += len(jsonquery.query(issue, 'fields.issuetype.name:New Feature'))
                    out['number_of_improvements'] += len(jsonquery.query(issue, 'fields.issuetype.name:Improvement'))

                    if extracted_features['delays'].total_seconds() >= 0:
                        out['delays']['data'] += [extracted_features['delays'].total_seconds()]
                    
                    if out['earliest_date'] is None or out['earliest_date'] > extracted_features['created_date']:
                        out['earliest_date'] = extracted_features['created_date']

                    if not extracted_features['assignee_accountId'] is None:
                        out['team_members'][extracted_features['assignee_accountId']] = extracted_features['assignee_displayName']
                        out['participants'][extracted_features['assignee_accountId']] = extracted_features['assignee_displayName']
                    
                    if not extracted_features['reporter_accountId'] is None:
                        out['reporters'][extracted_features['reporter_accountId']] = extracted_features['reporter_displayName']
                        out['participants'][extracted_features['reporter_accountId']] = extracted_features['reporter_displayName']

                    for comment in extracted_features['comments']:
                        out['participants'][comment['author_accountId']] = comment['author_displayName']

        out['number_of_other'] = out['number_of_issues'] - (out['number_of_bugs'] + out['number_of_features'] + out['number_of_improvements'])
        
        out['number_of_participants'] = len(out['participants'].keys())
        out['number_of_team_members'] = len(out['team_members'].keys())
        out['number_of_reporters'] = len(out['reporters'].keys())

        if not out['earliest_date'] is None and not out['release_date'] is None:
            out['elapsed_time'] = out['release_date'] - out['earliest_date']
        
        for feature in out['Meta']['aggregated_features']:
            L = len(out[feature]['data'])
            
            for aggregator_name, aggregator in out['Meta']['aggregators'].items():
                out[feature][aggregator_name] = 0

                if L == 1:
                    out[feature][aggregator_name] = out[feature]['data'][0]
                elif L > 1:
                    out[feature][aggregator_name] = aggregator(out[feature]['data'])
        
        return out
