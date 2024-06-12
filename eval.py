import os
import requests
from legent import Environment, Action, ActionFinish, Observation, store_json, ResetInfo, load_json, save_image, unpack_scenes, time_string, find_files_by_extension
from legent.utils.math import vec_xz, distance
from PIL import Image
import io
import base64
import requests
from openai import OpenAI
from functools import partial
from legent.utils.math import distance, vec_xz
import re
from legent.action.action import Action, ActionFinish
import queue
import threading

PROMPT_PREFIX = """You are a vision language assistant agent with high intelligence.
You are placed inside a virtual environment and you are given a goal that needs to be finished, you need to choose an action at each step to complete the task. If you need more information, you should explore the environment.

Your current task is:
{}
"""

PROMPT_SUFFIX = """Your current options are as follows:
{}
You must choose one of them and directly output the number of the option. Try use move forward the best choice.
If the object is in your view and near you, you can choose to grab it.
If the last action in Action history failed, do not choose it again.
"""
# ATTENTION:
    # Do not call grab action twice.
    # Do not turn left and then turn right back.
    # Do not turn right and the turn left back.
    # Please use move forward more frequently. 

class AgentBase:
    def __init__(self, model_name: str, sync: bool = False, env=None) -> None:
        # init the api or model
        self.model_name = model_name
        self.images = []
        self.actions = [] # (action feedback)
        self.max_history = 3
        self.task = ""
        self.sync = sync
        if not sync:
            self.env = env
            self.request_queue = queue.Queue()  # Queue for storing requests
            self.response_queue = queue.Queue()  # Queue for storing responses

            worker_thread = threading.Thread(target=self._process_request)
            worker_thread.daemon = True  # Set as a daemon thread so it will automatically quit if the main program exits
            worker_thread.start()
            self.is_waiting_response = False
    
    def _process_request(self):
        while True:
            try:
                (image, feedback, options, extra_hint) = self.request_queue.get(timeout=1)  # Avoid endless polling of an empty queue, saving CPU resources, and ensures timely responses to new requests.
                
                action = self.act_sync(image, feedback, options, extra_hint)
                self.response_queue.put(action)
            except queue.Empty:
                continue

    def start(self, instruction):
        self.instruction = instruction
        self.images = []
        self.actions = []

    def init_message(self):
        raise NotImplementedError
    
    def append_text(self):
        raise NotImplementedError
    
    def append_image(self):
        raise NotImplementedError
    
    def print_message(self):
        raise NotImplementedError
    
    def send_message(self):
        raise NotImplementedError
    
    def _act(self, actions, images, image, options, extra_hint):
        # 输入行动历史、图片历史、当前图片和候选项，输入行动选项
        self.init_message()
        self.append_text(f"{PROMPT_PREFIX.format(self.instruction)}\n")
        # append_text(f"the history of the images you have seen and the history of your actions are as follows:\n")
        # for o, a in zip(images, actions):
        #     append_image(o)
        #     append_text(a)
        self.append_text(f"Action history (action -> result):\n")
        for a in actions:
            self.append_text(f"\t{a[0]} -> {a[1]}\n")
        self.append_text(f"\nThe history of images you have seen:\n")
        for o in images:
            self.append_image(o)
        
        self.append_text(f"\nThe current image you see: \n")
        self.append_image(image)
        options_string = "\n".join([f"{i}. {option}" for i, option in enumerate(options)])
        self.append_text(f"\n\n{PROMPT_SUFFIX.format(options_string)}\n{extra_hint}") # Your History

        self.print_message()
        
        return self.send_message()
    
    def act(self, image, feedback, options, extra_hint=""):
        if self.sync:
            return self.act_sync(image, feedback, options, extra_hint)
        else:
            self.request_queue.put((image, feedback, options, extra_hint))
            while True:
                env.step()
                try:
                    action = self.response_queue.get_nowait()
                    break
                except queue.Empty:
                    pass

            return action
            
            
        
    def act_sync(self, image, feedback, options, extra_hint=""):
        if feedback:
            self.update_feedback(feedback)
        response = self._act(self.actions, self.images, image, options, extra_hint).strip()
        
        print("response:", response)
        action = Action()
        action.action_choice = int(re.search(r'\d', response).group(0))
        
        self.update_history(image, options[action.action_choice])
        return action
    
    def update_history(self, image, action):
        self.images.append(image)
        self.actions.append([action, ""])
        if len(self.images) > self.max_history:
            self.images = self.images[-self.max_history :]
        # NOTE: do not truncate action_history
        
    def update_feedback(self, feedback):
        if self.actions:
            self.actions[-1][1] = feedback

class AgentGPT4V(AgentBase):
    def __init__(self, env=None) -> None:
        super().__init__("gpt4v", env==None, env)
        self.api_key = "sk-qmu3GtIMZtNYCTMm743199219bD44791BfBcDbFd9d1b3404"
        self.client = OpenAI(api_key=self.api_key, base_url="https://yeysai.com/v1/")
    
    def init_message(self):
        self.payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user","content": []}],
            "max_tokens": 1024
        }
    
    def append_text(self, text):
        self.payload["messages"][0]["content"].append({"type": "text", "text": text})
    
    def append_image(self, image):
        def encode_image(image):
            if type(image) == str:
                with open(image, "rb") as image:
                    return base64.b64encode(image.read()).decode('utf-8')
            else:
                from PIL import Image
                buffer = io.BytesIO()
                Image.fromarray(image).save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
        image = {"type": "image_url","image_url": {"url": f"data:image/jpeg;base64,{encode_image(image)}"}}
        self.payload["messages"][0]["content"].append(image)
    
    def print_message(self):
        message = " ".join([m["text"] if m["type"]=="text" else "<image>" for m in self.payload["messages"][0]["content"]])
        print("="*20+"\n"+message+"="*20+"\n")
    
    def send_message(self):
        def send_request(payload):
            headers = {"Content-Type": "application/json","Authorization": f"Bearer {self.api_key}"}

            # for the official openai api
            # response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            # for lab api
            response = requests.post("https://yeysai.com/v1/chat/completions", headers=headers, json=payload)
            # print(response.json())
            answer = response.json()["choices"][0]["message"]["content"]
            return answer
        return send_request(self.payload)


class AgentGemini(AgentBase):
    def __init__(self, env=None) -> None:
        super().__init__("gemini-pro", env==None, env)

    def init_message(self):
        self.messages = []
        self.files = []
    
    def append_text(self, text):
        self.messages.append(text)
    
    def append_image(self, image):
        self.messages.append("<image>")
        img = Image.fromarray(image)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        self.files.append(("files", (f"image{i}.png", buf.read(), "image/png")))
    
    def print_message(self):
        message = "".join(self.messages)
        print("="*20+"\n"+message+"="*20+"\n")
    
    def send_message(self):
        message = "".join(self.messages)
        payload = {"message": message, "model": "pro"}  # model: flash or pro
        return requests.post("http://146.190.166.36:8901/", files=self.files, data=payload).text

class AgentHuman(AgentBase):
    def __init__(self, env) -> None:
        super().__init__("human")
        self.env = env
        
    def act(self, image, options, extra_hint="") -> int:
        action = Action()
        while True:
            obs = env.step()
            if obs.text!="":
                action.action_choice = int(obs.text)
                return action
    

class Predicate:
    def __init__(self) -> None:
        pass
    
    def task_done(self, action: Action, obs: Observation, options, task_setting)->int:
        # 0 continue 1 success -1 failed
        raise NotImplementedError

class PredicateChoose(Predicate):
    def __init__(self, answer) -> None:
        self.answer = answer

    def task_done(self, action: Action, obs: Observation, options, task_setting)->int:
        if options[action.action_choice] == self.answer:
            return 1, {}
        elif options[action.action_choice].startswith("answer"):
            return -1, {}
        else:
            return 0, {}

class PredicateAgentNear(Predicate):
    def __init__(self, object_id) -> None:
        self.object_id = object_id

    def task_done(self, action: Action, obs: Observation, options, task_setting)->int:
        
        game_states = obs.game_states
        d = distance(vec_xz(game_states["agent"]["position"]), vec_xz(game_states["instances"][self.object_id]["position"]))
        if d < 1.5:
            return 1, {"distance": d}
        else:
            return 0, {"distance": d}
        
class PredicateCloser(Predicate):
    def __init__(self, object1, object2, obs: Observation) -> None:
        self.object1 = object1
        self.object2 = object2
        instances = obs.game_states["instances"]
        self.init_distance = distance(vec_xz(instances[object1]["position"]), vec_xz(instances[object2]["position"]))

    def task_done(self, action: Action, obs: Observation, options, task_setting)->int:
        instances = obs.game_states["instances"]
        d = distance(vec_xz(instances[self.object1]["position"]), vec_xz(instances[self.object2]["position"]))
        if self.init_distance - d > 2:
            return 1, {"distance_closer": self.init_distance - d}
        else:
            return 0, {"distance_closer": self.init_distance - d}

class PredicateFurther(Predicate):
    def __init__(self, object1, object2, obs: Observation) -> None:
        self.object1 = object1
        self.object2 = object2
        instances = obs.game_states["instances"]
        self.init_distance = distance(vec_xz(instances[object1]["position"]), vec_xz(instances[object2]["position"]))

    def task_done(self, action: Action, obs: Observation, options, task_setting)->int:
        instances = obs.game_states["instances"]
        d = distance(vec_xz(instances[self.object1]["position"]), vec_xz(instances[self.object2]["position"]))
        if d - self.init_distance > 1:
            return 1, {"distance_closer": d - self.init_distance}
        else:
            return 0, {"distance_closer": d - self.init_distance}
        

class PredicateOn(Predicate):
    def __init__(self, object1, object2) -> None:
        self.object1 = object1
        self.object2 = object2

    def task_done(self, action: Action, obs: Observation, options, task_setting)->int:
        instances = obs.game_states["instances"]
        d = distance(vec_xz(instances[self.object1]["position"]), vec_xz(instances[self.object2]["position"]))
        if d < 0.3:
            return 1, {}
        else:
            return 0, {}


class PredicateGrab(Predicate):
    def __init__(self, object) -> None:
        self.object = object

    def task_done(self, action: Action, obs: Observation, options, task_setting)->int:
        done = obs.game_states["agent_grab_instance"] == self.object
        if done:
            return 1, {}
        else:
            return 0, {}
        

class PredicateSwap(Predicate):
    def __init__(self, object1, object2, obs: Observation) -> None:
        self.object1 = object1
        self.object2 = object2
        instances = obs.game_states["instances"]
        self.init_pos1 = instances[object1]["position"]
        self.init_pos2 = instances[object2]["position"]

    def task_done(self, action: Action, obs: Observation, options, task_setting)->int:
        instances = obs.game_states["instances"]
        pos1 = instances[self.object1]["position"]
        pos2 = instances[self.object2]["position"]
        
        if distance(vec_xz(self.init_pos1), vec_xz(pos2)) < 1 and distance(vec_xz(self.init_pos2), vec_xz(pos1)) < 1:
            return 1, {}
        else:
            return 0, {}


class PredicateIn(Predicate):
    def __init__(self, objects, on_object) -> None:
        self.objects = objects
        self.on_object = on_object

    def task_done(self, action: Action, obs: Observation, options, task_setting)->int:
        instances = obs.game_states["instances"]
        for object_id in self.objects:
            d = distance(vec_xz(instances[object_id]["position"]), vec_xz(instances[self.on_object]["position"]))
            if d > 0.3:
                return 0, {}

        return 1, {}
    

class PredicateNotOn(Predicate):
    def __init__(self, objects, on_object) -> None:
        self.objects = objects
        self.on_object = on_object

    def task_done(self, action: Action, obs: Observation, options, task_setting)->int:
        instances = obs.game_states["instances"]
        for object_id in self.objects:
            d = distance(vec_xz(instances[object_id]["position"]), vec_xz(instances[self.on_object]["position"]))
            if d < 2:
                return 0, {}

        return 1, {}
    
def build_predicate(predicates, obs)->Predicate:
    assert len(predicates) == 1, predicates
    predicate: str = predicates[0]
    print(predicate)
    if predicate.startswith("choose"):
        return PredicateChoose(predicate.split(' ', maxsplit=1)[1])
    elif predicate.startswith("near"):
        splits = predicate.split(' ')
        assert len(splits) == 2
        if len(splits) == 2:
            return PredicateAgentNear(int(splits[1]))
    elif predicate.startswith("closer"):
        splits = predicate.split(' ')
        assert len(splits) == 3
        return PredicateCloser(int(splits[1]), int(splits[2]), obs)
    elif predicate.startswith("further"):
        splits = predicate.split(' ')
        assert len(splits) == 3
        return PredicateFurther(int(splits[1]), int(splits[2]), obs)
    elif predicate.startswith("on"):
        splits = predicate.split(' ')
        assert len(splits) == 3
        return PredicateOn(int(splits[1]), int(splits[2]))
    elif predicate.startswith("grab"):
        splits = predicate.split(' ')
        assert len(splits) == 2
        return PredicateGrab(int(splits[1]))
    elif predicate.startswith("swap"):
        splits = predicate.split(' ')
        assert len(splits) == 3
        return PredicateSwap(int(splits[1]), int(splits[2]), obs)
    elif predicate.startswith("in"):
        splits = predicate.split(' ')
        assert len(splits) == 4
        return PredicateIn([int(_id) for _id in splits[1:-1]], int(splits[-1]))
    elif predicate.startswith("noton"):
        splits = predicate.split(' ')
        assert len(splits) == 3 or len(splits) == 4 or len(splits) == 5
        return PredicateNotOn([int(_id) for _id in splits[1:-1]], int(splits[-1]))

def get_feedback(action: str, prev_obs, obs):
    action = action.lower()
    if action.startswith("grab"):
        if prev_obs.game_states["agent_grab_instance"] == -1 and obs.game_states["agent_grab_instance"] != -1:
            return "success"
        else:
            return "failed"
    elif action.startswith("put"):
        if prev_obs.game_states["agent_grab_instance"] != -1 and obs.game_states["agent_grab_instance"] == -1:
            return "success"
        else:
            return "failed"
    else:
        return "success"
        
# Download from eval_folder_xxx.zip from https://huggingface.co/LEGENT/temp_share/tree/main and extract it
eval_folder = "F:/Downloads/eval_folder_20240611_2357"
   
def get_task_settings_0612():
    
    scenes_zip = ["packed_20_scenes_20240607-124204-783646", "packed_77_scenes_20240607-124050-071183", "packed_15_scenes_20240611-033932-398380"]
    scene_path_to_scene = {}
    for scene_zip in scenes_zip:
        scenes = unpack_scenes(f"{eval_folder}/{scene_zip}.zip")
        for scene in scenes:
            scene["player"]["prefab"] = "null"
        for i, scene in enumerate(scenes):
            scene_path_to_scene[f"{scene_zip}/scene_{i}.json"] = scene
    def get_scene_by_path(path):
        import copy
        path = '/'.join(path.split("/")[-2:])
        return  copy.deepcopy(scene_path_to_scene[path])
        
    task_settings = []
    files = find_files_by_extension(eval_folder, ".json", recursive=False)
    for file in files:
        # print(file)
        tasks = load_json(file)
        if "QA" in tasks:
            for sample in tasks["QA"]:
                sample["type"] = "QA"
        if "ACTION" in tasks:
            for sample in tasks["ACTION"]:
                sample["type"] = "ACTION"
                
        for sample in tasks["QA"] + tasks["ACTION"]:
            qa = sample["type"] == "QA"
            
            # Process scene
            scene = get_scene_by_path(sample["scene"])
            # add object_of_interest
            for object_id in sample["object_id"]:
                scene["instances"][object_id]["of_interest"] = True
            # add options
            # TODO: 这个任务需要加一个抬头动作
            if sample["task"] == "Please help me move my laptops off the tall dark brown chest of drawers with black drawer pulls.":
                sample["options"].append("look upward")
                sample["options"].append("look downward")
            
            options = []
            for option in sample["options"]:
                if qa:
                    assert ":" not in option
                    options.append({"description": f"answer \"{option}\"", "object_ids": []})
                else:
                    # TODO：有一个标的不统一，暂时改成grab
                    if option.startswith("pick up"):
                        option = option.replace("pick up", "grab")
                        print(option)
                    
                    if ":" in option:
                        description, object_ids = option.split(":")
                        options.append({"description": description, "object_ids": object_ids.split(",")})
                    else:
                        options.append({"description": option, "object_ids": []})
            scene["options"] = options
            
            if qa:
                task_description = f"Question: {sample['task']}"
                scene["task"] = task_description
                
                assert len(sample["answer"]) == 1
                answer = options[sample['answer'][0]-1]["description"]
                
                predicates = [f"choose {answer}"]
                scene["predicates"] = [{
                    "predicate": "choose",
                    "content": answer,
                    "object_ids": []
                }]
            else:
                
                # TODO: 这个任务 ['noton 33'] 要改一下
                if sample["task"] == "Clear the folding chair of all objects.":
                    sample["predicates"][0] = "noton 34 37 38 33"
                if sample["task"] == "Clear the bedside table of all things.":
                    sample["predicates"][0] = "noton 16 15"
                if sample["task"] == "Take out everything from the bathroom sink":
                    sample["predicates"][0] = "noton 42 43 44 41"
                if sample["task"] == "Clear the round wooden table of all objects.":
                    sample["predicates"][0] = "noton 36 35"
                
                task_description = f"Command: {sample['task']}"
                scene["task"] = task_description
                
                assert len(sample["predicates"]) == 1,  sample["predicates"]
                predicate = sample["predicates"][0]
                # TODO: 这个标错了
                if predicate.startswith("not on"):
                    predicate = predicate.replace("not on", "noton")
                predicates = [predicate]
                # print(len(task_settings), predicate)
                splits = predicate.split(" ")
                scene["predicates"] = [{
                    "predicate": splits[0],
                    "content": "",
                    "object_ids": [int(_id) for _id in splits[1:]]
                }]
                
            task_setting = {"scene": scene, "task": task_description, "predicates": predicates, "type": sample["type"]}
            task_settings.append(task_setting)
                
    return task_settings

task_settings = get_task_settings_0612()
store_json(task_settings, f"task_settings.json")

# task_settings = get_task_settings_0609()[6:]
#print(len(task_settings))
#exit(0)

MAX_STEPS = 25
failed_cases = []

env = Environment(env_path="auto", action_mode=1, camera_resolution_width=448, camera_resolution_height=448, camera_field_of_view=90, run_options={"port": 50051}, use_animation=False)

#agent = AgentHuman(env)
agent = AgentGemini(env)
#agent = AgentGPT4V(env)
success_count = 0

save_path = f"{eval_folder}/results/{time_string()}-{agent.model_name}"
try:
    for i in range(len(task_settings)):
        # 16 closer 这个例子很好
        # 17 further
        # 18 on
        # 19 grab
        # 20 swap 这个例子很好
        # 21 in 两个物体
        # 22 noton
        #   23 on
        #   24 noton 多个，这个例子很好，但是桌子那些称呼不太分的清
        # 25 near
        #   26 noton 多个，这个例子也可以
        #   27 grab
        #   28 further
        #   29 closer 18 9
        #   45 swap 11 38
        #   46 in 11 23
        #   47 near 39
        #   48 closer 9 27
        #   49 further 11 29
        #   50 on 20 24
        #   51 grab 28
        #   52 swap 30 19
        #   53 noton 18 15
        #   54 in 17 15
        #   55 noton 16 17 15
        #   56 near 24
        #   57 grab 17
        #   58 noton 15
        #   59 on 16 32
        #   65 on 62 41
        #   66 noton 41
        #   67 on 88 56
        #   68 near 95 navigation点很怪
        #   69 noton 35
        if i<17:
            continue
        if task_settings[i]["type"] == "QA":
            continue
        print("\n" + "==" * 4 + f"Start episode {i}" + "==" * 4)
        task_setting = task_settings[i]
        print(task_setting["task"])
        print("Predicates:", task_setting["predicates"])
        agent.start(task_setting["task"])
        obs: Observation = env.reset(ResetInfo(scene=task_setting["scene"]))
        
        predicate = build_predicate(task_setting["predicates"], obs)
        
        options = obs.game_states["option_mode_info"]["options"]
        feedback = None
        prev_obs = obs
        print(options)
        
        traj_save_dir = f"{save_path}/traj{i:04d}"
        os.makedirs(traj_save_dir)
        step = 0
        done = 0
        while step < MAX_STEPS:
            if step == MAX_STEPS - 1:
                extra_hint = "You have reached the maximum steps. You must choose the correct answer now."
                action: Action = agent.act(obs.image, feedback, options, extra_hint=extra_hint)
            else:
                action: Action = agent.act(obs.image, feedback, options)
            obs = env.step(action)
            
            # 获取选项和反馈信息
            new_options = obs.game_states["option_mode_info"]["options"]
            # success_calculated_by_env = obs.game_states["option_mode_info"]["success"]
            feedback = get_feedback(options[action.action_choice], prev_obs, obs)
            prev_obs = obs
            
            save_image(obs.image, f"{traj_save_dir}/{step:04d}.png")
            print(f"step {step}, action: {action.action_choice}. {options[action.action_choice]}\n")
            done, info = predicate.task_done(action, obs, options, task_setting)
            
            store_json({"step": step, "options": options, "action_choice": action.action_choice, "action": options[action.action_choice],  "done_after_action": done, "info_after_action": info}, f"{traj_save_dir}/{step:04d}a.json")
            
            options = new_options
            print(options)
            
            step += 1
            if done==1:
                success_count += 1
                print("Task accomplished.")
            if isinstance(action, ActionFinish) or action.text != "" or done!=0:
                save_image(obs.image, f"{traj_save_dir}/{step:04d}.png")
                break
        if done!=1:
            failed_cases.append(i)
            print("Task failed.")
except Exception as e:
    raise e
finally:
    env.close()
result = {"Success Rate": f"{success_count}/{len(task_settings)}", "failed cases": failed_cases}
print(result)
store_json(result, f"{save_path}/result.json")
