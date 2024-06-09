import os
import requests
from legent import Environment, Action, ActionFinish, Observation, store_json, ResetInfo, load_json, save_image, unpack_scenes, time_string
from legent.utils.math import vec_xz, distance
from legent.dataset.controller import MAX_MOVE_DISTANCE, MAX_ROTATE_DEGREE
from PIL import Image
import io
import base64
import requests
from openai import OpenAI
from functools import partial

PROMPT_SHARED = f"""You are a vision language assistant agent with high intelligence.
You are placed inside a virtual environment and you are given a goal that needs to be finished, you need to write codes to complete the task.
You can solve any complex tasks by decomposing them into subtasks and tackling them step by step, but you should only provide the action code for solving the very next subtask.
You need to perform the following actions to complete the tasks:
1. choose [number]: choose an answer.
2. move_forward [meters]: move forward a certain distance (max_meters={MAX_MOVE_DISTANCE:.1f}).
3. rotate_right [degrees]: Adjust the view to the right with a certain degree. "degrees" can be any integers between -{MAX_ROTATE_DEGREE} and {MAX_ROTATE_DEGREE}, inclusive.
4. rotate_down [degrees]: Adjust the view to look down (negative means look up). "degrees" can be any integers between -{MAX_ROTATE_DEGREE} and {MAX_ROTATE_DEGREE}, inclusive.
5. focus [x_ratio] [y_ratio]: focus on a pixel in the image. x_ratio and y_ratio are between 0 and 1. 0 0 is the top left corner and 1 1 is the bottom right corner.
6. grab: grab the object in the center of the image, if it is not in the center, you should use focus first.
7. release

For example, if you want to choose the second option, you should write "choose 2". Do not output any other things including comment.
If you want to grab an object that is not in the center of the image, you should write "focus 0.21 0.38" (suppose the object in the image is at 0.21 0.38).
If the object you want to grab is in the center of the image, you should write "grab".

Your task is to answer the question or complete the command. If you have no enough information to answer the question, you can move and rotate the get more information.
"""
# If you are too close to an object, consider looking down to see the object.

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
    if action.use_look_at:
        action_strings.append(f"lookat {action.look_x} {action.look_y}")

    return ", ".join(action_strings)


def string_to_action(action_str: str):
    try:
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
            elif elem.startswith("focus"):
                action.look_x = float(splits[1])
                action.look_y = float(splits[2])
                action.use_look_at = True
            elif elem.startswith("choose"):
                action.text = splits[1]
        return action
    except:
        action = Action()
        print("Wrong action format.")
        raise
        return action


class AgentBase:
    def __init__(self, model_name: str) -> None:
        # init the api or model
        self.model_name = model_name
        self.images = []
        self.actions = []
        self.max_history = 3
        self.task = ""

    def start(self, instruction):
        self.instruction = instruction
        self.images_history = []
        self.action_history = []

    def act(self, image):
        raise NotImplementedError
    
    def update_history(self, image, action):
        self.images.append(image)
        self.actions.append(action_to_string(action))
        if len(self.images) > self.max_history:
            self.images = self.images[-self.max_history :]
        if len(self.actions) > self.max_history:
            self.actions = self.actions[-self.max_history :]


class AgentGPT4V(AgentBase):
    def __init__(self) -> None:
        super().__init__("gpt4v")
        self.api_key = "sk-qmu3GtIMZtNYCTMm743199219bD44791BfBcDbFd9d1b3404"
        self.client = OpenAI(api_key=self.api_key, base_url="https://yeysai.com/v1/")
    def send_request(self, payload):
        headers = {"Content-Type": "application/json","Authorization": f"Bearer {self.api_key}"}
        
        # for the official openai api
        # response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        # for lab api
        response = requests.post("https://yeysai.com/v1/chat/completions", headers=headers, json=payload)
        # print(response.json())
        answer = response.json()["choices"][0]["message"]["content"]
        return answer

        
    def start(self, instruction):
        self.instruction = instruction
        self.images_history = []
        self.action_history = []
        
    def act(self, image, extra_hint=""):
        
        # Function to encode the image
        def encode_image(image):
            if type(image) == str:
                with open(image, "rb") as image:
                    return base64.b64encode(image.read()).decode('utf-8')
            else:
                from PIL import Image
                buffer = io.BytesIO()
                Image.fromarray(image).save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode('utf-8')

        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user","content": []}],
            "max_tokens": 1024
        }
        
        def append_image(image):
            image = {"type": "image_url","image_url": {"url": f"data:image/jpeg;base64,{encode_image(image)}"}}
            payload["messages"][0]["content"].append(image)
            
        def append_text(text):
            payload["messages"][0]["content"].append({"type": "text", "text": text})
            
        
        message = f"{PROMPT_SHARED}\nYour task:\n{self.instruction}\n\nHistory:\n{extra_hint}"
        append_text(message)
        for o, a in zip(self.images, self.actions):
            append_image(o)
            append_text(a)
        append_image(image)
        
        append_text("Please output your next action apis")

        response = self.send_request(payload)
        print("response:", response.strip())
        action = string_to_action(response)
        self.update_history(image, action)
        return action



#agent = AgentGPT4V()
#agent.start("描述这张图片")
#agent.act(image="C:/Users/cheng/Desktop/LIGENT_dev/temp.png")
#exit(0)

class AgentGemini(AgentBase):
    def __init__(self) -> None:
        super().__init__("gemini-pro")

    def act(self, image, extra_hint=""):
        super().act()
        action = Action()

        images,actions = self.images_history,self.action_history

        message = f"{PROMPT_SHARED}\nYour task:\n{self.instruction}\n\nHistory:\n{extra_hint}"
        for o, a in zip(images, actions):
            message += f"Image: <image> Action: {a}"  # <image> is a placeholder for the image
        message += "\nPlease output your next action apis"
        payload = {"message": message, "model": "pro"}  # model: flash or pro
        files = []
        for i, image_array in enumerate(images):
            img = Image.fromarray(image_array)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            files.append(("files", (f"image{i}.png", buf.read(), "image/png")))

        # files = [("files", (f"image{i}.png", image, "image/png")) for i, image in enumerate(images)]
        response = requests.post("http://146.190.166.36:8901/", files=files, data=payload).text
        response = "focus 0.6 0.5"
        
        print("response:", response.strip())
        action = string_to_action(response)
        self.update_history(image, action)

        return action


#agent = AgentGemini()
agent = AgentGPT4V()
success_count = 0


COME_DONE_DISTANCE = 2.0


def task_done(action: Action, obs, task_setting):
    assert len(task_setting["predicates"])==1
    predicate = task_setting["predicates"][0]
    splits = predicate.split(" ")
    if splits[0] == "choose":
        done = action.text == splits[1]
        return done, {}
    else:
        return False, {}
    # if task == "come":
    #     game_states = obs.game_states
    #     d = distance(vec_xz(game_states["agent"]["position"]), vec_xz(game_states["player"]["position"]))
    #     done = d < COME_DONE_DISTANCE
    #     return done, {"distance": d}
    # elif task == "qa":
    #     done = action.text == task_setting["predicates"][0].split(" ")[1]
    #     return done, {}
    # else:
    #     raise NotImplementedError


# Download from eval_folder_example.zip from https://cloud.tsinghua.edu.cn/d/502178ebdc6647138ce2/ and extract it
eval_folder = "F:/Downloads/eval_folder_example" # 0606
eval_folder = "F:/Downloads/eval_77" # 0609
save_path = f"{eval_folder}/results/{time_string()}-{agent.model_name}"

scenes = unpack_scenes(f"{eval_folder}/scenes.zip")
for scene in scenes:
    scene["player"]["prefab"] = "null"

def get_task_settings_0606():
    scene_tasks = [load_json(f"{eval_folder}/scene_tasks/{item}") for item in os.listdir(f"{eval_folder}/scene_tasks") if item.endswith(".json")]
    assert len(scenes) == len(scene_tasks)
    task_settings = []
    for i in range(len(scene_tasks)):
        task = scene_tasks[i]
        if "QA" in task:
            for sample in task["QA"]:
                options = " ".join([f"{j}.{option}" for j, option in enumerate(sample["options"])])
                task_settings.append({"scene": scenes[i], "task": f"Question: {sample['task']}\nOptions: {options}", "predicates": [f"choose {sample['answer']}"]})
        elif "ACTION" in task:
            for sample in task["ACTION"]:
                task_settings.append({"scene": scenes[i], "task": f"Command: {sample['task']}", "predicates": [f"false"]})
    return task_settings
    
def get_task_settings_0609():
    task_settings = []
    tasks = load_json(f"{eval_folder}/tasks.json")
    
        
    #scenes[i]["player"]["prefab"] = "null"
    if "QA" in tasks:
        #print(tasks["ACTION"])
        for sample in tasks["QA"]:
            break
            i = int(sample["scene"].split("/")[-1].split(".")[0].split("_")[1])
            options = " ".join([f"{j}.{option}" for j, option in enumerate(sample["options"])])
            task_settings.append({"scene": scenes[i], "task": f"Question: {sample['task']}\nOptions: {options}", "predicates": [f"choose {sample['answer']}"]})
    if "ACTION" in tasks:
        # print(tasks["ACTION"])
        for sample in tasks["ACTION"]:
            #print(sample)
            i = int(sample["scene"].split("/")[-1].split(".")[0].split("_")[1])
            task_settings.append({"scene": scenes[i], "task": f"Command: {sample['task']}", "predicates": sample["predicates"]})
    return task_settings

task_settings = get_task_settings_0609()[6:]
#print(len(task_settings))
#exit(0)
MAX_STEPS = 25
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
            done, info = task_done(action, obs, task_setting)
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
except Exception as e:
    raise e
finally:
    env.close()
result = {"Success Rate": f"{success_count}/{len(task_settings)}", "failed cases": failed_cases}
print(result)
store_json(result, f"{save_path}/result.json")
