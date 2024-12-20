from typing import List, Tuple
from legent import Action
import re
import queue
import threading
import numpy as np
import re
from prompts import PROMPT_IMAGE_PREFIX, PROMPT_VIDEO_PREFIX, PROMPT_SUFFIX
from openai import OpenAI



VERBOSE = True

class AgentBase:
    def __init__(self, model_name: str, sync: bool, env) -> None:
        self.model_name = model_name
        self.images = []
        self.actions = []  # [(action, feedback)]
        self.task = ""
        self.sync = sync
        if not sync:
            self.env = env
            self.request_queue = queue.Queue()
            self.response_queue = queue.Queue()
            worker_thread = threading.Thread(target=self._process_request)
            worker_thread.daemon = True  # Set as a daemon thread so it will automatically quit if the main program exits
            worker_thread.start()
            self.is_waiting_response = False
        self.env = env

    def _process_request(self):
        while True:
            try:
                (image, feedback, options, use_video, video_path) = self.request_queue.get(timeout=1) # Avoid endless polling of an empty queue, saving CPU resources, and ensures timely responses to new requests.

                action = self.act_sync(image, feedback, options, use_video, video_path)
                self.response_queue.put(action)
            except queue.Empty:
                continue

    def start(self, instruction):
        self.instruction = instruction
        self.images = []
        self.actions = []

    def init_message(self):
        self.texts = []
        self.images = []
    
    def append_text(self, text):
        self.texts.append(text)
        
    def append_image(self, image):
        self.texts.append("<image>")
        self.images.append(image)

    def print_message(self):
        if VERBOSE:
            message = "".join(self.texts)
            print("-" * 40 + "\n" + message + "-" * 40 + "\n")

    def generate(self):
        raise NotImplementedError

    def _act(self, actions, images, image, options, use_video=False, video_path=None):
        self.init_message()
        PROMPT_PREFIX = PROMPT_IMAGE_PREFIX if not use_video else PROMPT_VIDEO_PREFIX
        self.append_text(f"{PROMPT_PREFIX.format(self.instruction)}\n")
        self.append_text(f"Action history (action -> feedback):\n")
        for a in actions:
            self.append_text(f"\t{a[0]} -> {a[1]}\n")

        if not use_video:
            self.append_text(f"\nVisual history:\n")
            for o in images:
                self.append_image(o)
                
            self.append_text(f"\nCurrent view:\n")
            self.append_image(image)
        else:
            self.video_path = video_path
            
        options_string = "\n".join([f"{i}. {option}" for i, option in enumerate(
            options) if i > 0])  # remove the first idle option
        self.append_text(
            f"\n\n{PROMPT_SUFFIX.format(options_string, self.max_steps)}")

        self.print_message()

        return self.generate()

    def act(self, image, feedback, options, use_video, video_path):
        if self.sync:
            return self.act_sync(image, feedback, options, use_video, video_path)
        else:
            self.request_queue.put(
                (image, feedback, options, use_video, video_path))
            while True:
                self.env.step()
                try:
                    action = self.response_queue.get_nowait()
                    break
                except queue.Empty:
                    pass

            return action

    def act_sync(self, image, feedback, options, use_video, video_path):
        if feedback:
            self.update_feedback(feedback)

        result = self._act(self.actions, self.images, image,
                           options, use_video, video_path)
        if not result:
            print("failed to get response")
            return False
        try:
            payload, response = result["payload"], result["answer"]
            response = response.strip()
        except:
            response = result.strip()

        print("response:", response)
        action = Action()
        action.text = response

        try:
            # Match "Choice: [4]" or "Choice: 4" using a regular expression
            action.action_choice = int(
                re.search(r"Choice:?[\n\s]*\[?(\d+)\]?", response, re.IGNORECASE).group(1))
        except:
            try:
                action.action_choice = int(
                    re.search(r"(\d+)(?!.*\d)", response, re.DOTALL).group(1))
            except:
                action.action_choice = -1  # code for cannot match any number
                
        if action.action_choice > 0 and action.action_choice < len(options):
            self.update_history(image, options[action.action_choice])
        else:
            action.action_choice = -2  # code for option out of range
            
        return action

    def update_history(self, image, action):
        self.images.append(image)
        self.actions.append([action, ""])
        if len(self.images) > self.max_image_history:
            self.images = self.images[-self.max_image_history:]
        # NOTE: do not truncate action_history

    def update_feedback(self, feedback):
        if self.actions:
            self.actions[-1][1] = feedback


class AgentHuman(AgentBase):
    def __init__(self, env) -> None:
        super().__init__("human", env == None, env)
        self.env = env

    def act(self, image, feedback, options, use_video, video_path) -> int:
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

    def act(self, image, feedback, options, use_video, video_path) -> int:
        print(options)
        action = Action()
        action.action_choice = 0
        return action


class AgentRandom(AgentBase):
    def __init__(self, env) -> None:
        super().__init__("random", env == None, env)
        self.env = env

    def act(self, image, feedback, options, use_video, video_path) -> int:
        action = Action()
        action.action_choice = np.random.randint(1, len(options))
        return action

# ===================== Models ===================== 
# ===================== API ===================== 
import requests
import base64
import io
from PIL import Image
import time

def encode_image(image):
    if type(image) == str:
        with open(image, "rb") as image:
            return base64.b64encode(image.read()).decode("utf-8")
    else:
        buffer = io.BytesIO()
        Image.fromarray(image).save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

class AgentGPT4V(AgentBase):
    def __init__(self, env, model="gpt-4o") -> None:
        super().__init__(model, env == None, env)
        self.model = model
        self.api_key = "your key"
        self.base_url = "https://api.openai.com/v1"
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            
    def init_message(self):
        self.payload = {"model": self.model, "messages": [{"role": "user", "content": []}], "max_tokens": 1024, "temperature": 0}

    def append_text(self, text):
        self.payload["messages"][0]["content"].append({"type": "text", "text": text})

    def append_image(self, image):
        image = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(image)}"}}
        self.payload["messages"][0]["content"].append(image)

    def print_message(self):
        if VERBOSE:
            message = " ".join([m["text"] if m["type"] == "text" else "<image>" for m in self.payload["messages"][0]["content"]])
            print("=" * 20 + "\n" + message + "=" * 20 + "\n")

    def generate(self):
        def send_request(payload):
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
            response = requests.post(self.base_url, headers=headers, json=payload)
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
        
        return answer


class AgentGemini(AgentBase):
    def __init__(self, env, use_flash=True) -> None:
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
        if VERBOSE:
            message = "".join(self.messages)
            print("-" * 40 + "\n" + message + "-" * 40 + "\n")

    def generate(self):
        for i in range(50):
            message = "".join(self.messages)
            if self.use_flash:
                payload = {"message": message, "model": "flash"}  # model: flash or pro
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
                print("retry")
                if self.use_flash:
                    time.sleep(5)
                else:
                    time.sleep(10)
        else:
            return False
        
        # 输入和输出
        return answer
    
    
# ===================== Image ===================== 
class AgentVILA(AgentBase):
    def __init__(self, env=None) -> None:
        model_name = "Llama-3-VILA1.5-8B"
        super().__init__(model_name, env == None, env)
        model_path = "Efficient-Large-Model/Llama-3-VILA1.5-8B"
        self.conv_mode="llama_3"
        import sys
        sys.path.append('...')
        from vila import init_model, run_inference
        self.run_inference = run_inference
        self.tokenizer, self.model, self.image_processor = init_model(model_path)
        
    def generate(self):
        output = self.run_inference(self.tokenizer, self.model, self.conv_mode, self.image_processor, self.images)
        return output

# ===================== Video ===================== 
class AgentLLaVAVideoSeries(AgentBase):
    def __init__(self, env=None) -> None:
        import sys
        sys.path.append('...')
        from llava_video import init_model, run_inference
        model_name = "LLaVA-Video-7B-Qwen2"
        super().__init__(model_name, env == None, env)
        self.run_inference = run_inference
        model_path = "lmms-lab/LLaVA-Video-7B-Qwen2"
        self.conv_mode = "qwen_1_5"
        self.tokenizer, self.model, self.image_processor, self.cfg_pretrained = init_model(
            model_path)

    def generate(self):
        output = self.run_inference(self.video_path, self.tokenizer, self.model,
                                    self.image_processor, self.cfg_pretrained, self.conv_mode, self.payload)
        return output


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