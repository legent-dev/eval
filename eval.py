import os
from legent import load_json, Action
from legent.dataset.controller import MAX_MOVE_DISTANCE, MAX_ROTATE_DEGREE
import requests

from legent import Environment, Observation, store_json, ResetInfo, load_json, save_image, unpack_scenes
import os
from legent.utils.config import EVAL_FOLDER
from legent import get_latest_folder_with_suffix, time_string, task_done, AgentClient, ActionFinish, Action, GPT4VAgentClient

from legent.utils.math import vec_xz, distance
from legent.action.action import Action
from PIL import Image
import io
from legent.action.action import parse_float, parse_string

PROMPT_SHARED = f"""You are a vision language assistant agent with high intelligence.
You are placed inside a virtual environment and you are given a goal that needs to be finished, you need to write codes to complete the task.
You can solve any complex tasks by decomposing them into subtasks and tackling them step by step, but you should only provide the action code for solving the very next subtask.
You need to perform the following actions to complete the tasks:
1. choose [number]: choose an answer.
2. move_forward [meters]: move forward a certain distance (max_meters={MAX_MOVE_DISTANCE:.1f}).
3. rotate_right [degrees]: Adjust the azimuth angle to change the view and direction. "degrees" can be any integers between -{MAX_ROTATE_DEGREE} and {MAX_ROTATE_DEGREE}, inclusive.
4. rotate_down [degrees]: Tilt the angle to adjust the view. "degrees" can be any integers between -{MAX_ROTATE_DEGREE} and {MAX_ROTATE_DEGREE}, inclusive.
5. grab
6. release

For example, if you want to choose the second option, you should write "choose 2". Do not output any other things including comment.
Your task is to answer the question or complete the command. If you have no enough information to answer the question, you can move and rotate the get more information.
"""


def action_to_string(action: Action):
    action_strings = []
    if action.teleport_forward:
        action_strings.append(f"move_forward {action.teleport_forward:.1f}")  # TODO: avoid move_forward(0.0)
    if action.rotate_right:
        action_strings.append(f"rotate_right {int(action.rotate_right)}")
    if action.rotate_down:
        action_strings.append(f"rotate_down {int(action.rotate_down)}")
    if action.grab:
        action_strings.append(f"grab")
    if action.text:
        action_strings.append(f"choose {action.text}")

    return ", ".join(action_strings)


def string_to_action(action_str: str):
    action = Action(use_teleport=True)
    for elem in action_str.split(", "):
        splits = elem.split(" ")
        if elem.startswith("move_forward"):
            action.teleport_forward = float(splits[1])
        elif elem.startswith("rotate_right"):
            action.rotate_right = float(splits[1])
        elif elem.startswith("rotate_down"):
            action.rotate_down = float(splits[1])
        elif elem.startswith("choose"):
            action.text = splits[1]
    return action


class AgentBase:
    def __init__(self, model_name: str) -> None:
        # init the api or model
        self.model_name = model_name
        self.images_history = []
        self.action_history = []
        self.max_history = 2
        self.task = ""

    def start(self, instruction):
        self.instruction = instruction
        self.images_history = []
        self.action_history = []

    def act(self, image):
        # call the api or perform model inference
        action = Action()

        self.images_history.append(image)
        self.action_history.append(action_to_string(action))

        return action


class AgentGPT4V(AgentBase):
    def __init__(self, api_key, base_url, instruction) -> None:
        super().__init__("gpt4v")

    def act(self, image):
        raise NotImplementedError


class AgentGemini(AgentBase):
    def __init__(self) -> None:
        super().__init__("gemini-pro")

    def act(self, image, extra_hint=""):
        action = Action()

        images = self.images_history
        if len(images) > self.max_history:
            images = images[-self.max_history :]
        actions = self.action_history
        if len(actions) > self.max_history:
            actions = actions[-self.max_history :]

        message = f"{PROMPT_SHARED}\nYour task:\n{self.instruction}\n\nHistory:\n{extra_hint}"
        for o, a in zip(images, actions):
            message += f"Image: <image> Action: {a}"  # <image> is a placeholder for the image
        message += "\nPlease output your next action apis"
        payload = {"message": message, "model": "pro"}  # model: flash or pro
        files = []
        for i, image_array in enumerate(images):
            # Convert NumPy array to PIL Image
            img = Image.fromarray(image_array)
            # Save the image to a buffer
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            files.append(("files", (f"image{i}.png", buf.read(), "image/png")))

        # files = [("files", (f"image{i}.png", image, "image/png")) for i, image in enumerate(images)]
        response = requests.post("http://146.190.166.36:8901/", files=files, data=payload).text
        print("response:", response.strip())
        try:
            action = string_to_action(response)
        except:
            action = Action()
            print("Wrong action format.")
        self.images_history.append(image)
        self.action_history.append(action_to_string(action))

        return action


agent = AgentGemini()
success_count = 0


COME_DONE_DISTANCE = 2.0


def task_done(task, action: Action, obs, task_setting):
    if task == "come":
        game_states = obs.game_states
        d = distance(vec_xz(game_states["agent"]["position"]), vec_xz(game_states["player"]["position"]))
        done = d < COME_DONE_DISTANCE
        return done, {"distance": d}
    elif task == "qa":
        done = action.text == task_setting["predicates"][0].split(" ")[1]
        return done, {}
    else:
        raise NotImplementedError


eval_folder = "F:/Downloads/eval_folder_example (1)"
save_path = f"{eval_folder}/results/{time_string()}-{agent.model_name}"

scenes = unpack_scenes(f"{eval_folder}/scenes")
scene_tasks = [load_json(f"{eval_folder}/scene_tasks/{item}") for item in os.listdir(f"{eval_folder}/scene_tasks") if item.endswith(".json")]
assert len(scenes) == len(scene_tasks)
task_settings = []
for i in range(len(scene_tasks)):
    task = scene_tasks[i]
    scenes[i]["player"]["prefab"] = "null"
    if "QA" in task:
        for sample in task["QA"]:
            options = " ".join([f"{j}.{option}" for j, option in enumerate(sample["options"])])
            task_settings.append({"scene": scenes[i], "task": f"Question: {sample['task']}\nOptions: {options}", "predicates": [f"choose {sample['answer']}"]})
    elif "ACTION" in task:
        continue
        for sample in task["ACTION"]:
            task_settings.append({"scene": scenes[i], "task": f"Command: {sample['task']}", "predicates": [f"false"]})

MAX_STEPS = 5
failed_cases = []

env = Environment(env_path="auto", camera_resolution_width=448, camera_resolution_height=448, camera_field_of_view=120, run_options={"port": 50051}, use_animation=False)
try:
    for i in range(len(task_settings)):
        print("\n" + "==" * 4 + f"Start episode {i}" + "==" * 4)
        task_setting = task_settings[i]
        print(task_setting["task"])
        print("Predicates:", task_setting["predicates"])
        agent.start(task_setting["task"])
        obs: Observation = env.reset(ResetInfo(scene=task_setting["scene"]))
        traj_save_dir = f"{save_path}/traj{i:04d}"
        os.makedirs(traj_save_dir)
        step = 0
        done = False
        while step < MAX_STEPS:
            if step == MAX_STEPS - 1:
                extra_hint = "You have reached the maximum steps. You must choose the correct answer now."
                action: Action = agent.act(obs.image, extra_hint=extra_hint)
            else:
                action: Action = agent.act(obs.image)
            obs = env.step(action)

            save_image(obs.image, f"{traj_save_dir}/{step:04d}.png")
            print(f"step {step}, action: {action_to_string(action)}\n")
            task_type = "qa"  # task_setting["task"].split("")[0].lower()
            done, info = task_done(task_type, action, obs, task_setting)
            store_json({"step": step, "action": action_to_string(action), "done_after_action": done, "info_after_action": info}, f"{traj_save_dir}/{step:04d}a.json")
            step += 1
            if done:
                success_count += 1
                print("Task accomplished.")
            if isinstance(action, ActionFinish) or action.text != "" or done:
                save_image(obs.image, f"{traj_save_dir}/{step:04d}.png")
                break
        if not done:
            failed_cases.append(i)
            print("Task failed.")
finally:
    env.close()
result = {"Success Rate": f"{success_count}/{len(task_settings)}", "failed cases": failed_cases}
print(result)
store_json(result, f"{save_path}/result.json")
