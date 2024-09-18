import os
from legent import Environment, Action, ActionFinish, Observation, store_json, load_json, ResetInfo, save_image, time_string
from legent.utils.math import distance, vec_xz
from legent.action.action import Action, ActionFinish
from legent.utils.io import log_green, create_video
from legent.action.api import SetVideoRecordingPath, SaveSceneToGltf
import argparse
from predicate import build_predicate, get_feedback
from task import get_task_settings
from agent import *

use_video = False

def run_eval(agent, max_steps, max_images, port, eval_folder, save_path, task_settings, task_ids, sync, run_one_task_instance, run_all_task_instance):

    run_args = {"agent": agent, "max_steps": max_steps, "max_images": max_images, "max_images_history": max_images - 1}
    MAX_STEPS = max_steps
    MAX_IMAGE_HISTORY = max_images - 1

    eval_folder = os.path.abspath(eval_folder)
        
    # Start episode 86崩溃了
     
    if run_one_task_instance or run_all_task_instance:
        eval_folder = "eval_annotated_20240916_1946" # if run_all_task_instance else "generated_eval_folder"
        task_folder = eval_folder
        task_settings = []
        
        character2material = {asset["asset_id"]: asset for asset in load_json("mixamo_assets.json")["assets"]}
        if run_one_task_instance:
            all_paths = [run_one_task_instance]
        else:
            all_paths = [f"{task_folder}/{file}" for file in os.listdir(task_folder) if file.endswith(".json")]
        
        for path in all_paths:
            task_setting = {"scene_file":"", "task_raw":"","scene": {"agent":{}, "player":{"prefab": "null", "position":[0,-100,0], "rotation":[0,0,0]}}}
            task_setting["scene"]["task_instance"] = load_json(path)
            scene_path = task_setting["scene"]["task_instance"]["scene_path"]
            mixamo_path = scene_path.split("/Assets/")[0] + "/Assets/Mixamo"

            scene_path = scene_path.split("/")[-1]
            if os.path.exists(f"{task_folder}/scenes/AI2THOR/{scene_path}"):
                scene_path = f"{task_folder}/scenes/AI2THOR/{scene_path}"
            elif os.path.exists(f"{task_folder}/scenes/HSSD/{scene_path}"):
                scene_path = f"{task_folder}/scenes/HSSD/{scene_path}"
            elif os.path.exists(f"{task_folder}/scenes/ObjaverseSynthetic/{scene_path}"):
                scene_path = f"{task_folder}/scenes/ObjaverseSynthetic/{scene_path}"
            task_setting["scene"]["task_instance"]["scene_path"] = scene_path
            task_setting["scene_file"] = scene_path

            task_setting["task"] = task_setting["scene"]["task_instance"]["task_text"]
            print(scene_path, task_setting["task"])
            task_setting["scene"]["instances"] = [{
                "prefab":task_setting["scene"]["task_instance"]["scene_path"],

                "position": [0,0,0],
                "rotation": [0,0,0],
                "scale": [1,1,1],
                "parent": 0,
                "type": "kinematic"
            }]
            if "humans" in task_setting["scene"]["task_instance"]:
                for human in task_setting["scene"]["task_instance"]["humans"]:
                    mesh_materials = character2material[human["asset"]+".fbx"]["mesh_materials"]
                    for mesh_material in mesh_materials:
                        for material in mesh_material["materials"]:
                            material["base_map"] = mixamo_path+"/Textures/"+material["base_map"].split("/")[-1]
                            material["normal_map"] = mixamo_path+"/Textures/"+material["normal_map"].split("/")[-1]
                            print(material["base_map"], material["normal_map"])
                    task_setting["scene"]["instances"].append({
                        "prefab": f"{mixamo_path}/{human['asset']}.fbx",
                        "position": human["human_position"],
                        "rotation": human["human_rotation"],
                        "scale": [1,1,1],
                        "parent": 0,
                        "type": "human",
                        "mesh_materials": mesh_materials
                    })
            task_setting["scene"]["walls"] = []
            task_setting["scene"]["floors"] = []
            task_setting["scene"]["agent"]["position"] = task_setting["scene"]["task_instance"]["agent_position"]
            task_setting["scene"]["agent"]["rotation"] = task_setting["scene"]["task_instance"]["agent_rotation"]

            for option in task_setting["scene"]["task_instance"]["options"]:
                if option["option_type"] == "Answer":
                    option["option_text"] =  f"answer \"{option['option_text']}\""
            for predicate in task_setting["scene"]["task_instance"]["predicates"]:
                if predicate["predicate_type"] == "choose":
                    predicate["right_answer_content"] = f"answer \"{predicate['right_answer_content']}\""
            task_settings.append(task_setting)

        if task_ids is None:
            task_ids = [0]
        task_ids = list(range(min(task_ids), len(task_settings)))
    else:
        if not task_settings:
            task_settings = get_task_settings(eval_folder)
            for task_setting in task_settings:
                for instance in task_setting["scene"]["instances"]:
                    if instance["prefab"].endswith(".fbx"):
                        instance["prefab"] = instance["prefab"].replace(".fbx", ".glb")
                        instance["scale"] = [1, 1, 1]
                        instance["rotation"][1] += 180
                        del instance["mesh_materials"]
        if not task_ids:
            task_ids = list(range(len(task_settings)))

    print(len(task_settings), "tasks")
    store_json(task_settings, f"task_settings.json")
    
    def save_to_csv():
        tasks_text = []
        template_to_task = {}
        for i in task_ids:
            setting = task_settings[i]
            # options = '/'.join([op["description"] for op in setting["scene"]["options"]])
            options = '/'.join([op for op in setting["task_raw"]["options"]])
            assert len(setting["scene"]["predicates"]) == 1
            pred = setting["scene"]["predicates"][0]
            predicate = pred["predicate"]+" "+pred["content"]+" "+'，'.join([str(j) for j in pred["object_ids"]])
            template = setting['task_raw']["template"].replace(",","，")
            if template not in template_to_task:
                template_to_task[template] = []
            # remove all ,options
            template, setting["task"], options, predicate = template.replace(",","，"), setting["task"].replace(",","，"), options.replace(",","，"), predicate.replace(",","，")
            text = template+","+setting["task"]+","+options+","+predicate
            template_to_task[template].append(text)
            tasks_text.append(text)
        with open(f"task_texts.csv", "w") as f:
            for template, tasks in template_to_task.items():
                for task in tasks:
                    f.write(f"{task}\n")
        exit(0)
    failed_cases = []
    success_cases = []

    path = "C:/Users/cheng/Desktop/LIGENT_dev/.legent/env/client/LEGENT-win-202406140317"
    path = "C:/users/cheng/desktop/ligent_dev/.legent/env/client/LEGENT-win-202408261101"
    path = "C:/Users/cheng/UnityProjects/thyplaymate/build/win-20240827"
    env = Environment(env_path="auto", action_mode=1, camera_resolution_width=448, camera_resolution_height=448, camera_field_of_view=90, run_options={"port": port}, use_animation=use_video, rendering_options={"use_default_light": 1, "style": 0})

    if agent == "human":
        agent = AgentHuman(env)  # 如果想要手动操作，"评测人类的性能"，可以使用这个
    if agent == "gemini-pro":
        agent = AgentGemini(None if sync else env)  # 如果带上env参数，就是异步的，人还可以操作环境前端界面
    if agent == "gemini-flash":
        agent = AgentGemini(None if sync else env, True)  # 如果带上env参数，就是异步的，人还可以操作环境前端界面
    elif agent == "gpt-4o":
        agent = AgentGPT4V(None if sync else env)
    elif agent == "rotate":
        agent = AgentRotate(env)
    elif agent == "random":
        agent = AgentRandom(env)

    # TODO: Change the agent to your agent
    # agent = YourAgent(env)
    # agent = YourAgentSimple(env)

    agent.max_steps = MAX_STEPS
    agent.max_image_history = MAX_IMAGE_HISTORY
    success_count = 0

    if not save_path:
        save_path = f"{eval_folder}/results/{time_string()}-{agent.model_name}-{max_images}"
    os.makedirs(save_path)
    store_json(task_ids, f"{save_path}/task_ids.json")
    store_json(run_args, f"{save_path}/run_args.json")
    def save_all_scenes_to_gltf():
        used_scenes = set()
        inspect_only = False
        for task_i in task_ids:
            task_setting = task_settings[task_i]
            file = task_setting["scene_file"]
            number = int(file.split("/")[-1].split(".")[0].split("_")[-1])
            # if "bedroom" in file or "livingroom" in file or "two" in file:
            #     continue
            # if number<=3:
            #     continue
            # if not ("two" in file and number==1):
            #     continue 
            # if not ("two" in file):
            #     continue
            # if inspect_only:
            #     if not ("living" in file and number==0):
            #         continue 
            #     # if not ("four" in file and number==1):
            #     #     continue 
            if file in used_scenes:
                continue
            
            instances = task_setting["scene"]["instances"]
            new_instances = []
            for i, instance in enumerate(instances):
                pos = instance["position"]
                if pos[1] < -1 or pos[1] > 4 or pos[0] < -50 or pos[0] > 50 or pos[2] < -50 or pos[2] > 50:
                    print(instance["prefab"], instance["position"])
                    continue
                instance["object_identifier_for_evaluation"] = "identifier" + str(i)
                new_instances.append(instance)
                
                # QuickHull coplanar!
                # if "09fad6a11f8b459d99d22f83dda714b7.glb" in instance["prefab"]:
                #     continue
            task_setting["scene"]["instances"] = new_instances

            used_scenes.add(file)
            
            # use gltFast, gltFast需要旋转180度
            if not inspect_only or True:
                for instance in task_setting["scene"]["instances"]:
                    if instance["prefab"].endswith(".glb"):
                        instance["rotation"][1] +=180
            dir_and_file = '/'.join(file.split("/")[-2:]).split(".")[0]
            if os.path.exists(f"F:/Downloads/EmaBench_EMNLP_scenes/{dir_and_file.replace('/', '_')}.glb"):
                print(f"F:/Downloads/EmaBench_EMNLP_scenes/{dir_and_file.replace('/', '_')}.glb exists")
                continue
            # if dir_and_file.replace('/', '_') != "livingroom_15_scene_13":
            #     continue
            env.reset(ResetInfo(scene=task_setting["scene"]))
            for i in range(180):
                env.step()
                print(".", end="",flush=True)
            if inspect_only:
                while True:
                    env.step(Action())
            else:
                # os.makedirs(f"F:/Downloads/EmaBench_EMNLP_scenes/"+dir_and_file.split("/")[0], exist_ok=True)
                # path = f"F:/Downloads/EmaBench_EMNLP_scenes/{dir_and_file}.glb"
                os.makedirs(f"F:/Downloads/EmaBench_EMNLP_scenes", exist_ok=True)
                path = f"F:/Downloads/EmaBench_EMNLP_scenes/{dir_and_file.replace('/', '_')}.glb"
                env.step(Action(api_calls=[SaveSceneToGltf(path)]))
        raise
    
    try:
        # save_all_scenes_to_gltf()
        for task_i in task_ids:

            print("\n" + "==" * 8 + f"Start episode {task_i}" + "==" * 8)
            # if task_i < 86:
            #     continue
            print(task_i, task_settings[task_i]["scene_file"])
            task_setting = task_settings[task_i]
            # for wall in task_setting["scene"]["walls"]:
            #     wall['material'] = "F:/Downloads/SourceTextures/SourceTextures/RoboTHOR_Wall_Panel_Fabric_Mat.png"
            # task_setting["scene"]["floors"][0]['material'] = "F:/Downloads/SourceTextures/SourceTextures/TexturesCom_MarbleNoisy0062_1_seamless_S.png"
            # task_setting["scene"]["floors"][1]['material'] = "F:/Downloads/SourceTextures/SourceTextures/TexturesCom_WoodFine0038_1_seamless_albedo_S.png"

            agent.start(task_setting["task"])
            # api_calls = [SetVideoRecordingPath("eval_video")] if use_video else []
            # 初始化不需要录制视频
            api_calls = []
                
            print(task_setting["task"])
            obs: Observation = env.reset(ResetInfo(scene=task_setting["scene"], api_calls=api_calls))
            if run_one_task_instance or run_all_task_instance:
                task_setting["predicates"] = obs.game_states["option_mode_info"]["predicates"]
                # replace multiple spaces with one space
                for i in range(len(task_setting["predicates"])):
                    import re
                    task_setting["predicates"][i] = re.sub(r"\s+", " ", task_setting["predicates"][i])
                print(task_setting["scene"]["task_instance"]["task_text"])
            print("Predicates:", task_setting["predicates"])
            pred_list = build_predicate(task_setting["predicates"], obs, old_version=not run_one_task_instance and not run_all_task_instance)

            options = obs.game_states["option_mode_info"]["options"]
            feedback = None
            prev_obs = obs
            print(options)

            traj_save_dir = f"{save_path}/traj{task_i:04d}"
            os.makedirs(traj_save_dir)
            store_json(task_setting["task_raw"], f"{traj_save_dir}/task_raw.json")
            store_json(task_setting, f"{traj_save_dir}/task.json")
            step = 0
            done = 0
            save_image(obs.image, f"{traj_save_dir}/{step:04d}.png")

            stuck_count = 0
            MAX_STAY_COUNT = 100 # TODO: add max stay
            stuck_pos = obs.game_states["agent"]["position"]
            while step < MAX_STEPS:
                # break
                if step == MAX_STEPS - 1:
                    action: Action = agent.act(obs.image, feedback, options)
                else:
                    action: Action = agent.act(obs.image, feedback, options)

                if action.action_choice < 0:
                    log_green(f"error occurred when evaluating {task_i}")
                    if agent.model_name == "gemini-pro":  # server error等问题，不是模型的问题，停止评测
                        raise
                response = action.text
                action.text = ""
                
                if use_video:
                    video_path = f"{traj_save_dir}/videos/{step+1:04d}"
                    action.api_calls = [SetVideoRecordingPath(video_path)]
                obs = env.step(action)
                
                if use_video:
                    if not os.path.exists(f"{video_path}/0.bmp"):
                        # create_video(f"{video_path}/{i:04d}", "bmp", f"{video_path}/video.mp4", 30, remove_images=True)
                        create_video([f"{traj_save_dir}/videos/{i:04d}" for i in range(1, step+2)], "bmp", f"{traj_save_dir}/{step+1:04d}.mp4", 30, remove_images=False)

                # 获取选项和反馈信息
                new_options = obs.game_states["option_mode_info"]["options"]
                # success_calculated_by_env = obs.game_states["option_mode_info"]["success"]
                feedback = get_feedback(options[action.action_choice], prev_obs, obs)
                feedback_content = obs.game_states["option_mode_info"]["feedback_content"]
                prev_obs = obs

                save_image(obs.image, f"{traj_save_dir}/{step+1:04d}.png")
                print(f"step {step}, action: {action.action_choice}. {options[action.action_choice]}, feedback: {feedback} - {feedback_content}\n")
                done = 1
                for predicate in pred_list:
                    _done, info = predicate.task_done(action, obs, options, task_setting)
                    if _done == -1:
                        done = -1
                        break
                    elif _done == 0:
                        done = 0

                if distance(vec_xz(stuck_pos), vec_xz(obs.game_states["agent"]["position"])) < 0.01:
                    stuck_count += 1
                else:
                    stuck_count = 0
                stuck_pos = obs.game_states["agent"]["position"]
                if stuck_count > MAX_STAY_COUNT:
                    done = -1

                store_json({"step": step, "options": options, "action_choice": action.action_choice, "action": options[action.action_choice], "response": response, "done_after_action": done, "info_after_action": info}, f"{traj_save_dir}/{step:04d}a.json")

                options = new_options
                print(options)

                step += 1
                if done == 1:
                    success_count += 1
                    log_green("Task accomplished.")
                if isinstance(action, ActionFinish) or action.text != "" or done != 0:
                    save_image(obs.image, f"{traj_save_dir}/{step:04d}.png")
                    break
            if done != 1:
                failed_cases.append(task_i)
                log_green("Task failed.")
            else:
                success_cases.append(task_i)

            log_green(f"success rate: {success_count}/{len(success_cases)+len(failed_cases)} of {len(task_settings)}")
            result = {"Success Rate": f"{success_count}/{len(success_cases)+len(failed_cases)}", "test cases": task_ids, "failed cases": failed_cases, "success cases": success_cases}
            if not run_one_task_instance:
                print(result)
            store_json(result, f"{save_path}/result_temp.json")
            if run_one_task_instance:
                break
    except Exception as e:
        result = {"Success Rate": f"{success_count}/{len(success_cases)+len(failed_cases)}", "test cases": task_ids, "failed cases": failed_cases, "success cases": success_cases}
        print(result)
        store_json(failed_cases, f"{save_path}/partial_results.json")
        raise e
    finally:
        env.close()
    result = {"Success Rate": f"{success_count}/{len(task_ids)}", "test cases": task_ids, "failed cases": failed_cases, "success cases": success_cases}
    if not run_one_task_instance:
        print(result)
    store_json(result, f"{save_path}/result.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", type=str, default="gpt-4o")  # "gpt-4o" "gemini-pro"
    parser.add_argument("--test_case_start", type=int, default=-1)  # 0-99
    parser.add_argument("--test_case_end", type=int, default=-1)
    parser.add_argument("--max_steps", type=int, default=25)
    parser.add_argument("--max_images", type=int, default=4)
    parser.add_argument("--port", type=int, default=50054)
    parser.add_argument("--eval_folder", type=str, default="./eval_folder_20240614_0251")
    parser.add_argument("--save_path", type=str, default=None)
    parser.add_argument("--sync", action="store_true")
    parser.add_argument("--run_one_task_instance", type=str, default=None)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    task_ids = None
    if args.test_case_start != -1 and args.test_case_end != -1:
        task_ids = list(range(args.test_case_start, args.test_case_end))
    run_eval(args.agent, args.max_steps, args.max_images, args.port, args.eval_folder, args.save_path, None, task_ids, args.sync, args.run_one_task_instance, args.all)

    # python run_eval.py --agent human --max_steps 2500 --max_images 25 --port 50058 --test_case_start=14 --test_case_end=100
    # python run_eval.py --agent gpt-4o --max_steps 25 --max_images 25 --port 50054 --sync
    # python run_eval.py --agent gemini-flash --max_steps 25 --max_images 25 --port 50058 --sync --test_case_start=0 --test_case_end=100
    # python run_eval.py --agent rotate --max_steps 25 --max_images 25 --port 50058 --sync --test_case_start=0 --test_case_end=100
    # python run_eval.py --agent random --max_steps 3 --max_images 25 --port 50051 --sync --test_case_start=0 --test_case_end=100
    
    # python run_eval.py --agent human --max_steps 30 --max_images 25 --port 50051 --sync --run_one_task_instance F:/UnityProjects/SceneProcessor/Assets/Tasks/task-20240912043700-102344094-Is_my_computer_on_in_the_bedroom_.json
    # python run_eval.py --agent human --max_steps 30 --max_images 25 --port 50051 --sync --run_one_task_instance F:/Downloads/task-20240913110854-FloorPlan11_physics-Check_what_s_on_the_other_side_of_the_bread__.json
    
    
    # python run_eval.py --agent human --max_steps 30 --max_images 25 --port 50051 --sync --run_one_task_instance F:/UnityProjects/SceneProcessor/Assets/Tasks/task-20240915152356-102344280-Reach_the_front_door_after_passing_through_the_hallway_and_turning_right__.json
    
    # 运行所有测例
    # python run_eval.py --agent human --max_steps 2500 --max_images 25 --port 50051 --test_case_start=0 --test_case_end=100 --all
    
    