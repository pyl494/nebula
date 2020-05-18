# Purpose
# This scans jira issues and tries to generate change requests from fix versions and affects versions

# Instructions
# This script requires the json data dumps

# Status
# the OOP in this is a terrible last minute thing.
# Does not yet properly generate change requests

# Source
# Harun Delic

from jsonquery import query
import json
import datetime
import datautil

class GenerateChangeRequests:
    def __init__(self, issueMap):
        self.issueMap = issueMap

        self.projectsFixVersions = {
            # PROJECT: {fixVersion: {issuekey: issue}}
        }

        self.projectsAffectsVersions = {
            # PROJECT : {affectsVersion: {issuekey: issue}}
        }

        self.changeRequests = {
            #PROJECT KEY: [
            #     summary: -> Change request fixVersion.name
            #     creationDate: -> fixVersion.releaseDate
            #     fixVersion: -> fixVersion.name
            #     linkedIssues: -> all issues with the same fixVersion
            # ]
        }

        self.versionMap = {
            # PROJECT: {fixVersion: {data}}
        }

    def getProjectsFixVersions(self):
        return self.projectsFixVersions
    
    def getProjectsAffectsVersions(self):
        return self.projectsAffectsVersions

    def getChangeRequests(self):
        return self.changeRequests

    def getVersionMap(self):
        return self.versionMap

    def getIssueMap(self):
        return self.issueMap

    def displayChangeRequestIssues(self):
        for project, versions in self.projectsFixVersions.items():
            for version, issues in versions.items():
                for issuekey in issues:
                    issue = self.issueMap.get(issuekey)
                    print('{key}  v\'{version}\' [{issuekey}]'.format(
                        key=project,
                        version=version,
                        issuekey=issuekey
                    ))

    def generate(self):
        issues = query(list(self.issueMap.get().values()), '$fields.fixVersions.name')
        for issue in issues:
            key = issue['fields']['project']['key']
            issueKey = issue['key']
            versions = issue['fields']['fixVersions']
            for version in versions:
                versionName = version['name']
                datautil.map_list(self.projectsFixVersions, (key, versionName), issueKey)
                datautil.map(self.versionMap, (key, versionName), version)

        issues = query(list(self.issueMap.get().values()), '$fields.versions.name')
        for issue in issues:
            key = issue['fields']['project']['key']
            issueKey = issue['key']
            versions = issue['fields']['versions']
            for version in versions:
                datautil.map_list(self.projectsAffectsVersions, (key, versionName), issueKey)
                datautil.map(self.versionMap, (key, versionName), version)

    def filterIssuesCreatedAfter(self):
        for key, versions in projectsFixVersions.items():
            print(key)
            
            for version, issues in versions.items():
                v = versionMap[key][version]
                if 'releaseDate' in v:
                    print('  ',version, ' -> ', len(issues))
                    versionReleaseDate = GenerateChangeRequests.date(v['releaseDate'])
                    
                    for issuekey in issues:
                        issue = self.issueMap.get(issuekey)
                        issueCreationDate = GenerateChangeRequests.date(issue['fields']['created'][:10])

                        if issueCreationDate >= versionReleaseDate:
                            print('   ', issue['id'])
                        
                        resolution = query(issue, 'fields.resolution.^name')
                        status = query(issue, 'fields.status.^name')
                        issuetype = query(issue, 'fields.issuetype.^name')
                        
                        is_fixed = len(resolution) == 1 and resolution[0] == 'Fixed'
                        is_chronological = issueCreationDate <= versionReleaseDate
                        is_closed = len(status) == 1 and status[0] == 'Closed'
                        is_bug = len(issuetype) == 1 and issuetype[0] == 'Bug'

                        if is_fixed and is_bug:
                            print('   ', issue['id'])

    def date(releaseDateString):
        dateparts = releaseDateString.split('-')
        return datetime.date(int(dateparts[0]), int(dateparts[1]), int(dateparts[2]))
                
if __name__ == '__main__':
    with open('../jsondumps.txt', 'r') as f:
        ROOT = f.readline()

    import issues

    issueMap = issues.Issues('Atlassian Projects', ROOT, 'ATLASSIAN_')
    for status in issueMap.load():
        print(status)
    
    test = GenerateChangeRequests(issueMap)
    
    test.generate()
    
    test.displayChangeRequestIssues()

    for project, version in test.getVersionMap().items():
        print(project, json.dumps(version, indent=1))