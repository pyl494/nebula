
def map(dataStructure, keys, data):
    for key in keys[:-1]:
        if not key in dataStructure:
            dataStructure[key] = {}
        
        dataStructure = dataStructure[key]
    dataStructure[keys[-1]] = data

def map_get(dataStructure, keys, default=None):
    for key in keys[:-1]:
        if not key in dataStructure:
            dataStructure = None
            break
        
        dataStructure = dataStructure[key]

    if not dataStructure is None and keys[-1] in dataStructure:
        return dataStructure[keys[-1]]
    
    return default

def map_touch(dataStructure, keys, data):
    for key in keys[:-1]:
        if not key in dataStructure:
            dataStructure[key] = {}
        
        dataStructure = dataStructure[key]

    if not keys[-1] in dataStructure:
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

def unlist_one(x):
    if isinstance(x, list) and len(x) == 1:
        return x[0]
    if isinstance(x, list) and len(x) == 0:
        return None
    return x