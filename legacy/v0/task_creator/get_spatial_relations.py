"""
This script demonstrates how to get spatial relations between objects in the scene.
Currently, the spatial relations include "on_what" and "in_what".
"""
from legent import Environment, ResetInfo, load_json, store_json
from legent.environment.env_utils import get_default_env_data_path
from legent.action.api import GetSpatialRelations
import os
import glob

# load the default scene
scene_folder = ""
task_folder = ""


env = Environment(env_path="auto")
for room_type in os.listdir(scene_folder):
    room_path = f"{scene_folder}/{room_type}"
    search_pattern = os.path.join(room_path, '**', 'scene_*.json')
    json_files = glob.glob(search_pattern, recursive=True)

    for json_file in json_files:
        if json_file.endswith("relative.json"):
            continue
        print(json_file)
        scene = load_json(json_file)
        try:
            obs = env.reset(ResetInfo(scene, api_calls=[GetSpatialRelations()]))
            info = obs.api_returns["object_relations"]
            scene_name = os.path.basename(json_file)[:-5]
            store_json(info, f"{task_folder}/{room_type}/{scene_name}/spatial_relations.json")
        except:
            env.close()
            env = Environment(env_path="auto")
env.close()

# json_file = "/Users/tuyuge/projects/eval-main/eval_folder_20240614_0251/three_rooms_5/scene_3.json"
# room_type = "three_rooms"
# scene = load_json(json_file)
# try:
#     obs = env.reset(ResetInfo(scene, api_calls=[GetSpatialRelations()]))
#     info = obs.api_returns["object_relations"]
#     scene_name = os.path.basename(json_file)[:-5]
#     store_json(info, f"{task_folder}/{room_type}/{scene_name}/spatial_relations.json")
#     print("file stored at: ", f"{task_folder}/{room_type}/{scene_name}/spatial_relations.json")
# except:
#     env.close()
