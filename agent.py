import os
from typing import List, Tuple
import requests
from legent import Environment, Action, ActionFinish, Observation, store_json, ResetInfo, load_json, save_image, unpack_scenes, time_string, find_files_by_extension
from legent.utils.math import vec_xz, distance
from PIL import Image
import io
import base64
import requests
from openai import OpenAI
from legent.utils.math import distance, vec_xz
import re
from legent.action.action import Action, ActionFinish
from legent.utils.io import log_green
import queue
import threading
import numpy as np
import time


verbose = False  # 是否输出每步详细信息
PROMPT_PREFIX = """You are a vision language assistant agent with high intelligence.
You are placed inside a virtual environment and you are given a goal that needs to be finished, you need to choose an action at each step to complete the task.

Your current task is:
{}
"""


# TO DO: 加入CoT，允许思考，但是要按指定格式输出然后parse
# TO DO: 怎样很好地避免这种情况：一直连续选择同一个动作，比如一直grab grab，一直失败，提示已经说了也不起作用。这种情况很容易发生！
# TO DO: 把last action单独拿出来？可以重点关注last action是否成功，如果不成功，不要再选择这个动作。
PROMPT_SUFFIX = (
    """Your current options are as follows:
{}
You must choose one of them and directly output the number of the option.
If the object is in your view and near you, you can choose to grab it.
If the last action in Action history failed, do not choose it again.
If you need more information beyond the current view, you can possibly explore the environment by "move forward", "turn left/right", "loo up/down". Among them, if you can move forward, prioritize "moving forward".
You can only hold one object at a time, so if you need to hold another object, you need to put down the current object first.
Attention: you only have a limited number of steps ({} steps) to finish the task, so do not turn around in circles at one position. If you are about to reach the maximum step count, please choose to answer the question immediately.
"""
)
# If you last action is grab and failed, DO NOT choose grab now.
# If you last action is put and failed, DO NOT choose put now.

# ATTENTION:
# Do not call grab action twice.
# Do not turn left and then turn right back.
# Do not turn right and the turn left back.
# Please use move forward more frequently.


class AgentBase:
    def __init__(self, model_name: str, max_image_history: int, sync: bool, env) -> None:
        # init the api or model
        self.model_name = model_name
        self.images = []
        self.actions = []  # (action feedback)
        self.max_history = max_image_history
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
        self.max_steps = 25

    def _process_request(self):
        while True:
            try:
                (image, feedback, options) = self.request_queue.get(timeout=1)  # Avoid endless polling of an empty queue, saving CPU resources, and ensures timely responses to new requests.

                action = self.act_sync(image, feedback, options)
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

    def generate(self):
        raise NotImplementedError

    def _act(self, actions, images, image, options):
        # 输入行动历史、图片历史、当前图片和候选项，输入行动选项
        self.init_message()
        self.append_text(f"{PROMPT_PREFIX.format(self.instruction)} {self.max_steps}\n")
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
        self.append_text(f"\n\n{PROMPT_SUFFIX.format(options_string)}")  # Your History

        self.print_message()

        return self.generate()

    def act(self, image, feedback, options):
        if self.sync:
            return self.act_sync(image, feedback, options)
        else:
            self.request_queue.put((image, feedback, options))
            while True:
                self.env.step()
                try:
                    action = self.response_queue.get_nowait()
                    break
                except queue.Empty:
                    pass

            return action

    def act_sync(self, image, feedback, options):
        if feedback:
            self.update_feedback(feedback)
        response = self._act(self.actions, self.images, image, options).strip()

        print("response:", response)
        action = Action()
        try:
            action.action_choice = int(re.search(r"\d", response).group(0))
        except:
            action.action_choice = -1
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
    def __init__(self, max_image_history, env) -> None:
        super().__init__("gpt-4o", max_image_history, env == None, env)
        self.api_key = "sk-qmu3GtIMZtNYCTMm743199219bD44791BfBcDbFd9d1b3404"
        self.client = OpenAI(api_key=self.api_key, base_url="https://yeysai.com/v1/")

    def init_message(self):
        self.payload = {"model": "gpt-4o", "messages": [{"role": "user", "content": []}], "max_tokens": 1024}

    def append_text(self, text):
        self.payload["messages"][0]["content"].append({"type": "text", "text": text})

    def append_image(self, image):
        def encode_image(image):
            if type(image) == str:
                with open(image, "rb") as image:
                    return base64.b64encode(image.read()).decode("utf-8")
            else:
                from PIL import Image

                buffer = io.BytesIO()
                Image.fromarray(image).save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode("utf-8")

        image = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(image)}"}}
        self.payload["messages"][0]["content"].append(image)

    def print_message(self):
        if verbose:
            message = " ".join([m["text"] if m["type"] == "text" else "<image>" for m in self.payload["messages"][0]["content"]])
            print("=" * 20 + "\n" + message + "=" * 20 + "\n")

    def generate(self):
        def send_request(payload):
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}

            # for the official openai api
            # response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            # for lab api
            response = requests.post("https://yeysai.com/v1/chat/completions", headers=headers, json=payload)
            # print(response.json())
            answer = response.json()["choices"][0]["message"]["content"]
            return answer

        for i in range(10):
            try:
                answer = send_request(self.payload)
                break
            except:
                time.sleep(5)
        else:
            raise Exception("Failed to get response from the model.")

        return answer


class AgentGemini(AgentBase):
    def __init__(self, env, max_image_history) -> None:
        super().__init__("gemini-pro", max_image_history, env == None, env)

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
        self.files.append(("files", (f"image{len(self.files)}.png", buf.read(), "image/png")))

    def print_message(self):
        if verbose:
            message = "".join(self.messages)
            print("-" * 40 + "\n" + message + "-" * 40 + "\n")

    def generate(self):
        for i in range(10):
            try:
                message = "".join(self.messages)
                payload = {"message": message, "model": "pro"}  # model: flash or pro
                answer = requests.post("http://146.190.166.36:8901/", files=self.files, data=payload).text
                break
            except:
                time.sleep(5)
        else:
            raise Exception("Failed to get response from the model.")
        return answer


class AgentHuman(AgentBase):
    def __init__(self, env) -> None:
        super().__init__("human", 1, env == None, env)
        self.env = env

    def act(self, image, options) -> int:
        action = Action()
        while True:
            obs = self.env.step()
            if obs.text != "":
                action.action_choice = int(obs.text)
                return action


class YourAgent(AgentBase):
    # 用于评测你的模型/API
    def __init__(self, env, max_image_history) -> None:
        super().__init__("your_model_name", max_image_history, env == None, env)
        # 这里放模型/API的初始化代码
        # self.model = ...

    def init_message(self):
        # 用来准备给模型的输入
        # init_message之后，agent.act会把prompt和历史信息通过append_text和append_image添加到消息中
        # 为了保证各种模型的消息构成一致，只暴露了这几个接口
        pass

    def append_text(self, text):
        pass

    def append_image(self, image):
        pass

    def print_message(self):
        # 打印一些信息，可以不用实现
        pass

    def generate(self):
        # 这里放模型/API的推理代码
        # return model.generate_text(...)
        pass


# TODO: write your own agent
class YourAgentSimple(AgentBase):
    # 用于评测你的模型/API
    def __init__(self, env, max_image_history) -> None:
        super().__init__("your_model_name", max_image_history, env == None, env)
        # 这里放模型/API的初始化代码
        # self.model = ...

    def _act(self, actions: List[Tuple[str, str]], images: List[np.array], image: np.array, options: List[str]) -> str:
        # 这里放模型/API的推理代码
        pass

        # TODO：将prompt和下列图文信息整理成模型的输入
        # self.instruction: 任务
        # actions: 行动历史 [("action content", "success_or_failed"), ("", ""), ...]
        # images: 图片历史
        # image: 当前图片
        # options: 当前可选项

        # TODO：进行模型推理
        # return model.generate_text(...)
        
        # TODO: parse推理结果为选项数字
