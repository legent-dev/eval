import re
import pandas as pd
import json


# 读取原始物体的名称-类别
def get_object_name_description(
    csv_file="/Users/frank/Code/LEGENT/object_info/descriptions.json",
):
    object_name_description = {}
    with open(csv_file, "r") as file:
        data = json.load(file)
    data = data["descriptions"]
    for dic in data:
        object_name_description[dic["asset"]] = [dic["class_name"], dic["description"]]
    return object_name_description  # dic{prefab:[object_category,object_description]}


# 获取场景中的所有物体信息
def get_scene_object_info(scene):
    object_name_description = get_object_name_description()
    instances = scene["instances"]
    object_info = {}
    index = 0  # 物体索引 scene["instances"]中第index个物体
    for dic in instances:
        object_name = re.findall(
            r"[A-Za-z]+", dic["prefab"].split("_")[1]
        )  # 提取出物体名称
        object_name = " ".join(object_name)
        # 如果涉及多房间还要处理door
        if object_name != "Floor" and object_name != "Wall":  # 不统计地板和墙
            object_info[index] = object_name_description[dic["prefab"]]
        index += 1
    return object_info  # dic{index:[object_name,object_description]}


# 新版场景下获取所有物体信息
def get_scene_object_info_new(scene):
    origin_object_name_description = get_object_name_description()
    instances = scene["instances"]
    object_info = {}  # 场景的所有物体信息
    room_object_info = {}  # 房间的物体信息
    for dic in instances:
        if "room_type" not in dic:  # 场景中的物体
            continue
        object_room = dic["room_type"]  # 物体所在房间
        room_object_info[object_room] = room_object_info.get(object_room, [])
        room_object_info[object_room].append(dic["index"])  # 对房间的物体进行索引
        if "description" not in dic:  # 旧的物体
            object_category, object_description = origin_object_name_description[
                dic["prefab"]
            ]
        else:  # 新的物体
            object_category = dic["category"]
            object_description = dic["description"]
        object_info[dic["index"]] = [object_category, object_description]
    return (
        object_info,
        room_object_info,
    )  # dic{index:[object_category,object_description]}, dic{room:[object_index]}


# 获取agent第一视角画面中的物体信息
def get_ego_object_list(visible_objects):
    object_info = {}
    for obj in visible_objects:
        object_name = re.findall(r"[A-Za-z]+", obj.split("_")[1])
        object_name = " ".join(object_name)
        if object_name != "Floor" and object_name != "Wall":
            object_info[object_name] = object_info.get(object_name, 0) + 1
    return object_info  # dic{object_name:object_num}
