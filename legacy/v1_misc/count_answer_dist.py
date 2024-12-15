
from legent import load_json, store_json
import os
from pprint import pprint

# list all files in the directory
dir = "F:/Downloads/tasks1107"
answer_dist = {i: [] for i in range(0, 8)}
scenes = set()

# iterate over all files recursively
for root, dirs, files in os.walk(dir):
    for file in files:
        if file.endswith(".json"):
            # load the json file
            data = load_json(os.path.join(root, file))
            
            count_scene = False
            if count_scene:
                scene = file.split("-")[2]
                scene = data["scene_name"]
                print(scene)
                scenes.add(scene)
                continue
            # count the number of answers
            options = [option["option_text"] for option in data["options"]]
            options = [option["option_text"] for option in data["options"] if option["option_type"] != "Answer"]
            options = [option["option_text"] for option in data["options"]]
            if options:
                
                print(data["task_text"])
                print(options)
                print()
            continue
            answer = data["predicates"][0]["right_answer_content"]
            # index of answer in options
            answer_index = options.index(answer)
            answer_dist[answer_index].append(file[:-5])
            if answer_index == 3:
                print(file[:-5])
            # s = "task-20241107064051-four_rooms_5_scene_4-Count_all_the_pink_objects_in_the_living_room_"
            # if s in file:
            #     print(options)
            #     print(answer)
            #     print(options.index(answer))
            # print(data["task_text"], answer_index)
        
#pprint(answer_dist)
answer_dist = {k: len(v) for k, v in answer_dist.items()}
print(answer_dist)
print(len(scenes))
# 1 