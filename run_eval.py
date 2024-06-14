import os
from legent import Environment, Action, ActionFinish, Observation, store_json, ResetInfo, save_image, time_string
from legent.action.action import Action, ActionFinish
from legent.utils.io import log_green
import argparse
from predicate import build_predicate, get_feedback
from task import get_task_settings
from agent import *


def run_eval(agent, max_steps, max_images, port, eval_folder, save_path, task_settings, task_ids, sync):
    
    run_args = {"agent": agent, "max_steps": max_steps, "max_images": max_images, "max_images_history": max_images - 1}
    MAX_STEPS = max_steps
    MAX_IMAGE_HISTORY = max_images - 1

    eval_folder = os.path.abspath(eval_folder)

    if not task_settings:
        task_settings = get_task_settings(eval_folder)
    if not task_ids:
        task_ids = list(range(len(task_settings)))

    print(len(task_settings), "tasks")
    store_json(task_settings, f"task_settings.json")

    failed_cases = []
    success_cases = []

    env = Environment(env_path="auto", action_mode=1, camera_resolution_width=448, camera_resolution_height=448, camera_field_of_view=90, run_options={"port": port}, use_animation=False, rendering_options={"use_default_light": 1, "style": 0})

    if agent == "human":
        agent = AgentHuman(None if sync else env)  # 如果想要手动操作，"评测人类的性能"，可以使用这个
    if agent == "gemini-pro":
        agent = AgentGemini(None if sync else env)  # 如果带上env参数，就是异步的，人还可以操作环境前端界面
    elif agent == "gpt-4o":
        agent = AgentGPT4V(None if sync else env)

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
    try:
        for task_i in task_ids:

            print("\n" + "==" * 8 + f"Start episode {task_i}" + "==" * 8)
            print(task_i, task_settings[task_i]["scene_file"])
            task_setting = task_settings[task_i]
            print(task_setting["task"])
            print("Predicates:", task_setting["predicates"])
            agent.start(task_setting["task"])
            obs: Observation = env.reset(ResetInfo(scene=task_setting["scene"]))

            predicate = build_predicate(task_setting["predicates"], obs)

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
            while step < MAX_STEPS:
                # break
                if step == MAX_STEPS - 1:
                    action: Action = agent.act(obs.image, feedback, options)
                else:
                    action: Action = agent.act(obs.image, feedback, options)

                if action.action_choice < 0:
                    log_green(f"error occurred when evaluating {task_i}")
                    if agent.model_name == "gemini-pro": # server error等问题，不是模型的问题，停止评测
                        raise
                response = action.text
                action.text = ""
                obs = env.step(action)

                # 获取选项和反馈信息
                new_options = obs.game_states["option_mode_info"]["options"]
                # success_calculated_by_env = obs.game_states["option_mode_info"]["success"]
                feedback = get_feedback(options[action.action_choice], prev_obs, obs)
                prev_obs = obs

                save_image(obs.image, f"{traj_save_dir}/{step:04d}.png")
                print(f"step {step}, action: {action.action_choice}. {options[action.action_choice]}\n")
                done, info = predicate.task_done(action, obs, options, task_setting)

                store_json({"step": step, "options": options, "action_choice": action.action_choice, "action": options[action.action_choice], "response": response, "done_after_action": done, "info_after_action": info}, f"{traj_save_dir}/{step:04d}a.json")

                options = new_options
                print(options)

                step += 1
                if done == 1:
                    success_count += 1
                    print("Task accomplished.")
                if isinstance(action, ActionFinish) or action.text != "" or done != 0:
                    save_image(obs.image, f"{traj_save_dir}/{step:04d}.png")
                    break
            if done != 1:
                failed_cases.append(task_i)
                print("Task failed.")
            else:
                success_cases.append(task_i)
                
            log_green(f"success rate: {success_count}/{len(success_cases)+len(failed_cases)} of {len(task_settings)}")
            result = {"Success Rate": f"{success_count}/{len(success_cases)+len(failed_cases)}", "test cases": task_ids, "failed cases": failed_cases, "success cases": success_cases}
            print(result)
            store_json(result, f"{save_path}/result_temp.json")
    except Exception as e:
        result = {"Success Rate": f"{success_count}/{len(success_cases)+len(failed_cases)}", "test cases": task_ids, "failed cases": failed_cases, "success cases": success_cases}
        print(result)
        store_json(failed_cases, f"{save_path}/partial_results.json")
        raise e
    finally:
        env.close()
    result = {"Success Rate": f"{success_count}/{len(task_ids)}", "test cases": task_ids, "failed cases": failed_cases, "success cases": success_cases}
    print(result)
    store_json(result, f"{save_path}/result.json")


if __name__ == "__main__":
    # python run_eval.py --agent gpt-4o --max_steps 25 --max_images 25 --port 50054
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
    args = parser.parse_args()
    task_ids = None
    if args.test_case_start != -1 and args.test_case_end != -1:
        task_ids = list(range(args.test_case_start, args.test_case_end))
    run_eval(args.agent, args.max_steps, args.max_images, args.port, args.eval_folder, args.save_path, None, task_ids, args.sync)
