import os
from legent import Environment, Action, Observation, load_json, ResetInfo, save_image
from legent.utils.io import log_green, create_video
from legent.action.api import SetVideoRecordingPath
import argparse
import re
from agent import *

def rerun_eval(agent_name, port, task_ids, use_video, model_name="human"):

    eval_folder = "data/tasks"
    new_tasks_path = f"{eval_folder}/index2json.json"
    task_to_type = {k: v.split("/")[0] for k, v in load_json(new_tasks_path).items()}
    task_settings = load_json(f"{eval_folder}/task_settings.json")

    env = Environment(env_path="auto",action_mode=1, camera_resolution_width=448, camera_resolution_height=448, camera_field_of_view=90, run_options={"port": port,"width":1024,"height":1024}, use_animation=use_video, rendering_options={"use_default_light": 1, "style": 0})
    agent = AgentRandom(env)
    agent.model_name = model_name
    
    try:
        for task_i in task_ids:
            task_setting = task_settings[task_i]
            case_id = task_setting["scene"]["task_instance"]["savePath"].replace("\\", "/").split("/")[-1].split(".")[0]
            task_category = task_to_type[str(task_i)]
            agent_result_folder = f"EmbodiedEvalData/final_results/{agent_name}/{task_category}/traj{task_i:04d}_{case_id}"
            traj_list = load_json(f"{agent_result_folder}/traj.json")

            print("\n" + "==" * 8 + f"Start episode {task_i}" + "==" * 8)

            agent.start(task_setting["task"])
            api_calls = []
            print(task_setting["task"])

            obs: Observation = env.reset(ResetInfo(scene=task_setting["scene"], api_calls=api_calls))
            step = 0
            frames = []

            task_setting["predicates"] = obs.game_states["option_mode_info"]["predicates"]
            for i in range(len(task_setting["predicates"])):
                task_setting["predicates"][i] = re.sub(r"\s+", " ", task_setting["predicates"][i])
            print(task_setting["scene"]["task_instance"]["task_text"])
            
            print("Predicates:", task_setting["predicates"])

            options = obs.game_states["option_mode_info"]["options"]
            print(options)

            while step < len(traj_list):
                if step == len(traj_list):
                    break
                traj = traj_list[step]
                action = Action()
                action.text = traj["response"]
                action.action_choice = traj["action_choice"]
                if "action" not in traj and traj["action"]:
                    action.action_choice = 0
                    
                if use_video:
                    video_path = f"{agent_result_folder}/frames_client/{step + 1:04d}_"
                    action.api_calls = [SetVideoRecordingPath(video_path)]
                    
                obs = env.step(action)
                
                if use_video:
                    write_frames = True
                    write_video = True
                    
                    frames_folder = f"{agent_result_folder}/frames"
                    if write_frames:
                        start = time.time()
                        os.makedirs(frames_folder, exist_ok=True)
                        for i, frame in enumerate(obs.frames):
                            save_image(frame, f"{frames_folder}/{step + 1:04d}_{i:04d}.png")
                        log_green(f"frames {len(obs.frames)}, time: {time.time() - start}")
                        
                    frames.extend(obs.frames)
                    if write_video:
                        create_video(frames, f"{agent_result_folder}/{step + 1:04d}.mp4", 30)
                        
                options = obs.game_states["option_mode_info"]["options"]
                step += 1
    except Exception as e:
        print(e)
    finally:
        env.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", type=str, default="gpt-4o")
    parser.add_argument("--test_case_start", type=int, default=-1)
    parser.add_argument("--test_case_end", type=int, default=-1)
    parser.add_argument("--port", type=int, default=50054)
    parser.add_argument("--use_video", action="store_true")
    args = parser.parse_args()
    
    if args.test_case_start != -1 and args.test_case_end != -1:
        task_ids = list(range(args.test_case_start, args.test_case_end))
    else:
        task_ids = []
        
    rerun_eval(args.agent, args.port, task_ids, args.use_video)
    
    # 用于拍demo视频
    # DISPLAY=:7 python record_video.py --agent human --port 53055 --use_video
    # for demo video
    # data = {
    #     "Nav": [76, 241, 179, 249, 287],
    #     "Attr": [82, 178, 221, 104, 213, 165, 130],
    #     "Obj": [5, 81, 103, 112, 209, 118, 319, 233],
    #     "SpatialQA": [113, 109, 263, 302],
    #     "Social": [27, 267, 315, 297]
    # }


    # task_ids = list(set(value for sublist in data.values() for value in sublist))
    # task_ids.sort()
