import openai
from openai import OpenAI
import base64
import requests


def get_message_old(content):
    return [
        [
            {
                "role": "user",
                "content": content,
            }
        ]
    ]


# openai==0.28
def get_response_old(content):
    message = get_message_old(content)
    response = openai.ChatCompletion.create(
        # model='gpt-3.5-turbo',
        # model='gpt-4-32k',
        # model='gpt-3.5-turbo-16k',
        model="gpt-4-turbo",
        messages=message,
    )
    return response["choices"][0]["message"]["content"]


def get_message_new(content):
    return [
        # {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": content},
    ]


# openai>=1.0.0
def get_response_new(content):
    message = get_message_new(content)
    client = OpenAI(api_key=api_key, base_url=api_base)
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=message,
    )
    # print(completion.choices[0].message)
    return completion.choices[0].message.content


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# gpt-4v
def get_response_4v(image_list, text, local=True):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [{"role": "user", "content": [{"type": "text", "text": text}]}],
        "max_tokens": 1024,
    }

    # Getting the base64 string
    for image in image_list:
        if local:
            base64_image = encode_image(image)
            new_dict = {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            }
        else:
            new_dict = {"type": "image_url", "image_url": {"url": image}}
        payload["messages"][0]["content"].append(new_dict)

    # for the official openai api
    # response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    # for lab api
    response = requests.post(
        "https://yeysai.com/v1/chat/completions", headers=headers, json=payload
    )
    try:
        answer = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(e)
        answer = "ERROR"
    return answer
