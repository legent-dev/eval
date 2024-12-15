from legent import load_json, store_json
import os
from pprint import pprint
import numpy as np

# list all files in the directory
dir = "F:/Downloads/tasks1111_0807"
answer_dist = {i: [] for i in range(0, 8)}
scenes = set()

cases = load_json("F:/Downloads/index2json_final_1111.json")
cases = {cases[k].split("/")[1]: k for k in cases}

num = 0
lines = {}

# iterate over all files recursively
for root, dirs, files in os.walk(dir):
    for file in files:
        # if file in cases:
        #     cases.pop(file)
        #     num+=1
        
        if file.endswith(".json"):
            # load the json file
            data = load_json(os.path.join(root, file))
            # for option in data["options"]:
            #     if option["option_type"] != "Answer":
            #         print(option["option_text"])
            # continue
            task_type = root.split("\\")[-1]
            if task_type not in lines:
                lines[task_type] = []
            lines[task_type].append(data["task_text"])
            
            
            continue
            points = data["special_points"]
            names = [point["name"] for point in points if point["type"] == "navigation"]
            points = [np.array([point["position"][0], point["position"][2]]) for point in points if point["type"] == "navigation"]
            # check if there are duplicate points(very near)
            has_dup = False
            for i in range(len(points)):
                for j in range(i + 1, len(points)):
                    if np.linalg.norm(points[i] - points[j]) < 0.3:
                        if has_dup == False:
                            print("")
                            print(root, file)
                            has_dup = True
                        print(names[i], names[j])
# print(cases)
# print(num)
#store_json(lines, "task_texts.json")