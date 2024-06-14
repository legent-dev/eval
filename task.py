import os
from legent import load_json, unpack_scenes


def get_task_settings(eval_folder):
    scenes_zip = [file for file in os.listdir(eval_folder) if file.endswith(".zip")]
    if len(scenes_zip) == 0:
        scenes_zip = [file for file in os.listdir(eval_folder) if os.path.isdir(f"{eval_folder}/{file}") and file != "results"]
    scene_path_to_scene = {}
    for scene_zip in scenes_zip:
        unpack_scenes(f"{eval_folder}/{scene_zip}")
        scene_dir_relative = scene_zip.rsplit(".", maxsplit=1)[0]
        scene_dir = f"{eval_folder}/{scene_dir_relative}"

        scene_files = [file for file in os.listdir(scene_dir) if file.endswith(".json") and not file.endswith("_relative.json")]
        for scene_file in scene_files:
            scene = load_json(f"{scene_dir}/{scene_file}")
            scene["player"]["prefab"] = "null"
            scene_path_to_scene[f"{scene_dir_relative}/{scene_file}"] = scene
            # print(f"{scene_dir_relative}/{scene_file}")
            # print(f"{scene_dir}/{scene_file}")

    def get_scene_by_path(path):
        import copy

        path = "/".join(path.split("/")[-2:])
        return copy.deepcopy(scene_path_to_scene[path])

    task_settings = []
    # files = find_files_by_extension(eval_folder, ".json", recursive=False)
    files = [f"{eval_folder}/{file}" for file in ["livingroom.json", "bedroom.json", "two_room.json", "three_room.json", "four_room.json"]]

    for file in files:
        # print(file)
        tasks = load_json(file)
        if "QA" in tasks:
            for sample in tasks["QA"]:
                sample["type"] = "QA"
        if "ACTION" in tasks:
            for sample in tasks["ACTION"]:
                sample["type"] = "ACTION"

        for sample in tasks["QA"] + tasks["ACTION"]:
            qa = sample["type"] == "QA"

            # Process scene
            scene = get_scene_by_path(sample["scene"])
            # add object_of_interest
            for object_id in sample["object_id"]:
                scene["instances"][object_id]["of_interest"] = True
            # add options
            # NOTE: 这个任务需要加一个抬头动作
            if sample["task"] == "Please help me move my laptops off the tall dark brown chest of drawers with black drawer pulls.":
                sample["options"].append("look upward")
                sample["options"].append("look downward")

            options = []
            for option in sample["options"]:
                if qa:
                    assert ":" not in option
                    options.append({"description": f'answer "{option}"', "object_ids": []})
                else:
                    # NOTE：有一个标的不统一，暂时改成grab
                    if option.startswith("pick up"):
                        option = option.replace("pick up", "grab")
                        print(option)

                    if ":" in option:
                        description, object_ids = option.split(":")
                        options.append({"description": description, "object_ids": object_ids.split(",")})
                    else:
                        options.append({"description": option, "object_ids": []})
            scene["options"] = options

            if qa:
                task_description = f"Question: {sample['task']}"
                scene["task"] = task_description

                assert len(sample["answer"]) == 1
                answer = options[sample["answer"][0] - 1]["description"]

                predicates = [f"choose {answer}"]
                scene["predicates"] = [{"predicate": "choose", "content": answer, "object_ids": []}]
            else:

                # NOTE: 这个任务 ['noton 33'] 要改一下
                if sample["task"] == "Clear the folding chair of all objects.":
                    sample["predicates"][0] = "noton 34 37 38 33"
                if sample["task"] == "Clear the bedside table of all things.":
                    sample["predicates"][0] = "noton 16 15"
                if sample["task"] == "Take out everything from the bathroom sink":
                    sample["predicates"][0] = "noton 42 43 44 41"
                if sample["task"] == "Clear the round wooden table of all objects.":
                    sample["predicates"][0] = "noton 36 35"

                task_description = f"Command: {sample['task']}"
                scene["task"] = task_description

                assert len(sample["predicates"]) == 1, sample["predicates"]
                predicate = sample["predicates"][0]
                # NOTE: 这个标错了
                if predicate.startswith("not on"):
                    predicate = predicate.replace("not on", "noton")
                predicates = [predicate]
                # print(len(task_settings), predicate)
                splits = predicate.split(" ")
                scene["predicates"] = [{"predicate": splits[0], "content": "", "object_ids": [int(_id) for _id in splits[1:]]}]

            task_setting = {"scene": scene, "task": task_description, "predicates": predicates, "type": sample["type"], "scene_file": sample["scene"], "rendering_options": {"use_default_light": 1, "style": 0}}
            task_settings.append(task_setting)

    return task_settings
