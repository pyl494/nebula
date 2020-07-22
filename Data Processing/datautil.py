
def map(dataStructure, keys, data):
    for key in keys[:-1]:
        if not key in dataStructure:
            dataStructure[key] = {}
        
        dataStructure = dataStructure[key]
    dataStructure[keys[-1]] = data

def map_get(dataStructure, keys):
    out = dataStructure
    for key in keys[:-1]:
        if not key in dataStructure:
            out = None
            break
        
        out = dataStructure[key]

    if not out is None and keys[-1] in out:
        return out[keys[-1]]
    
    return None

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