import os
from typing import List, Tuple
import requests
from legent import Environment, Action
from PIL import Image
import io
import base64
import requests
from openai import OpenAI
import re
import queue
import threading
import numpy as np
import time


verbose = False  # 是否输出每步详细信息

PROMPT_PREFIX = """You are an intelligent vision-language assistant agent situated in a virtual environment.
Your goal is to complete a specific task provided to you.
You will be given a series of images and action history.
The input images represent your ego-centric view of the environment. 
Each image corresponds to a step in your action history, and the additional one image represents your latest view after the last action.
Based on these views, you need to choose an action at each step to accomplish your task.
After each action, the environment will respond, indicating whether the action was successful and providing a new view.

Your current task is:
{}
"""


PROMPT_SUFFIX = (
    """Your current options are presented in the format "[Option Number]. Content", as follows::
{}
Considering your visual input and action history, select the next action.
Please include the option number in your answer with "Choice: [Option Number]", for example, "Choice: [1]".
If an object is within your view and close to you, you can choose to grab it.
Avoid repeating actions that have previously failed.
If you need additional information beyond the current view, consider exploring the environment using "move forward", "turn left/right", or "look up/down". 
If possible, prioritize "move forward."
Note that you can only hold one object at a time, so put down the current object before picking up another.
Remember: You have a limited number of {} steps to complete the task. Avoid unnecessary circling in one place.
If you are approaching the maximum step count, make your final decision promptly.
"""
)


class AgentBase:
    def __init__(self, model_name: str, sync: bool, env) -> None:
        # init the api or model
        self.model_name = model_name
        self.images = []
        self.actions = []  # (action feedback)
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
        self.env = env

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
        self.append_text(f"{PROMPT_PREFIX.format(self.instruction)}\n")
        # append_text(f"the history of the images you have seen and the history of your actions are as follows:\n")
        # for o, a in zip(images, actions):
        #     append_image(o)
        #     append_text(a)
        self.append_text(f"Action history (action -> feedback):\n")
        for a in actions:
            self.append_text(f"\t{a[0]} -> {a[1]}\n")
        self.append_text(f"\nThe history of images you have seen:\n")
        for o in images:
            self.append_image(o)

        self.append_text(f"\nThe current image you see: \n")
        self.append_image(image)
        options_string = "\n".join([f"{i}. {option}" for i, option in enumerate(options)])
        self.append_text(f"\n\n{PROMPT_SUFFIX.format(options_string, self.max_steps)}")  # Your History

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
            action.action_choice = int(re.search(r"\[(\d+)\]", response).group(1))
        except:
            action.action_choice = -1
        self.update_history(image, options[action.action_choice])
        return action

    def update_history(self, image, action):
        self.images.append(image)
        self.actions.append([action, ""])
        if len(self.images) > self.max_image_history:
            self.images = self.images[-self.max_image_history :]
        # NOTE: do not truncate action_history

    def update_feedback(self, feedback):
        if self.actions:
            self.actions[-1][1] = feedback


class AgentGPT4V(AgentBase):
    def __init__(self, env) -> None:
        super().__init__("gpt-4o", env == None, env)
        self.api_key = "sk-qmu3GtIMZtNYCTMm743199219bD44791BfBcDbFd9d1b3404"
        self.client = OpenAI(api_key=self.api_key, base_url="https://yeysai.com/v1/")
        print("env", env)

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
    def __init__(self, env) -> None:
        super().__init__("gemini-pro", env == None, env)

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
    def __init__(self, env) -> None:
        super().__init__("your_model_name", env == None, env)
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
    def __init__(self, env) -> None:
        super().__init__("your_model_name", env == None, env)
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
