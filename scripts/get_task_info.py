import glob
import os
from legent import store_json

task_folder = "/data41/private/legent/eval/EmbodiedEvalData"

all_paths = glob.glob(os.path.join(f"{task_folder}/final_tasks", '**', '*.json'), recursive=True)

id2json = {}
json2type = {}
for i, path in enumerate(all_paths):
    json_name = '/'.join(path.split("/")[-2:])
    id2json[i] = json_name

# /data41/private/legent/eval/scripts
store_json(id2json, "/data41/private/legent/eval/scripts/index2json.json")
print(id2json)