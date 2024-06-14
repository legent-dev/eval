import os
from legent import Environment, Action, ActionFinish, Observation, store_json, ResetInfo, save_image, time_string
from legent.action.action import Action, ActionFinish
from legent.utils.io import log_green
import argparse
from predicate import build_predicate, get_feedback
from task import get_task_settings
from agent import *


def run_eval(agent, test_case_start, test_case_end, max_steps, max_images, port, save_path):

    MAX_STEPS = max_steps
    MAX_IMAGE_HISTORY = max_images - 1

    # TODO: change the path to your eval_folder
    eval_folder = "./eval_folder_20240614_0251"
    eval_folder = os.path.abspath(eval_folder)
    verbose = False  # 输出详细信息

    task_settings = get_task_settings(eval_folder)

    print(len(task_settings), "tasks")
    store_json(task_settings, f"task_settings.json")

    failed_cases = []

    env = Environment(env_path="auto", action_mode=1, camera_resolution_width=448, camera_resolution_height=448, camera_field_of_view=90, run_options={"port": port}, use_animation=False, rendering_options={"use_default_light": 1, "style": 0})

    if agent == "human":
        agent = AgentHuman(env)  # 如果想要手动操作，"评测人类的性能"，可以使用这个
    if agent == "gemini-pro":
        agent = AgentGemini(env)  # 如果带上env参数，就是异步的，人还可以操作环境前端界面
    elif agent == "gpt-4o":
        agent = AgentGPT4V(env)

    # TODO: Change the agent to your agent
    # agent = YourAgent(env)
    # agent = YourAgentSimple(env)

    agent.max_steps = MAX_STEPS
    agent.max_image_history = MAX_IMAGE_HISTORY
    success_count = 0

    if not save_path:
        save_path = f"{eval_folder}/results/{time_string()}-{agent.model_name}"
    try:
        for task_i in range(test_case_start, test_case_end):

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
            step = 0
            done = 0
            while step < MAX_STEPS:
                # break
                if step == MAX_STEPS - 1:
                    action: Action = agent.act(obs.image, feedback, options)
                else:
                    action: Action = agent.act(obs.image, feedback, options)

                if action.action_choice == -1:
                    log_green(f"error occurred when evaluating {task_i}")
                    raise  # 还是暂停评测，可能是模型输出错误，也有可能是server error不能误伤
                obs = env.step(action)

                # 获取选项和反馈信息
                new_options = obs.game_states["option_mode_info"]["options"]
                # success_calculated_by_env = obs.game_states["option_mode_info"]["success"]
                feedback = get_feedback(options[action.action_choice], prev_obs, obs)
                prev_obs = obs

                save_image(obs.image, f"{traj_save_dir}/{step:04d}.png")
                print(f"step {step}, action: {action.action_choice}. {options[action.action_choice]}\n")
                done, info = predicate.task_done(action, obs, options, task_setting)

                store_json({"step": step, "options": options, "action_choice": action.action_choice, "action": options[action.action_choice], "done_after_action": done, "info_after_action": info}, f"{traj_save_dir}/{step:04d}a.json")

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
            log_green(f"success rate: {success_count}/{task_i-test_case_start+1} of {len(task_settings)}")
            result = {"Success Rate": f"{success_count}/{task_i-test_case_start+1}", "test cases range": f"[{test_case_start} - {task_i+1})", "failed cases": failed_cases}
            print(result)
            store_json(result, f"{save_path}/result_temp.json")
    except Exception as e:
        result = {"Success Rate": f"{success_count}/{task_i-test_case_start}", "test cases range": f"[{test_case_start}, {task_i})", "failed cases": failed_cases}
        print(result)
        store_json(failed_cases, f"{save_path}/partial_results.json")
        raise e
    finally:
        env.close()
    result = {"Success Rate": f"{success_count}/{task_i-test_case_start+1}", "test cases range": f"[{test_case_start} - {task_i+1})", "failed cases": failed_cases}
    print(result)
    store_json(result, f"{save_path}/result.json")


if __name__ == "__main__":
    # python run_eval.py --agent gpt-4o --test_case_start 0 --max_steps 25 --max_images 4 --port 50054
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", type=str, default="")  # "gpt-4o" "gemini-pro"
    parser.add_argument("--test_case_start", type=int, default=0)  # 0-99
    parser.add_argument("--test_case_end", type=int, default=100)
    parser.add_argument("--max_steps", type=int, default=25)
    parser.add_argument("--max_images", type=int, default=4)
    parser.add_argument("--port", type=int, default=50054)
    parser.add_argument("--save_path", type=str, default=None)
    args = parser.parse_args()

    run_eval(args.agent, args.test_case_start, args.test_case_end, args.max_steps, args.max_images, args.port, args.save_path)
