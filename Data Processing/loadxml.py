# Purpose
# This was the first method I used to convert xml dumps to json. This is no longer relevant

# Instructions
# This script requires the xml data dumps

# Status
# This should run.

# Source
# Harun Delic

ROOT = 'F:/xmldumps/atlassian/'

import xml.etree.ElementTree as ET
import json

from html.parser import HTMLParser

class HtmlDataExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.extracted_data = ""

    def handle_data(self, data):
        self.extracted_data += data.strip() + "\n"

    def get_extracted_data(self):
        return self.extracted_data.replace('\n\n','\n')[:-1]

#indent = '  '
#tags = set()
#attributes = set()

def recurse(element, depth, includeCustomFields = False):
    #if (not includeCustomFields) and ('custom' in element.tag):
    #    return None

    o = {}
    #tags.add(element.tag)
    for a in element.attrib:
        o[a] = element.attrib[a]
        #attributes.add(a)

    #print(indent * depth, element.tag, element.attrib)

    for elem in element:
        r = recurse(elem, depth + 1)

        #post process
        if not r is None:
            v = r[1]

            if isinstance(v, dict):
                keys = list(v.keys())
                if len(keys) == 1 and keys[0] == r[0]:
                    #"key":{"key":"value"} -> "key":"value"
                    v = v[r[0]]
                elif len(keys) == 0:
                    #"key":{} -> "key": None
                    v = None
            
            # add this element to the output dictionary
            if r[0] in o:
                if not isinstance(o[r[0]], list):
                    o[r[0]] = [ o[r[0]] ]
                
                o[r[0]].append(v)
            else:    
                o[r[0]] = v
    
    if (not element.text is None):
        parser = HtmlDataExtractor()
        parser.feed(element.text)
        #print(indent * (depth + 1), parser.get_extracted_data().encode('utf-8'))
        o[element.tag] = parser.get_extracted_data()
    
    return (element.tag, o)


def xmlstojsons(basename, includeCustomFields=False):
    count = 0
    problems = []#[190190, 257257, 260260, 733733, 874874, 877877]
    
    search = True

    while search:
        if count in problems:
            count += 1001
            continue

        try:
            name = basename + '_' + str(count) + '.xml'
            print(name)
            #context = ET.iterparse(name, events=('start', 'end') )
            #context = iter(context)
            #event, root = next(context)
            #for event, elem in context:
            #    pass
            context = ET.parse(name)
            root = context.getroot()
            #print(root)

            out = recurse(root, 0)
            issues = out[1]['channel']['item']

            try:
                name = basename + '_' + str(count + 1000) + '.xml'
                context = ET.parse(name)
                root = context.getroot()

                out = recurse(root, 0, includeCustomFields)
                issues += [out[1]['channel']['item']]
                print('ok')
            except:
                print('bad')
                pass

            issues = {'issues': issues}

            j = json.dumps(issues, indent=4)

            with open(basename + '_' + str(count) + '.json', 'w') as f:
                f.write(j)

            count += 1001
        except:
            search = False

xmlstojsons(ROOT + 'ATLASSIAN', includeCustomFields=True)

#print('number of issues:', len(issues['issues']))

#for issue in issues['issues']:
#    if 'comments' in issue:
#        print(issue['title'], len(issue['comments']['comment']))
        #for comment in issue['comments']:
        #    print(comment)