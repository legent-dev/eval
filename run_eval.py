import os
from legent import Environment, Action, ActionFinish, Observation, store_json, load_json, ResetInfo, save_image, time_string
from legent.utils.math import distance, vec_xz
from legent.utils.io import log_green, create_video
from legent.action.api import SetVideoRecordingPath, SaveSceneToGltf
import argparse
from predicate import build_predicate, get_feedback
# from task import get_task_settings
import glob
import json
import sys
import re
from agent import *
import traceback

new_tasks_path = "index2json_0929.json"
task_to_type = {k: v.split("/")[0] for k, v in load_json(new_tasks_path).items()}

partial_final_results = set()  # get_qwen_partial_final_results()


def run_eval(agent, max_steps, max_images, port, eval_folder, save_path, task_settings, task_ids, sync, run_one_task_instance, run_all_task_instance, rerun, no_infer, use_video):
    run_args = {"agent": agent, "max_steps": max_steps, "max_images": max_images, "max_images_history": max_images - 1}
    MAX_STEPS = max_steps
    MAX_IMAGE_HISTORY = max_images - 1

    eval_folder = os.path.abspath(eval_folder)

    if run_one_task_instance or run_all_task_instance:
        eval_folder = "data"
        task_folder = eval_folder
        task_settings = []

        character2material = {asset["asset_id"]: asset for asset in load_json("mixamo_assets.json")["assets"]}
        if run_one_task_instance:
            all_paths = [run_one_task_instance]
        else:
            all_paths = glob.glob(os.path.join(f"{task_folder}/tasks", '**', '*.json'), recursive=True)

        for path in all_paths:
            with open(path, "r", encoding="utf-8") as f:
                line = ''.join(f.readlines()).strip()
            
            def process_special_scene(line):
                setting = json.loads(line)
                for scene_name in ["mini_project_bedroom_on_sketchfab", "ejemplo","richards_art_gallery_-_audio_tour"]:
                    if setting["scene_path"].endswith(scene_name+".glb"):
                        import re
                        replaced_text = re.sub("Sketchfab_model/", f'/', line)
                        return replaced_text
                return line
            line = process_special_scene(line)
            task_setting = {"scene_file": "", "task_raw": "", "scene": {"agent": {}, "player": {"prefab": "null", "position": [0, -100, 0], "rotation": [0, 0, 0]}}}
            task_setting["scene"]["task_instance"] = json.loads(line)
            scene_path = task_setting["scene"]["task_instance"]["scene_path"]
            mixamo_path = scene_path.split("/Assets/")[0] + "/Assets/Mixamo"
            if not os.path.exists(mixamo_path):
                mixamo_path = f"{task_folder}/scenes/Mixamo"
            mixamo_path = os.path.abspath(mixamo_path)

            if not os.path.exists(scene_path):
                scene_path = scene_path.split("/")[-1]
                if os.path.exists(f"{task_folder}/scenes/AI2THOR/{scene_path}"):
                    scene_path = f"{task_folder}/scenes/AI2THOR/{scene_path}"
                elif os.path.exists(f"{task_folder}/scenes/HSSD/{scene_path}"):
                    scene_path = f"{task_folder}/scenes/HSSD/{scene_path}"
                elif os.path.exists(f"{task_folder}/scenes/ObjaverseSynthetic/{scene_path}"):
                    scene_path = f"{task_folder}/scenes/ObjaverseSynthetic/{scene_path}"
                elif os.path.exists(f"{task_folder}/scenes/Sketchfab/{scene_path}"):
                    scene_path = f"{task_folder}/scenes/Sketchfab/{scene_path}"
            scene_path = os.path.abspath(scene_path)
            task_setting["scene"]["task_instance"]["scene_path"] = scene_path
            task_setting["scene_file"] = scene_path

            task_setting["task"] = task_setting["scene"]["task_instance"]["task_text"]
            print(scene_path, task_setting["task"])
            # scale = task_setting["scene"]["task_instance"]["scene_scale"]  # Unused variable
            task_setting["scene"]["instances"] = [{
                "prefab": task_setting["scene"]["task_instance"]["scene_path"],
                "position": [0, 0, 0],
                "rotation": [0, 0, 0],
                "scale": [1, 1, 1],  # gltFast动态导入的scale和Editor模式的scale不一样，有问题。只能用1,1,1
                "parent": 0,
                "type": "kinematic"
            }]
            if "humans" in task_setting["scene"]["task_instance"]:
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
            task_setting["scene"]["walls"] = []
            task_setting["scene"]["floors"] = []
            task_setting["scene"]["agent"]["position"] = task_setting["scene"]["task_instance"]["agent_position"]
            task_setting["scene"]["agent"]["rotation"] = task_setting["scene"]["task_instance"]["agent_rotation"]

            for option in task_setting["scene"]["task_instance"]["options"]:
                if option["option_type"] == "Answer":
                    option["option_text"] = f"answer \"{option['option_text']}\""
            for predicate in task_setting["scene"]["task_instance"]["predicates"]:
                if predicate["predicate_type"] == "choose":
                    predicate["right_answer_content"] = f"answer \"{predicate['right_answer_content']}\""
            task_setting["scene"]["interaction_distance"] = 1
            task_settings.append(task_setting)

        if task_ids is None:
            task_ids = [0]
        task_ids = list(range(min(task_ids), len(task_settings)))
    else:
        pass
        # if not task_settings:
        #     task_settings = get_task_settings(eval_folder)
        #     for task_setting in task_settings:
        #         for instance in task_setting["scene"]["instances"]:
        #             if instance["prefab"].endswith(".fbx"):
        #                 instance["prefab"] = instance["prefab"].replace(".fbx", ".glb")
        #                 instance["scale"] = [1, 1, 1]
        #                 instance["rotation"][1] += 180
        #                 del instance["mesh_materials"]
        # if not task_ids:
        #     task_ids = list(range(len(task_settings)))

    print(len(task_settings), "tasks")
    store_json(task_settings, f"task_settings.json")


    failed_cases = []
    success_cases = []
    error_cases = []

    # path = ...  # Removed unused path assignments
    path = "C:/Users/cheng/UnityProjects/thyplaymate/build/win-20241015"
    #path = "C:/Users/cheng/UnityProjects/thyplaymate/Builds/Windows/202410280606"
    #path = "C:/Users/cheng/UnityProjects/thyplaymate/build/win-20241028"
    path = "C:/Users/cheng/UnityProjects/thyplaymate/build/win-20241028-全有"
    path = "C:/Users/cheng/UnityProjects/thyplaymate/Builds/Windows/202410280631"
    path = "C:/Users/cheng/UnityProjects/thyplaymate/Builds/Windows/202410281017" # 这个非常神奇又不行了
    path = "C:/Users/cheng/UnityProjects/thyplaymate/Builds/Windows/202410290306"
    port = 50051
    env = Environment(env_path="auto",action_mode=1, camera_resolution_width=448, camera_resolution_height=448, camera_field_of_view=90, run_options={"port": port,"width":1024,"height":1024}, use_animation=use_video, rendering_options={"use_default_light": 1, "style": 0})

    if agent == "human":
        agent = AgentHuman(env)  # 如果想要手动操作，"评测人类的性能"，可以使用这个
    elif agent == "gemini-pro":
        # agent = AgentGemini(None if sync else env)  # 如果带上env参数，就是异步的，人还可以操作环境前端界面
        agent = AgentGeminiPro(None if sync else env)
    elif agent == "gemini-flash":
        agent = AgentGemini(None if sync else env, True)  # 如果带上env参数，就是异步的，人还可以操作环境前端界面
    elif agent == "gpt-4o":
        agent = AgentGPT4V(None if sync else env)
    elif agent == "gpt-4o-mini":
        agent = AgentGPT4V(None if sync else env, "gpt-4o-mini")
    elif agent == "qwen-vl-max":
        agent = AgentQwen(None if sync else env, "qwen-vl-max")
    elif agent == "qwen-vl-plus":
        agent = AgentQwen(None if sync else env, "qwen-vl-plus")
    elif agent == "rotate":
        agent = AgentRotate(env)
    elif agent == "random":
        agent = AgentRandom(env)
    else:
        raise ValueError(f"Unsupported agent type: {agent}")

    # TODO: Change the agent to your agent
    # agent = YourAgent(env)
    # agent = YourAgentSimple(env)

    agent.max_steps = MAX_STEPS
    agent.max_image_history = MAX_IMAGE_HISTORY
    success_count = 0

    if not save_path:
        save_path = f"{eval_folder}/results/{time_string()}-{agent.model_name}-step{max_steps}-image{max_images}-case{task_ids[0]}"
    os.makedirs(save_path)
    store_json(task_ids, f"{save_path}/task_ids.json")
    store_json(run_args, f"{save_path}/run_args.json")

    if not rerun:
        to_be_done_tasks = load_json(f"/data41/private/legent/eval/EmbodiedEvalData/final_results/{agent.model_name}/missed_tasks.json")
        to_be_done_tasks = [s.split("/")[-1] for s in to_be_done_tasks]
        log_green(f"About to run {len(to_be_done_tasks)} tasks")

    try:
        for task_i in task_ids:
            task_setting = task_settings[task_i]
            case_id = task_setting["scene"]["task_instance"]["savePath"].replace("\\", "/").split("/")[-1].split(".")[0]

            task_category = task_to_type[str(task_i)]
            # if task_category in ["AttributeQA", "SpatialQA"]:
            #     continue
            agent_result_folder = f"/data41/private/legent/eval/EmbodiedEvalData/final_results/{agent.model_name}/{task_category}/traj{task_i:04d}_{case_id}"
            
                  
            if no_infer:
                try:
                    try:
                        traj_list = load_json(f"{agent_result_folder}/traj.json")
                    except:
                        files = sorted(f for f in os.listdir(agent_result_folder) if f.endswith("a.json"))
                        traj_list = []
                        for file_name in files:
                            data = load_json(f"{agent_result_folder}/{file_name}")
                            result = {k:v for k,v in data.items() if k not in "payload"}
                            traj_list.append(result)
                    done_after_action = -1 if -1 in traj_list[-1]["predicates_done"] else 1 if all(x == 1 for x in traj_list[-1]["predicates_done"]) else 0
                    if traj_list[-1]["done_after_action"] == done_after_action:
                        log_green("already done")
                        continue
                except:
                    files = sorted(f for f in os.listdir(agent_result_folder) if f.endswith("a.json"))
                    traj_list = []
                    for file_name in files:
                        data = load_json(f"{agent_result_folder}/{file_name}")
                        result = {k:v for k,v in data.items() if k not in "payload"}
                        traj_list.append(result)
                
                # 从agent的结果文件夹中读取已有的结果 
                predicates = load_json(f"{agent_result_folder}/task.json")["predicates"]
                if len(predicates) == 1:
                    for traj in traj_list:
                        traj["predicates_done"] = [traj["done_after_action"]]
                    store_json(traj_list, f"{agent_result_folder}/traj.json")
                    continue

            if case_id + ".json" in partial_final_results:
                log_green(f"skip final results {case_id}, already done")
                continue
            if not rerun:
                if case_id + ".json" not in to_be_done_tasks:
                    continue

            print("\n" + "==" * 8 + f"Start episode {task_i}" + "==" * 8)

            agent.start(task_setting["task"])
            api_calls = []

            print(task_setting["task"])

            try:
                obs: Observation = env.reset(ResetInfo(scene=task_setting["scene"], api_calls=api_calls))
                step = 0
                done = 0
                frames = []

                stuck_count = 0
                MAX_STAY_COUNT = 100
                stuck_pos = obs.game_states["agent"]["position"]
                if run_one_task_instance or run_all_task_instance:
                    task_setting["predicates"] = obs.game_states["option_mode_info"]["predicates"]
                    for i in range(len(task_setting["predicates"])):
                        task_setting["predicates"][i] = re.sub(r"\s+", " ", task_setting["predicates"][i])
                    print(task_setting["scene"]["task_instance"]["task_text"])
                
                print("Predicates:", task_setting["predicates"])
                pred_list = build_predicate(task_setting["predicates"], obs, old_version=not run_one_task_instance and not run_all_task_instance)

                options = obs.game_states["option_mode_info"]["options"]
                feedback = None
                prev_obs = obs
                print(options)
                
                
                if not no_infer:
                    # 路径奇怪时，写视频文件会有问题
                    traj_save_dir = f"{save_path}/traj{task_i:04d}" # f"{save_path}/traj{task_i:04d}_{case_id}"

                    os.makedirs(traj_save_dir)
                    store_json(task_setting["task_raw"], f"{traj_save_dir}/task_raw.json")
                    store_json(task_setting, f"{traj_save_dir}/task.json")
                    
                    save_image(obs.image, f"{traj_save_dir}/{step:04d}.png")
                
                    
                while step < MAX_STEPS:
                    if no_infer:
                        if step == len(traj_list):
                            break
                        traj = traj_list[step]
                        action = Action()
                        action.text = traj["response"]
                        action.action_choice = traj["action_choice"]
                        if "action" in traj and traj["action"]:
                            action_text = traj["action"]
                        else:
                            # option是错的，就当什么也没做
                            action_text = "idle"
                            action.action_choice = 0
                        
                        obs = env.step(action)
                        new_options = obs.game_states["option_mode_info"]["options"]
                        

                        feedback = get_feedback(action_text, prev_obs, obs)
                        feedback_content = obs.game_states["option_mode_info"]["feedback_content"]
                        prev_obs = obs

                        feedback = feedback + (f": {feedback_content}" if feedback_content != "" else "")
                        done_list = [] # predicates的结果
                        for predicate in pred_list:
                            _done, info = predicate.task_done(action, obs, options, task_setting)
                            done_list.append(_done)
                        traj["feedback"] = feedback
                        traj["predicates_done"] = done_list
                        # Write the updated 'traj' back into the 'traj_list'
                        traj_list[step] = traj
                        options = new_options
                        step += 1
                    else:
                        if use_video:
                            agent.frames = frames
                        if step == MAX_STEPS - 1:
                            action = agent.act(obs.image, feedback, options)
                        else:
                            action = agent.act(obs.image, feedback, options)

                        if not action:
                            format_error = "api_crash"  # 如果api断掉了这条要重新测
                            store_json({"step": step, "options": options, "action_choice": None, "action_error": format_error, "response": "", "thought": "", "done_after_action": done, "info_after_action": "", "feedback": "", "time": time_string(), "payload": payload}, f"{traj_save_dir}/{step:04d}a.json")
                            break
                        else:
                            response = action.text

                        try:
                            thought = re.search(r'Thought: (.*?)\nChoice:', response, re.DOTALL).group(1).strip()
                        except:
                            thought = ""

                        if action.action_choice < 0:
                            if action.action_choice == -1:
                                format_error = "no option match"
                            else:
                                format_error = "option out of range"
                            log_green(format_error)
                            store_json({"step": step, "options": options, "action_choice": action.action_choice, "action_error": format_error, "response": response, "thought": thought, "done_after_action": done, "info_after_action": "", "feedback": "", "time": time_string(), "payload": payload}, f"{traj_save_dir}/{step:04d}a.json")

                            break

                        try:
                            payload = action.payload
                        except:
                            payload = ""
                        action.text = ""

                        if use_video:
                            video_path = f"{traj_save_dir}/frames_client/{step + 1:04d}_"
                            action.api_calls = [SetVideoRecordingPath(video_path)]
                        obs = env.step(action)

                        if use_video:
                            write_frames = True
                            write_video = True
                            
                            frames_folder = f"{traj_save_dir}/frames"
                            if write_frames:
                                start = time.time()
                                os.makedirs(frames_folder, exist_ok=True)
                                for i, frame in enumerate(obs.frames):
                                    save_image(frame, f"{frames_folder}/{step + 1:04d}_{i:04d}.png")
                                log_green(f"frames {len(obs.frames)}, time: {time.time() - start}")
                                
                            frames.extend(obs.frames)
                            if write_video:
                                create_video(frames, f"{traj_save_dir}/{step + 1:04d}.mp4", 30)
                                # image_paths = sorted([os.path.join(frames_folder, img) for img in os.listdir(frames_folder) if img.endswith(f".png")], key=lambda x: (len(x), x))
                                # create_video(image_paths, f"{traj_save_dir}/{step + 1:04d}_.mp4", 30)

                        new_options = obs.game_states["option_mode_info"]["options"]
                        feedback = get_feedback(options[action.action_choice], prev_obs, obs)
                        feedback_content = obs.game_states["option_mode_info"]["feedback_content"]
                        prev_obs = obs

                        save_image(obs.image, f"{traj_save_dir}/{step + 1:04d}.png")
                        print(f"step {step}, action: {action.action_choice}. {options[action.action_choice]}, feedback: {feedback} - {feedback_content}\n")

                        feedback = feedback + (f": {feedback_content}" if feedback_content != "" else "")
                        print("feedback:", feedback)
                        done = 1
                        done_list = [] # predicates的结果
                        for predicate in pred_list:
                            _done, info = predicate.task_done(action, obs, options, task_setting)
                            done_list.append(_done)
                            print(f"predicate: {type(predicate)}, {_done}")
                            # calcuate Goal-condition Success Rate
                            if _done == -1:
                                done = -1
                                break
                            elif _done == 0:
                                done = 0
                        
                        print(f"goal complete ratio: {done_list.count(1)} / {len(done_list)}")

                        if distance(vec_xz(stuck_pos), vec_xz(obs.game_states["agent"]["position"])) < 0.01:
                            stuck_count += 1
                        else:
                            stuck_count = 0
                        stuck_pos = obs.game_states["agent"]["position"]
                        if stuck_count > MAX_STAY_COUNT:
                            done = -1

                        
                        store_json({"step": step, "options": options, "action_choice": action.action_choice, "action": options[action.action_choice], "response": response, "thought": thought, "done_after_action": done, "info_after_action": info,  "feedback":  feedback, "predicates_done":done_list, "time":time_string(), "payload":payload}, f"{traj_save_dir}/{step:04d}a.json")

                        options = new_options
                        print(options)

                        step += 1
                        if done == 1:
                            success_count += 1
                            log_green("Task accomplished.")
                        if isinstance(action, ActionFinish) or action.text != "" or done != 0:
                            save_image(obs.image, f"{traj_save_dir}/{step:04d}.png")
                            break
                if not no_infer:
                    if done != 1:
                        failed_cases.append(task_i)
                        store_json({"result": "failed", "steps_taken": step}, f"{traj_save_dir}/result.json")
                        log_green("Task failed.")
                    else:
                        success_cases.append(task_i)
                        store_json({"result": "success", "steps_taken": step}, f"{traj_save_dir}/result.json")

                    log_green(f"success rate: {success_count}/{len(success_cases) + len(failed_cases)} of {len(task_settings)}")
                    result = {"Success Rate": f"{success_count}/{len(success_cases) + len(failed_cases)}", "test cases": task_ids, "failed cases": failed_cases, "success cases": success_cases}
                    if not run_one_task_instance:
                        print(result)
                    store_json(result, f"{save_path}/result_temp.json")
                    if run_one_task_instance:
                        break
                else:
                    # Save the updated traj_list back to the JSON file
                    try:
                        done_after_action = -1 if -1 in traj_list[-1]["predicates_done"] else 1 if all(x == 1 for x in traj_list[-1]["predicates_done"]) else 0
                        assert traj_list[-1]["done_after_action"] == done_after_action
                        store_json(traj_list, f"{agent_result_folder}/traj.json")
                    except:
                        with open(f'/data41/private/legent/eval/EmbodiedEvalData/final_results/{agent.model_name}/errors.jsonl', 'a') as jsonl_file:
                            error_info = {
                                'index': task_i,
                                "folder": agent_result_folder,
                                "traj_list": traj_list
                            }
                            jsonl_file.write(json.dumps(error_info) + '\n')
                        log_green(agent_result_folder)
                        # exit()
            except Exception as e:
                raise
                if "Game client exited" in str(e):
                    print("Game client exited. Terminating execution.")
                    sys.exit(1)
                with open(f'{save_path}/errors.jsonl', 'a') as jsonl_file:
                    error_info = {
                        'index': task_i,
                        'task': task_settings[task_i]["scene_file"],
                        'error': str(e),
                        'time': time_string()
                    }
                    jsonl_file.write(json.dumps(error_info) + '\n')
                error_cases.append(task_i)
                print(e)
                traceback.print_exc()
                env.close()
                env = Environment(env_path="auto", action_mode=1, camera_resolution_width=448, camera_resolution_height=448, camera_field_of_view=90, run_options={"port": port}, use_animation=use_video, rendering_options={"use_default_light": 1, "style": 0})
    except Exception as e:
        print(e)
        traceback.print_exc()
        if not no_infer:
            result = {"Success Rate": f"{success_count}/{len(task_ids) - len(error_cases)}", "test cases": task_ids, "failed cases": failed_cases, "success cases": success_cases, "error cases": error_cases}
            print(result)
            store_json(failed_cases, f"{save_path}/partial_results.json")
    finally:
        env.close()
    if not no_infer:
        result = {"Success Rate": f"{success_count}/{len(task_ids) - len(error_cases)}", "test cases": task_ids, "failed cases": failed_cases, "success cases": success_cases, "error cases": error_cases}
        if not run_one_task_instance:
            print(result)
        store_json(result, f"{save_path}/result.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", type=str, default="gpt-4o")
    parser.add_argument("--test_case_start", type=int, default=-1)
    parser.add_argument("--test_case_end", type=int, default=-1)
    parser.add_argument("--max_steps", type=int, default=24)
    parser.add_argument("--max_images", type=int, default=4)
    parser.add_argument("--port", type=int, default=50054)
    parser.add_argument("--eval_folder", type=str, default="./eval_folder_20240614_0251")
    parser.add_argument("--save_path", type=str, default=None)
    parser.add_argument("--sync", action="store_true")
    parser.add_argument("--run_one_task_instance", type=str, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--rerun", action="store_true")
    parser.add_argument("--no_infer", action="store_true")
    parser.add_argument("--use_video", action="store_true")
    args = parser.parse_args()
    task_ids = None
    if args.test_case_start != -1 and args.test_case_end != -1:
        task_ids = list(range(args.test_case_start, args.test_case_end))
    run_eval(args.agent, args.max_steps, args.max_images, args.port, args.eval_folder, args.save_path, None, task_ids, args.sync, args.run_one_task_instance, args.all, args.rerun, args.no_infer, args.use_video)
