# Purpose
# This allows you to dig through a python data structure and extract specific things out of it in one line.
# example: query(CLOVER_data, 'issues.fields.^summary') will return all issue summaries
# example: query(CLOVER_data, 'issues.$fields.assignee.name:bob') will return all issues with bob as an assignee
# example: query(CLOVER_data, 'issues.fields.^*:Task') will return any field with the value 'Task'

# Instructions
# This script requires the json data dumps

# Status
# This should run.

# Source
# Harun Delic

import json

def query(element, query, breadcrumbs = False):
    parts = query.split('.')

    result = [(element, element, [])]
    
    for part in parts:
        conditional = part.split(':')
        if len(conditional) == 0:
            raise 'bad format'

        check_condition = len(conditional) == 2
        updateCheckpoint = '^' in conditional[0]
        updateCheckpoint2 = '$' in conditional[0]
        conditional[0] = conditional[0].replace('^', '')
        conditional[0] = conditional[0].replace('$', '')

        conditional[0] = conditional[0].split('|')
        for i in range(len(conditional[0])):
            conditional[0][i] = conditional[0][i].strip()

        if check_condition:
            conditional[1] = conditional[1].split('|')
            for i in range(len(conditional[1])):
                conditional[1][i] = conditional[1][i].strip()
        r = []
        for i in range(len(result)):
            node = result[i]

            array = [node[0]]
            if isinstance(node[0], list):
                array = node[0]

            firstConditional = conditional[0][0]
            if firstConditional == '*':
                for element in array:
                    for child in element:
                        if not check_condition or element[child] in conditional[1] or child in conditional[1]:
                            checkpoint = node[1]
                            if updateCheckpoint:
                                checkpoint = element[child]
                            elif updateCheckpoint2:
                                if isinstance(node[0], list):
                                    checkpoint = element
                                else:
                                    checkpoint = node[0]

                            r += [(element[child], checkpoint, node[2] + [child])]
            else:
                for name in conditional[0]:
                    success = False

                    for element in array:
                        if name in element:
                            if not check_condition or element[name] in conditional[1]:
                                checkpoint = node[1]
                                if updateCheckpoint:
                                    checkpoint = element[name]
                                elif updateCheckpoint2:
                                    if isinstance(node[0], list):
                                        checkpoint = element
                                    else:
                                        checkpoint = node[0]
 
                                r += [(element[name], checkpoint, node[2] + [name])]
                            success = True
                    
                    if success:
                        break
        result = r
    r = []
    if breadcrumbs:
        for node in result:
            if isinstance(node[1], list) and len(node[1]) == 1:
                r += [(tuple(node[2]), node[1][0])]    
            else:
                r += [(tuple(node[2]), node[1])]
    else:
        for node in result:
            if isinstance(node[1], list) and len(node[1]) == 1:
                r += [node[1][0]]
            else:
                r += [node[1]]
    return r

if __name__ == '__main__':
    test = 'test.$inner:blah'

    b = json.loads('{"test": {"inner": "blah"} }')
    print(query(b, test))

    b = json.loads('[{"test": {"inner": "blah"} }]')
    print(query(b, test))

    b = json.loads('{"test": [{"inner": "blah"}] }')
    print(query(b, test))

    b = json.loads('[{"test": {"inner": "blah"} }, {"test": {"inner": "blah2"} }]')
    print(query(b, test))

    b = json.loads('{"test": [{"inner": "blah"}, {"inner": "blah2"}] }')
    print(query(b, test))

    b = json.loads('{"test": [{"inner": "blah", "big": "stuff"}, {"inner": "blah2"}] }')
    print(query(b, test))

    #print(get(get(b, 'issues.^project.key:BAM')[0][1],
    #    'resolution.resolution:Unresolved'))
