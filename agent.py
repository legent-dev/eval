import os
from typing import List, Tuple
import requests
from legent import Environment, Action, store_json, time_string
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


# 用于记录输入
class EmbodiedEvalAction(Action):
    def __init__(self, payload={}):
        super().__init__() 
        self.payload = payload

verbose = True  # 是否输出每步详细信息

PROMPT_PREFIX = """You are an intelligent vision-language embodied agent skilled at solving tasks and answering questions in a 3D environment. Your goal is to efficiently complete a given task.
PROMPT_PREFIX = """You are an intelligent vision-language embodied agent skilled at solving tasks and answering questions in a 3D environment. Your goal is to efficiently complete a given task.
You will receive a series of ego-centric images and a corresponding action history. Each image shows what you see at a particular step in your action sequence, along with an extra image showing your current view.
Your job is to analyze these visual inputs and the action history to decide the most appropriate action for each step, guiding you towards successful task completion. After each action, you will get feedback on whether it was successful or the response from the human, along with an updated view to guide your next move.
Your job is to analyze these visual inputs and the action history to decide the most appropriate action for each step, guiding you towards successful task completion. After each action, you will get feedback on whether it was successful or the response from the human, along with an updated view to guide your next move.

Your current task is:
{}
"""


PROMPT_SUFFIX = """Your available options are listed as "[Option Number]. Content" as follows:
{}

Choose your next action from the above options by replying with "Thought: Your reasoning.\nChoice: [Option Number]". For example, "Choice: [1]".
Choose your next action from the above options by replying with "Thought: Your reasoning.\nChoice: [Option Number]". For example, "Choice: [1]".

Note:
- If the task needs more information of the scene, prioritize exploring unseen areas and rooms using "move forward", "turn left/right", or "look up/down".
- If the task includes terms like "I" or "me", the task is issued by a human in the scene.
- If the task needs more information of the scene, prioritize exploring unseen areas and rooms using "move forward", "turn left/right", or "look up/down".
- If the task includes terms like "I" or "me", the task is issued by a human in the scene.
- You can only hold one object at a time, so put down the current object before picking up another.
- You can interact with objects or humans (e.g. pick/place/open/close/handover) only if they are within your view and close to you (within 2m).
- Avoiding repeating already successful actions. 
- Reflect on why previous actions fail to avoid repeating mistakes and ajdust your current action smartly.
- You have a limited number of {} steps to complete the task, so choose wisely to maximize your progress and achieve your goal efficiently.
"""

# PROMPT_SUFFIX = """Your available options are listed as "[Option Number]. Content" as follows:
# {}

# Choose your next action from the above options by directly replying with "Choice: [Option Number]" without extra words. For example, "Choice: [1]".

# Note:
# - If the task needs more information of the scene, prioritize exploring unseen areas and rooms using "move forward", "turn left/right", or "look up/down".
# - If the task includes terms like "I" or "me", the task is issued by a human in the scene.
# - You can only hold one object at a time, so put down the current object before picking up another.
# - You can interact with objects or humans (e.g. pick/place/open/close/handover) only if they are within your view and close to you. If not visible or close, try to look around to find it or move close to it.
# - Avoiding repeating already successful actions. 
# - Reflect on why previous actions fail to avoid repeating mistakes and ajdust your current action smartly.
# - You have a limited number of {} steps to complete the task, so choose wisely to maximize your progress and achieve your goal efficiently.
# """

# 去掉了一些点：
#  Avoid unnecessary circling in one place.
#  If possible, prioritize "move forward."
#  If you are approaching the maximum step count, make your final decision promptly.

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
        self.append_text(f"\nVisual history:\n")
        for o in images:
            self.append_image(o)

        self.append_text(f"\nCurrent view:\n")
        self.append_image(image)
        options_string = "\n".join([f"{i}. {option}" for i, option in enumerate(options) if i > 0]) #  去掉idle
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
            
        result = self._act(self.actions, self.images, image, options)
        if not result:
            print("failed to get response")
            return False
        if not result:
            print("failed to get response")
            return False
        try:
            payload, response = result["payload"], result["answer"]
            response = response.strip()
        except:
            response = result.strip()

        print("response:", response)
        action = EmbodiedEvalAction()
        action.text = response
        action.payload = payload
        
        try:
            # Match "Choice: [4]" or "Choice: 4" using a regular expression
            action.action_choice = int(re.search(r"Choice:?[\n\s]*\[?(\d+)\]?", response, re.IGNORECASE).group(1))
        except:
            try:
                action.action_choice = int(re.search(r"(\d+)(?!.*\d)", response, re.DOTALL).group(1))
            except:
                action.action_choice = -1 # cannot match any number
        try:
            self.update_history(image, options[action.action_choice])
        except:
            action.action_choice = -2 # option out of range
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
    def __init__(self, env, model="gpt-4o") -> None:
        super().__init__(model, env == None, env)
        self.model = model
        use = 3
        if use == 1:
            self.api_key = "sk-qmu3GtIMZtNYCTMm743199219bD44791BfBcDbFd9d1b3404"
        elif use == 2:
            self.api_key = "sk-AW9DZ4gqpAG4rdu050C55e33010e47C2B9E40a00536c8aC9"
        else:
            self.api_key = "sk-zk2f5d1691b1640e3d81147f5b3f900cdd866f6d047921ce"
        
        if use < 3:
            self.base_url = "https://yeysai.com/v1"
        else:
            self.base_url = "https://api.zhizengzeng.com/v1"
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            
    def __init__(self, env, model="gpt-4o") -> None:
        super().__init__(model, env == None, env)
        self.model = model
        use = 3
        if use == 1:
            self.api_key = "sk-qmu3GtIMZtNYCTMm743199219bD44791BfBcDbFd9d1b3404"
        elif use == 2:
            self.api_key = "sk-AW9DZ4gqpAG4rdu050C55e33010e47C2B9E40a00536c8aC9"
        else:
            self.api_key = "sk-zk2f5d1691b1640e3d81147f5b3f900cdd866f6d047921ce"
        
        if use < 3:
            self.base_url = "https://yeysai.com/v1"
        else:
            self.base_url = "https://api.zhizengzeng.com/v1"
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            

    def init_message(self):
        self.payload = {"model": self.model, "messages": [{"role": "user", "content": []}], "max_tokens": 1024}
        self.payload = {"model": self.model, "messages": [{"role": "user", "content": []}], "max_tokens": 1024}

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

    def generate(self, use_official=True):
    def generate(self, use_official=True):
        def send_request(payload):
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
            # if use_official:
            #     # for the official openai api
            #     response = requests.post("https://api.zhizengzeng.com/v1", headers=headers, json=payload)
            #     print("use official gpt4-o")
            # if use_official:
            #     # for the official openai api
            #     response = requests.post("https://api.zhizengzeng.com/v1", headers=headers, json=payload)
            #     print("use official gpt4-o")

            # for lab api
            print(f"about to query {self.model}")
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            print(f"about to query {self.model}")
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            # print(response.json())
            answer = response.json()["choices"][0]["message"]["content"]
            return answer

        for i in range(50):
            try:
                answer = send_request(self.payload)
                break
            except:
                time.sleep(5)
        else:
            raise Exception("Failed to get response from the model.")

        # 输入和输出
        return {"payload": self.payload, "answer":answer}


class AgentGeminiPro(AgentBase):
    def __init__(self, env) -> None:
        super().__init__("gemini-pro", env == None, env)
        
        self.api_key = "sk-zk2b9aff16a140c420bcc70a0c9f0f5d08066f7e5138a6ef"
        self.base_url = "https://api.zhizengzeng.com/v1"
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            

    def init_message(self):
        self.payload = {"model": "gemini-1.5-pro", "messages": [{"role": "user", "content": []}], "max_tokens": 1024}

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

    def generate(self, use_official=True):
        def send_request(payload):
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
            # if use_official:
            #     # for the official openai api
            #     response = requests.post("https://api.zhizengzeng.com/v1", headers=headers, json=payload)
            #     print("use official gpt4-o")

            # for lab api
            print("about to query gemini-pro")
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            # print(response.json())
            answer = response.json()["choices"][0]["message"]["content"]
            return answer

        for i in range(50):
            try:
                answer = send_request(self.payload)
                break
            except Exception as e:
                print(e)
                time.sleep(5)
        else:
            raise Exception("Failed to get response from the model.")

        # 输入和输出
        return {"payload": self.payload, "answer":answer}


class AgentGeminiPro(AgentBase):
    def __init__(self, env) -> None:
        super().__init__("gemini-pro", env == None, env)
        
        self.api_key = "sk-zk2b9aff16a140c420bcc70a0c9f0f5d08066f7e5138a6ef"
        self.base_url = "https://api.zhizengzeng.com/v1"
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            

    def init_message(self):
        self.payload = {"model": "gemini-1.5-pro", "messages": [{"role": "user", "content": []}], "max_tokens": 1024}

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

    def generate(self, use_official=True):
        def send_request(payload):
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
            # if use_official:
            #     # for the official openai api
            #     response = requests.post("https://api.zhizengzeng.com/v1", headers=headers, json=payload)
            #     print("use official gpt4-o")

            # for lab api
            print("about to query gemini-pro")
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            # print(response.json())
            answer = response.json()["choices"][0]["message"]["content"]
            return answer

        for i in range(50):
            try:
                answer = send_request(self.payload)
                break
            except Exception as e:
                print(e)
                time.sleep(5)
        else:
            raise Exception("Failed to get response from the model.")

        # 输入和输出
        return {"payload": self.payload, "answer":answer}


class AgentGemini(AgentBase):
    def __init__(self, env, use_flash=False) -> None:
        self.use_flash = use_flash
        if use_flash:
            super().__init__("gemini-flash", env == None, env)
        else:
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
        for i in range(50):
            message = "".join(self.messages)
            if self.use_flash:
                payload = {"message": message, "model": "flash"}  # model: flash or pro
                print("about to query gemini-flash")
                print("about to query gemini-flash")
            else:
                payload = {"message": message, "model": "pro"}
                print("about to query gemini-pro")
            try:
                response = requests.post("http://146.190.166.36:8901/", files=self.files, data=payload)
                if response.status_code == 200:
                    answer = response.text
                    break
                else:
                    print("retry")
                    if self.use_flash:
                        time.sleep(5)
                    else:
                        time.sleep(10)
            except:
                print("about to query gemini-pro")
            try:
                response = requests.post("http://146.190.166.36:8901/", files=self.files, data=payload)
                if response.status_code == 200:
                    answer = response.text
                    break
                else:
                    print("retry")
                    if self.use_flash:
                        time.sleep(5)
                    else:
                        time.sleep(10)
            except:
                print("retry")
                if self.use_flash:
                    time.sleep(5)
                else:
                    time.sleep(10)
                if self.use_flash:
                    time.sleep(5)
                else:
                    time.sleep(10)
        else:
            return False
            return False
        
        # 输入和输出
        return {"payload": payload, "answer":answer}


class AgentQwen(AgentBase):
    def __init__(self, env, model) -> None:
        super().__init__(model, env == None, env)
        self.model = model
    def __init__(self, env, model) -> None:
        super().__init__(model, env == None, env)
        self.model = model
        self.api_key = "sk-5a6c7237637b4ee7b74445be2de15aa9"
        self.client = OpenAI(api_key=self.api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")

    def init_message(self):
        self.payload = {"model": self.model, "messages": [{"role": "user", "content": []}], "max_tokens": 1024}
        self.payload = {"model": self.model, "messages": [{"role": "user", "content": []}], "max_tokens": 1024}

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
            completion = self.client.chat.completions.create(model=payload["model"],messages=payload["messages"])
            return completion

        for i in range(20):
        for i in range(20):
            try:
                print("about to query qwen") # 一般是payload too large这个错误
                completion = send_request(self.payload)
                print("about to query qwen") # 一般是payload too large这个错误
                completion = send_request(self.payload)
                answer = completion.choices[0].message.content
                break
            except Exception as e:
                print(e)
                print("retry")
                time.sleep(2)
            except Exception as e:
                print(e)
                print("retry")
                time.sleep(2)
        else:
            return False
            return False

        # 输入和输出
        return {"payload": self.payload, "answer":answer}
   
    
class AgentHuman(AgentBase):
    def __init__(self, env) -> None:
        super().__init__("human", env == None, env)
        self.env = env

    def act(self, image, feedback, options) -> int:
        action = Action()
        while True:
            obs = self.env.step()
            if obs.text != "":
                try:
                    action.action_choice = int(obs.text)
                    if action.action_choice < 0 or action.action_choice >= len(options):
                        continue
                except:
                    continue
                return action


class AgentRotate(AgentBase):
    def __init__(self, env) -> None:
        super().__init__("rotate", env == None, env)
        self.env = env

    def act(self, image, feedback, options) -> int:
        print(options)
        action = Action()
        action.action_choice = 0
        return action


class AgentRandom(AgentBase):
    def __init__(self, env) -> None:
        super().__init__("random", env == None, env)
        self.env = env

    def act(self, image, feedback, options) -> int:
        action = Action()
        action.action_choice = np.random.randint(1, len(options))
        action.action_choice = np.random.randint(1, len(options))
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
