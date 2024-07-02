from legent import (
    Environment,
    ResetInfo,
    generate_scene,
    TakePhotoWithVisiblityInfo,
    store_json,
)
import os
import json
from scripts.gpt_api import get_response_new, get_response_4v
from scripts.get_object_info import (
    get_scene_object_info,
    get_ego_object_list,
    get_scene_object_info_new,
)
from scripts.prompt_create_task import (
    scene_to_description,
    description_to_task,
    description_to_task_QA,
    description_to_task_action,
)
import pandas as pd

# scene_index = 9  # 场景编号
option = 1  # 1:仅拍照 2:拍照+生成任务

env = Environment(env_path="auto")

task_num = 1  # 任务编号


try:
    for i in range(0, 2):

        scene_json = f"/Users/frank/Code/LEGENT/TASK/scene/one_room_2_scenes/scene_{i}.json"  # 场景路径
        save_folder = f"/Users/frank/Code/LEGENT/TASK/task/one_room_2_scenes/scene_{i}"  # 生成任务文件夹路径
        os.makedirs(save_folder, exist_ok=True)

        # 载入事先构造好的场景
        with open(scene_json, "r", encoding="utf-8") as file:
            scene = json.load(file)
        print(f"\n\nscene loaded\n\n")

        # position = [3.8, 2.6, 4.4]
        # rotation = [50, -135, 0]

        position = [0.2, 2.5, 0.2]
        rotation = [50, 45, 0]

        photo_path = f"{save_folder}/photo.png"  # 图片路径
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
        print(f"\n\nphoto taken\n\n")

        object_info, room_object_info = get_scene_object_info_new(
            scene
        )  # 场景中的所有物体信息 dic{index:category}
        store_json(object_info, f"{save_folder}/scene_object_info.json")
        store_json(room_object_info, f"{save_folder}/room_object_info.json")

        # if option == 2:
        #     print("\n\nstart to generate scene description\n\n")
        #     scene_description = scene_to_description(
        #         save_folder, object_info, room_object_info
        #     )  # 场景描述
        #     print("\n\n--------------scene_description--------------")
        #     print(scene_description)

        #     print("\n\nstart to generate task\n\n")
        #     task_QA = description_to_task_QA(
        #         scene_description, object_info, room_object_info
        #     )  # 生成QA类任务
        #     tasks_action = description_to_task_action(
        #         scene_description, object_info, room_object_info
        #     )  # 生成执行类任务

        #     print("\n\n-------------TASK QA-------------")
        #     print(task_QA)
        #     print("\n\n-------------TASK ACTION-------------")
        #     print(tasks_action)

        #     store_json(task_QA, f"{save_folder}/task_QA.json")
        #     store_json(tasks_action, f"{save_folder}/task_action.json")

        print(f"\n\nscene {i} finished\n\n")
finally:
    env.close()
