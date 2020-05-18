
def map(dataStructure, keys, data):
    for key in keys[:-1]:
        if not key in dataStructure:
            dataStructure[key] = {}
        
        dataStructure = dataStructure[key]
    dataStructure[keys[-1]] = data

def map_list(dataStructure, keys, data):
    for key in keys[:-1]:
        if not key in dataStructure:
            dataStructure[key] = {}
        
        dataStructure = dataStructure[key]
    
    if not keys[-1] in dataStructure:
        dataStructure[keys[-1]] = [data]
    else:
        dataStructure[keys[-1]] += [data]

def map_set(dataStructure, keys, data):
    for key in keys[:-1]:
        if not key in dataStructure:
            dataStructure[key] = {}
        
        dataStructure = dataStructure[key]
    
    if not keys[-1] in dataStructure:
        dataStructure[keys[-1]] = {data}
    else:
        dataStructure[keys[-1]].add(data)
    