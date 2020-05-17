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

class GenerateChangeRequests:
    def __init__(self):
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

    def displayChangeRequestIssues(self):
        for project, versions in self.projectsFixVersions.items():
            for version, issues in versions.items():
                for issuekey, issue in issues.items():
                    print('{key}  v\'{version}\' [{issuekey}]'.format(
                        key=project,
                        version=version,
                        issuekey=issuekey
                    ))

    def generate(self):
        with open('../jsondumps.txt', 'r') as f:
            ROOT = f.readline()

        count = 0
        while True:
            try:
                with open(ROOT + 'ATLASSIAN_' + str(count) + '.json', 'r', encoding='UTF-8') as f:
                    data = json.loads(f.read())

                issues = query(data, 'issues.$fields.fixVersions.name')
                for issue in issues:
                    key = issue['fields']['project']['key']
                    issueKey = issue['key']
                    versions = issue['fields']['fixVersions']
                    for version in versions:
                        versionName = version['name']
                        self.map(self.projectsFixVersions, (key, versionName, issueKey), issue)
                        self.map(self.versionMap, (key, versionName), version)

                issues = query(data, 'issues.$fields.versions.name')
                for issue in issues:
                    key = issue['fields']['project']['key']
                    issueKey = issue['key']
                    versions = issue['fields']['versions']
                    for version in versions:
                        self.map(self.projectsAffectsVersions, (key, versionName, issueKey), issue)
                        self.map(self.versionMap, (key, versionName), version)

                yield 'ATLASSIAN_' + str(count)

                count += 1000
                #if count > 10000:
                #    break######### REMOVE THIS TO PROCESS ALL FILES

            except Exception as e:
                print('error', e)
                break

    def map(self, dataStructure, keys, data):
        for key in keys[:-1]:
            if not key in dataStructure:
                dataStructure[key] = {}
            
            dataStructure = dataStructure[key]
        dataStructure[keys[-1]] = data

    def date(releaseDateString):
        dateparts = releaseDateString.split('-')
        return datetime.date(int(dateparts[0]), int(dateparts[1]), int(dateparts[2]))
                

if __name__ == '__main__':
    test = GenerateChangeRequests()

    for file in test.generate():
        print(file)
    
    test.displayChangeRequestIssues()

    for project, version in test.getVersionMap().items():
        print(project, json.dumps(version, indent=1))