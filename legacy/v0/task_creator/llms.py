import base64
import requests
from retry import retry
from openai import OpenAI
from functools import partial
import requests
import time
import os
from mimetypes import guess_type
import requests


API_KEY = "sk-qmu3GtIMZtNYCTMm743199219bD44791BfBcDbFd9d1b3404"
BASE_URL = "https://yeysai.com/v1/"


client = OpenAI(
    api_key='sk-qmu3GtIMZtNYCTMm743199219bD44791BfBcDbFd9d1b3404',
    base_url='https://yeysai.com/v1'
)

# Function to encode the image
def local_image_to_data_url(image_path):
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:{mime_type};base64,{base64_encoded_data}"


def gpt_4o(image_list, text, local=True, model="gpt-4o"):
    messages=[
        {
            "role": "user",
            "content": [{"type": "text", "text": text}],
        }
    ]
    # Getting the base64 string
    for image in image_list:
        if local:
            new_dict = {
                "type": "image_url",
                "image_url": {"url": local_image_to_data_url(image)}
            }
        else:
            new_dict = {
                "type": "image_url",
                "image_url": {"url": image}
            }
        messages[0]["content"].append(new_dict)


    #for the official openai api
    # response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    # for lab api
    i = 0
    answer = ""
    while i < 10:
        response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens = 1000,
                temperature = 0.2
            )
        answer = response.choices[0].message.content
        if answer:
            break
        else:
            time.sleep(1)
            i += 1
    return answer


def gemini(image_list, prompt, model="pro"):
    payload={"message":prompt+"<image>", "model": model}
    address = 'http://146.190.166.36:8901/'

    files = [('files', ('image1.png', open(image_list[0], 'rb'), 'image/png'))]

    response = requests.post(address, files=files, data=payload).text
    return response
    

@retry(Exception, tries=10)
def get_llm(model_name, content):
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    messages = [{"role": "user", "content": content}]
    response = client.chat.completions.create(model=model_name,messages=messages)
    result = response.choices[0].message.content
    return result


chatgpt = partial(get_llm, model_name='gpt-3.5-turbo')
gpt4 = partial(get_llm, model_name='gpt-4')
gpt4_mini = partial(get_llm, model_name="gpt-4o-mini")


def test(image_path):
    payload={"message":"你好,描述一下这两张图片，中间要有分隔<image>", "model":"flash"} # # model flash或者pro
    files=[
        ('files', ('image1.png', open(image_path, 'rb'), 'image/png')),
    ]
    response = requests.post('http://146.190.166.36:8901/', files=files, data=payload).text
    print(response)


if __name__ == "__main__":
    # test('/Users/tuyuge/projects/eval-main/tasks/bedroom_18/scene_0/photo.png')
    # exit()
    text = "What are in these images?"
    # # Path to your image
    image_list = ["/Users/tuyuge/projects/eval-main/tasks/bedroom_18/scene_0/photo.png"]
    print(gemini(image_list, text))
    # print(gpt_4o(image_list, text, model="gpt-4o"))

    # prompt = "Your task is to write a function called common_and_uncommon_parts. The function does the following things: the inputs are wall1, wall2, the function checks if the two walls overlap, if so, it returns common_part, [uncommon_part_wall1, uncommon_part_wall2]. Examples: input: wall1 = [(0,0),(0,3)], wall2 = [(0,1),(0,3)], output: [(0,1),(0,3)],[[(0,0),(0,1)], None]. Input: wall1 = [(0,0),(0,3)], wall2 = [(0,0),(0,3)], output: [(0,0),(0,3)],[None, None]. Input: wall1 = [(1,2),(2,2)], wall2 = [(1,2),(3,2)], output: [(1,2),(2,2)],[None,[(2,2),(3,2)]]. Input: wall1 = [(4, 2), (4, 4)], wall2 = [(4, 2), (4, 3)], output:[(4, 2), (4, 3)] [[(4, 3), (4, 4)], None]. Input: wall1=[(7, 0), (7, 8)], wall_2=[(7, 3), (7, 0)], Output: [(7, 3), (7, 0)] [[(7, 3), (7, 8)], None]."
    # result = gpt4(content=prompt)
    # print(result)
