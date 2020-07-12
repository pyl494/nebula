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

        self.change_request_map = {
            #issue_key: {
            #     issue...
            #     'ChangeRequestMeta': {
            #        project_key: project_key,
            #        release_date: fixVersion.releaseDate,
            #        fixVersion: fixVersion.name,
            #        linked_issues: [issue_keys],
            #        affected_issues: [issue_keys]
            #     }
            # }
        }

        self.projects_version_info_map = {
            # PROJECT: {fixVersion: {data}}
        }

    def getChangeRequestIssueMap(self):
        return self.change_request_map

    def getProjectsFixVersionIssueMap(self):
        return self.projects_fixVersions_issue_map
    
    def getProjectsAffectsVersionIssueMap(self):
        return self.projects_affectsVersions_issue_map

    def getProjectsVersionInfoMap(self):
        return self.projects_version_info_map

    def getIssueMap(self):
        return self.issue_map

    def getAutomaticRiskLabel(self, change_request_issue_key):
        change_request_meta = self.change_request_map[change_request_issue_key]['ChangeRequestMeta']
        acount = len(change_request_meta['affected_issues'])

        import math
        i = min(2, 
            int(
                math.log10(
                    max(1, 
                        acount
                    )
                )
            )
        )

        return ['low', 'medium', 'high'][i]

    def getManualRiskLabel(self, change_request_issue_key):
        try:
            project_key = self.change_request_map[change_request_issue_key]['ChangeRequestMeta']['project_key']

            filename = '../Data Labels/' + self.issue_map.getUniverseName() + '_' + project_key + '.json'
            with open(filename, 'r') as f:
                labels = json.loads(f.read())
            
            return labels[change_request_issue_key]

        except Exception as e:
            return None

    def setManualRiskLabel(self, change_request_issue_key, label):
        try:
            project_key = self.change_request_map[change_request_issue_key]['ChangeRequestMeta']['project_key']

            filename = '../Data Labels/' + self.issue_map.getUniverseName() + '_' + project_key + '.json'
            with open(filename, 'r') as f:
                labels = json.loads(f.read())
        except Exception as e:
            labels = {}
            
        datautil.map(labels, (change_request_issue_key,), label)

        with open(filename, 'w') as f:
            f.write(json.dumps(labels, indent=4, sort_keys=True))
        
    def displayChangeRequestIssues(self):
        for project_key, version_issue_map in self.projects_fixVersions_issue_map.items():
            for version_name, issues in version_issue_map.items():
                for issue_key in issues:
                    issue = self.issue_map.get(issue_key)
                    print('{key}  v\'{version}\' [{issue_key}]'.format(
                        key=project_key,
                        version=version_name,
                        issue_key=issue_key
                    ))

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
        
        # Now generate the actual change requests
        for project_key, fixVersions_issue_map in self.projects_fixVersions_issue_map.items():
            
            i = 0
            for version_name, issue_map in fixVersions_issue_map.items():
                change_request_issue_key = project_key + '_gcr_-' + str(i)
                i += 1

                change_request_version = self.projects_version_info_map[project_key][version_name]
                change_request_release_date = None
                if 'releaseDate' in change_request_version:
                    change_request_release_date = Issues.parseDateTimeSimple(change_request_version['releaseDate'])
                else:
                    continue

                fixed_issues = []
                for issue_key in issue_map:
                    issue = self.issue_map.get(issue_key)
                    issue_creation_date = Issues.parseDateTimeSimple(issue['fields']['created'][:10])
                    
                    resolution = jsonquery.query(issue, 'fields.resolution.^name')
                    status = jsonquery.query(issue, 'fields.status.^name')
                    issuetype = jsonquery.query(issue, 'fields.issuetype.^name')
                    
                    is_fixed = len(resolution) == 1 and resolution[0] == 'Fixed'
                    is_chronological = issue_creation_date <= change_request_release_date
                    is_closed = len(status) == 1 and status[0] == 'Closed'
                    is_bug = len(issuetype) == 1 and issuetype[0] == 'Bug'
                    
                    dates = []
                    for version in issue['fields']['fixVersions']:
                        if 'releaseDate' in version:
                            version_date = Issues.parseDateTimeSimple(version['releaseDate'])
                            dates += [version_date]
                    
                    is_earliest_version = min(dates) == change_request_release_date

                    if is_earliest_version and is_fixed and is_chronological and is_closed:# and is_bug:
                        fixed_issues += [issue_key]

                if len(fixed_issues) == 0:
                    continue

                affected_issues = datautil.map_get(self.projects_affectsVersions_issue_map, (project_key, version_name))
                if affected_issues is None:
                    affected_issues = []
                
                related_affected_issues = []
                for issue_key in affected_issues:
                    issue = self.issue_map.get(issue_key)
                    issue_creation_date = Issues.parseDateTime(issue['fields']['created'])
                    
                    resolution = jsonquery.query(issue, 'fields.resolution.^name')
                    status = jsonquery.query(issue, 'fields.status.^name')
                    issuetype = jsonquery.query(issue, 'fields.issuetype.^name')
                    
                    is_chronological = issue_creation_date >= change_request_release_date
                    is_bug = len(issuetype) == 1 and issuetype[0] == 'Bug'

                    dates = []
                    for version in issue['fields']['versions']:
                        if 'releaseDate' in version:
                            version_date = Issues.parseDateTimeSimple(version['releaseDate'])
                            dates += [version_date]
                    
                    is_earliest_version = min(dates) == change_request_release_date

                    if is_earliest_version and is_chronological and is_closed:# and is_bug:
                        related_affected_issues += [issue_key]

                datautil.map(self.change_request_map, (change_request_issue_key, 'ChangeRequestMeta'),{
                    'project_key': project_key,
                    'fixVersion': version_name,
                    'release_date': change_request_release_date,
                    'linked_issues': fixed_issues,
                    'affected_issues': related_affected_issues
                })

    def getExtractedFeatures(self, change_request_issue_key):
        out = {}

        change_request_meta = self.change_request_map[change_request_issue_key]['ChangeRequestMeta']
        project_key = change_request_meta['project_key']
        version_name = change_request_meta['fixVersion']

        out['number_of_issues'] = len(change_request_meta['linked_issues'])
        out['number_of_bugs'] = 0#len(issues_bugs)
        out['number_of_features'] = 0#len(issues_features)
        out['number_of_improvements'] = 0
        out['number_of_other'] = 0
        
        out['number_of_comments'] = 0
        out['discussion_time'] = datetime.timedelta()

        out['number_of_blocked_by_issues'] = 0
        out['number_of_blocks_issues'] = 0

        out['participants'] = {}
        out['number_of_participants'] = 0

        out['elapsed_time'] = datetime.timedelta()
        out['earliest_date'] = None
        out['delays'] = datetime.timedelta()

        out['release_date'] = change_request_meta['release_date']

        for issue_key in change_request_meta['linked_issues']:
            issue = self.issue_map.get(issue_key)

            extracted_features = self.issue_map.getExtractedFeatures(issue_key, self.projects_version_info_map[project_key])
            
            out['discussion_time'] += extracted_features['discussion_time']
            out['number_of_comments'] += extracted_features['number_of_comments']
            
            out['number_of_blocked_by_issues'] += extracted_features['number_of_blocked_by_issues']
            out['number_of_blocks_issues'] += extracted_features['number_of_blocks_issues']
            
            out['number_of_bugs'] += len(jsonquery.query(issue, 'fields.issuetype.name:Bug'))
            out['number_of_features'] += len(jsonquery.query(issue, 'fields.issuetype.name:New Feature'))
            out['number_of_improvements'] += len(jsonquery.query(issue, 'fields.issuetype.name:Improvement'))

            if extracted_features['delays'].days >= 0:
                out['delays'] += extracted_features['delays']
            
            if out['earliest_date'] is None or out['earliest_date'] > extracted_features['created_date']:
                out['earliest_date'] = extracted_features['created_date']

            if not extracted_features['assignee_accountId'] is None:
                out['participants'][extracted_features['assignee_accountId']] = extracted_features['assignee_displayName']
            
            if not extracted_features['reporter_accountId'] is None:
                out['participants'][extracted_features['reporter_accountId']] = extracted_features['reporter_displayName']

            for comment in extracted_features['comments_extracted']:
                out['participants'][comment['author_accountId']] = comment['author_displayName']

        out['number_of_other'] = out['number_of_issues'] - (out['number_of_bugs'] + out['number_of_features'] + out['number_of_improvements'])
        out['number_of_participants'] = len(out['participants'].keys())

        if not out['earliest_date'] is None and not out['release_date'] is None:
            out['elapsed_time'] = out['release_date'] - out['earliest_date']

        return out
                
if __name__ == '__main__':
    with open('../jsondumps.txt', 'r') as f:
        ROOT = f.readline()

    import issues

    issue_map = Issues('Atlassian Projects', ROOT, 'ATLASSIAN_', 1000)
    for status in issue_map.load():
        print(status)
    
    test = ChangeRequest(issue_map)
    
    test.generate()
    
    test.displayChangeRequestIssues()

    for project, version in test.getProjectsVersionInfoMap().items():
        print(project, json.dumps(version, indent=1))