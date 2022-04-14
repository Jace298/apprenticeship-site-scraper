# Randomly remove a piece of data.json
import json
import random

def loadJSON():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return {}

data = loadJSON()
delIndex = random.choice(list(data.keys()))
print(f"Removing {delIndex} from data.json")
del data[delIndex]
with open("data.json", "w") as f:
        json.dump(data, f, indent=2)