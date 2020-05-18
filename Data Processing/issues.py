
import datautil
import json

class Issues:
    def __init__(self, universeName, dataLocation, dataPrefix):
        self.universeName = universeName
        self.dataLocation = dataLocation
        self.dataPrefix = dataPrefix
        self.issueMap = {}

    def load(self):
        count = 0
        while True:
            try:
                with open(self.dataLocation + self.dataPrefix + str(count) + '.json', 'r', encoding='UTF-8') as f:
                    issues = json.loads(f.read())
                
                for issue in issues['issues']:
                    datautil.map(self.issueMap, (issue['key'],), issue)
                
                yield self.dataPrefix + str(count)

                count += 1000
                #if count > 1000:
                #    break######### REMOVE THIS TO PROCESS ALL FILES

            except Exception as e:
                print('error', e)
                break
    
    def getUniverseName(self):
        return self.universeName

    def getDataLocation(self):
        return self.dataLocation

    def getDataPrefix(self):
        return self.dataPrefix

    def get(self, issuekey = None):
        if issuekey is None:
            return self.issueMap
        else:
            return self.issueMap[issuekey]
        
