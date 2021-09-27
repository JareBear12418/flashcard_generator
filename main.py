import json
with open('data.json') as f:
    d = json.load(f)
    for i in d:
        if len(d[i]) == 0:
            continue
        print(d[i][-1]) 