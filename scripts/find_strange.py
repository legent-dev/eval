

import glob
import os
from legent import store_json, load_json

task_folder = "/data41/private/legent/eval/EmbodiedEvalData"

all_paths = glob.glob(os.path.join(f"{task_folder}/tasks", '**', '*.json'), recursive=True)

id2json = {}
json2type = {}
for i, path in enumerate(all_paths):
    print(i)
    json_name = '/'.join(path.split("/")[-2:])
    id2json[i] = json_name
    
    save_path = load_json(path)["savePath"].replace("\\", "/")
    a = json_name.split("/")[-1]
    b = '/'.join(save_path.split("/")[-1:])
    # if i==92:
    #     continue
    assert a == b, a+"\n"+b