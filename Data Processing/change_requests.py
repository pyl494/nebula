# Purpose
# This scans jira issues and tries to generate change requests from fix versions and affects versions

# Instructions
# This script requires the json data dumps

# Status
# the OOP in this is a terrible last minute thing.
# Does not yet properly generate change requests

# Source
# Harun Delic

import jsonquery
import json
import datetime
import datautil
import issues

class ChangeRequest:
    def __init__(self, issue_map):
        self.issue_map = issue_map

        self.projects_fixVersions_issue_map = {
            # PROJECT: {fixVersion: {issue_key: issue}}
        }

        self.projects_affectsVersions_issue_map = {
            # PROJECT : {affectsVersion: {issue_key: issue}}
        }

        self.change_request_map = {
            #PROJECT KEY: [
            #     summary: -> Change request fixVersion.name
            #     creationDate: -> fixVersion.releaseDate
            #     fixVersion: -> fixVersion.name
            #     linkedIssues: -> all issues with the same fixVersion
            # ]
        }

        self.projects_version_info_map = {
            # PROJECT: {fixVersion: {data}}
        }

    def getProjectsFixVersionIssueMap(self):
        return self.projects_fixVersions_issue_map
    
    def getProjectsAffectsVersionIssueMap(self):
        return self.projects_affectsVersions_issue_map

    def getChangeRequestMap(self):
        return self.change_requests

    def getProjectsVersionInfoMap(self):
        return self.projects_version_info_map

    def getIssueMap(self):
        return self.issue_map

    def getAutomaticRiskLabel(self, project, version):
        if project in self.projects_fixVersions_issue_map:
            if version in self.projects_fixVersions_issue_map[project] and len(self.projects_fixVersions_issue_map[project][version]) > 0:
                if project in self.projects_affectsVersions_issue_map:
                    aversions = self.projects_affectsVersions_issue_map[project]
                    acount = 0
                    if version in aversions:
                        acount = len(aversions[version])

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
                else:
                    return 'low'
        
        return None

    def getManualRiskLabel(self, project, version):
        try:
            filename = '../Data Labels/' + self.issue_map.getUniverseName() + '_' + project + '.json'
            with open(filename, 'r') as f:
                labels = json.loads(f.read())
            
            return labels[version]

        except Exception as e:
            return None

    def setManualRiskLabel(self, project, version, label):
        try:
            filename = '../Data Labels/' + self.issue_map.getUniverseName() + '_' + project + '.json'
            with open(filename, 'r') as f:
                labels = json.loads(f.read())
        except Exception as e:
            labels = {}
            
        datautil.map(labels, (version,), label)

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

    def filterIssuesCreatedAfter(self):
        for project_key, version_issue_map in self.projects_fixVersions_issue_map.items():
            print(project_key)
            
            for version_name, issues in version_issue_map.items():
                v = projects_version_info_map[project_key][version_name]
                if 'releaseDate' in v:
                    print('  ',version_name, ' -> ', len(issues))
                    version_release_date = ChangeRequest.date(v['releaseDate'])
                    
                    for issue_key in issues:
                        issue = self.issue_map.get(issue_key)
                        issue_creation_date = ChangeRequest.date(issue['fields']['created'][:10])

                        if issue_creation_date >= version_release_date:
                            print('   ', issue['id'])
                        
                        resolution = jsonquery.query(issue, 'fields.resolution.^name')
                        status = jsonquery.query(issue, 'fields.status.^name')
                        issuetype = jsonquery.query(issue, 'fields.issuetype.^name')
                        
                        is_fixed = len(resolution) == 1 and resolution[0] == 'Fixed'
                        is_chronological = issue_creation_date <= version_release_date
                        is_closed = len(status) == 1 and status[0] == 'Closed'
                        is_bug = len(issuetype) == 1 and issuetype[0] == 'Bug'

                        if is_fixed and is_bug:
                            print('   ', issue['id'])

    def date(release_date_string):
        dateparts = release_date_string.split('-')
        return datetime.date(int(dateparts[0]), int(dateparts[1]), int(dateparts[2]))

    def getExtractedFeatures(self, project, version_name, version_issues):
        out = {}

        out['number_of_issues'] = len(version_issues)
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

        out['release_date'] = None
        version_info = self.projects_version_info_map[project][version_name]
        if 'releaseDate' in version_info:
            out['release_date'] = issues.Issues.parseDateTimeSimple(version_info['releaseDate'])

        for issue_key in version_issues:
            issue = self.issue_map.get(issue_key)

            extracted_features = self.issue_map.getExtractedFeatures(issue_key, project)
            
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

    issue_map = issues.Issues('Atlassian Projects', ROOT, 'ATLASSIAN_', 1000)
    for status in issue_map.load():
        print(status)
    
    test = ChangeRequest(issue_map)
    
    test.generate()
    
    test.displayChangeRequestIssues()

    for project, version in test.getProjectsVersionInfoMap().items():
        print(project, json.dumps(version, indent=1))