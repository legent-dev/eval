import os
from legent import store_json, load_json
import re
import json

def process_special_scene(task_info):
    """Fix paths of some Sketchfab scenes."""
    for scene_name in ["mini_project_bedroom_on_sketchfab", "ejemplo","richards_art_gallery_-_audio_tour"]:
        if task_info["scene_path"].endswith(scene_name+".glb"):
            replaced_text = re.sub("Sketchfab_model/", f'/', json.dumps(task_info))
            return json.loads(replaced_text)
    return task_info


def get_scene_path(scene_path, scene_folder):
    """Resolves the scene path based on predefined folder locations."""
    scene_path = scene_path.split("/")[-1]
    print(scene_path)
    for folder in ["AI2THOR", "HSSD", "ObjaverseSynthetic", "Sketchfab"]:
        print(f"{scene_folder}/{folder}/{scene_path}")
        if os.path.exists(f"{scene_folder}/{folder}/{scene_path}"):
            scene_path = f"{scene_folder}/{folder}/{scene_path}"
            return os.path.abspath(scene_path)

def add_human_instances(task_setting, mixamo_path):
    """Adds human instances to the task setting based on human data."""
    if "humans" in task_setting["scene"]["task_instance"]:
        character2material = {asset["asset_id"]: asset for asset in load_json("data/scenes/mixamo_assets.json")["assets"]}
        for human in task_setting["scene"]["task_instance"]["humans"]:
            mesh_materials = character2material[human["asset"] + ".fbx"]["mesh_materials"]
            for mesh_material in mesh_materials:
                for material in mesh_material["materials"]:
                    material["base_map"] = mixamo_path + "/Textures/" + material["base_map"].split("/")[-1]
                    material["normal_map"] = mixamo_path + "/Textures/" + material["normal_map"].split("/")[-1]
            task_setting["scene"]["instances"].append({
                "prefab": f"{mixamo_path}/{human['asset']}.fbx",
                "position": human["human_position"],
                "rotation": human["human_rotation"],
                "scale": [1, 1, 1],
                "parent": 0,
                "type": "human",
                "mesh_materials": mesh_materials
            })

def process_options_and_predicates(task_setting):
    """Processes options and predicates in the task setting."""
    for option in task_setting["scene"]["task_instance"]["options"]:
        if option["option_type"] == "Answer":
            option["option_text"] = f"answer \"{option['option_text']}\""
    for predicate in task_setting["scene"]["task_instance"]["predicates"]:
        if predicate["predicate_type"] == "choose":
            predicate["right_answer_content"] = f"answer \"{predicate['right_answer_content']}\""

def create_task_setting(path, scene_folder):
    """Creates a task setting dictionary from a given file path."""
    task_info = load_json(path)
    
    line = process_special_scene(task_info)
    task_setting = {"scene_file": "", "task_raw": "", "scene": {"agent": {}, "player": {"prefab": "null", "position": [0, -100, 0], "rotation": [0, 0, 0]}}}
    task_setting["scene"]["task_instance"] = line
    scene_path = task_info["scene_path"]
    
    mixamo_path = os.path.abspath(scene_folder + "/Mixamo")
    scene_path = get_scene_path(scene_path, scene_folder)
    if not scene_path:
        raise FileNotFoundError(f"Scene path not found.")
    if not mixamo_path:
        raise FileNotFoundError(f"Mixamo path not found.")
    
    task_setting["scene"]["task_instance"]["scene_path"] = scene_path
    task_setting["scene_file"] = scene_path

    task_setting["task"] = task_setting["scene"]["task_instance"]["task_text"]

    task_setting["scene"]["instances"] = [{
        "prefab": task_setting["scene"]["task_instance"]["scene_path"],
        "position": [0, 0, 0],
        "rotation": [0, 0, 0],
        "scale": [1, 1, 1], 
        "parent": 0,
        "type": "kinematic"
    }]
    
    add_human_instances(task_setting, mixamo_path)
    
    task_setting["scene"]["walls"] = []
    task_setting["scene"]["floors"] = []
    task_setting["scene"]["agent"]["position"] = task_setting["scene"]["task_instance"]["agent_position"]
    task_setting["scene"]["agent"]["rotation"] = task_setting["scene"]["task_instance"]["agent_rotation"]

    process_options_and_predicates(task_setting)
    
    task_setting["scene"]["interaction_distance"] = 1
    return task_setting

def ensure_output_order(task_settings, index2json):
    """Ensures the output order of task settings based on index2json."""
    new_task_settings = []
    for index in index2json:
        for setting in task_settings:
            json_name = setting["scene"]["task_instance"]["savePath"].replace("\\","/").split("/")[-1]
            if index2json[index].split("/")[-1] == json_name:
                new_task_settings.append(setting)
    return new_task_settings

def process_task_settings(all_paths, scene_folder, index2json):
    """Processes task settings from a list of file paths."""
    task_settings = []
    for path in all_paths:
        task_settings.append(create_task_setting(path, scene_folder))

    task_settings = ensure_output_order(task_settings, index2json)
    # store_json(task_settings, f"data/tasks/task_settings.json")
    return task_settings