from legent import (
    Environment,
    ResetInfo,
    generate_scene,
    TakePhotoWithVisiblityInfo,
    store_json,
)
import os
import json
import pandas as pd


# 读取原始物体的名称-类别
def get_object_name_description(
    csv_file="/Users/daishiqi/Desktop/LEGENT-main/create_task/descriptions.json",
    csv2_file="/Users/daishiqi/Desktop/LEGENT-main/create_task/holodeck_assets.json"
):
    # TODO descriptions.json里有的物体描述在holodect_assets.json没有出现

    object_name_description = {}
    des2uid = {}
    with open(csv2_file, "r") as file:
        assets = json.load(file)
        # 构建 description - uid 字典对
        for asset in assets:
            if asset["description"] != '':
                des2uid[asset["description"]] = asset["uid"]
    with open(csv_file, "r") as file:
        data = json.load(file)
    data = data["descriptions"]
    for dic in data:
       object_name_description[dic["asset"]] = [dic["class_name"], dic["description"]]
        

    return object_name_description, des2uid  # dic{prefab:[object_category,object_description]} , description2uid


# 新版场景下获取所有物体信息
def get_scene_object_info_new(scene):
    origin_object_name_description, des2uid = get_object_name_description()
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
            try:
                object_category, object_description = origin_object_name_description[
                    dic["prefab"]
                ]
                object_uid = des2uid[object_description]
            except KeyError as e:
                print(e)
                # with open('create_task/keyerror.log', 'a') as log_file:
                #     log_file.write(f"KeyError: {e}\n")
                continue
        else:  # 新的物体
            object_category = dic["category"]
            object_description = dic["description"]
            if object_description in des2uid:
                object_uid = des2uid[object_description]
            else:
                object_uid = ""
        object_info[dic["index"]] = [object_category, object_description, object_uid]
    return (
        object_info,
        room_object_info,
    )  # dic{index:[object_category,object_description]}, dic{room:[object_index]}


def single_room_take_photos(scene_json_folder, save_dir, option):
    port = 50013
    env = Environment(env_path="auto", run_options={"port": port})

    try:
        for i in range(0, 1):
            scene_json = f"{scene_json_folder}/scene_{i}.json"  # 场景路径
            save_folder = f"{save_dir}/{option}/scene_{i}" # 生成任务文件夹路径
            os.makedirs(save_folder, exist_ok=True)

            # 载入事先构造好的场景
            with open(scene_json, "r", encoding="utf-8") as file:
                scene = json.load(file)

            # 改intensity
            scene["lights"][0]['intensity'] = 0.35
            print(f"\n\nscene loaded\n\n")
            photo_path = f"{save_folder}/photo.png"  # 图片路径

            """original view"""
            if option == "original":
                # position = [3.8, 2.6, 4.4]
                # rotation = [50, -135, 0]
                position = [0.2, 2.5, 0.2]
                rotation = [50, 45, 0]

                obs = env.reset(
                    ResetInfo(
                        scene,
                        api_calls=[
                            TakePhotoWithVisiblityInfo(
                                photo_path,
                                position,
                                rotation,
                                width=4096,
                                height=int(4096 * 90 / 120),
                                vertical_field_of_view=90,
                                rendering_type="",
                            )
                        ],
                    )
                )
            
            """topdown view"""
            if option == "topdown":
                def _remove_ceiling(scene):
                    # remove the ceiling
                    i = 0
                    while i < len(scene["floors"]):
                        if scene["floors"][i]["position"][1] > 0:
                            scene["floors"].pop(i)
                        else:
                            i += 1
                    return scene
                scene = _remove_ceiling(scene)
                position = scene["center"]
                rotation = [90, 0, 0]

                obs = env.reset(
                    ResetInfo(
                        scene,
                        api_calls=[
                            TakePhotoWithVisiblityInfo(
                                photo_path,
                                position,
                                rotation,
                                width=2048,
                                height=2048,
                                vertical_field_of_view=50,
                                rendering_type="",
                            )
                        ],
                    )
                )


            print(f"\n\nphoto taken\n\n")

            object_info, room_object_info = get_scene_object_info_new(
                scene
            )  # 场景中的所有物体信息 dic{index:category}

            store_json(object_info, f"{save_folder}/scene_object_info.json")
            store_json(room_object_info, f"{save_folder}/room_object_info.json")

            print(f"\n\nscene {i} finished\n\n")
    finally:
        env.close()

def get_prompt():

    pass


def main():
    scene_json_folder = "/Users/daishiqi/Desktop/LEGENT-main/场景待优化/eval_folder_20240614_0251/bedroom_18"
    save_dir = "/Users/daishiqi/Desktop/LEGENT-main/create_task/bedroom_18"
    option = "topdown" # ["topdown", "original"]

    single_room_take_photos(scene_json_folder, save_dir, option)
if __name__ == "__main__":
    main()