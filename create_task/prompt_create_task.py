from scripts.gpt_api import get_response_4v, get_response_new


# 使用GPT-4V 根据场景和物体信息生成文本化描述
def scene_to_description(file_path, scene_object_info, room_object_info):
    photo_path = [f"{file_path}/photo.png"]  # 图像路径

    prompt = ""
    prompt += "Imagine you are an embodied robotic assistant and you are in a virtual cartoon-style indoor scene. \n"

    prompt += "Taking into account the uncertainty of language description, it is clearly stated that there are a total of the following objects in the entire scene: \n"
    if len(room_object_info) > 1:  # 多房间
        prompt += f"There are {len(room_object_info)} rooms in the scene: "
        for room, objects in room_object_info.items():
            prompt += f"{room}, "
        prompt = prompt[:-2] + ". \n"
        for room, objects in room_object_info.items():
            prompt += f"Room {room} has the following objects: \n"
            for index in objects:
                prompt += f"object number:{index}, object name:{scene_object_info[index][0]}, object description:{scene_object_info[index][1]}. \n"
    else:  # 单房间
        prompt += "There is only one room in the scene: "
        prompt += f"{list(room_object_info.keys())[0]}. \n"
        prompt += "The room has the following objects: \n"
        for room, objects in room_object_info.items():
            for index in objects:
                prompt += f"object number:{index}, object name:{scene_object_info[index][0]}, object description:{scene_object_info[index][1]}. \n"

    prompt += "This image is a bird's-eye view of the room you are in. \n"
    prompt += "Please combine the image with the object information in the scene I gave you, and use natural language to describe the scene in detail for me, especially the characteristics of the objects in the scene (color, shape, etc.) and the spatial position of the objects. \n"
    prompt += "Examples are as follows: \n"
    prompt += "There is a wooden table in the livingroom with a red cup and a green toy car on the table. Next to the toy car is a black box with two pencils inside. There are chairs on each side of the wooden table. \n"

    scene_description = get_response_4v(photo_path, prompt, local=True)

    return scene_description


# 使用GPT-4 根据场景描述和任务模板生成任务
def description_to_task(scene_description, scene_object_info, room_object_info):
    prompt = ""
    prompt += "Suppose you are an embodied robotic assistant and you are in an indoor scene. The scene is described as follows: \n"
    prompt += scene_description
    prompt += " \n"

    prompt += "Taking into account the uncertainty of language description, it is clearly stated that there are a total of the following objects in the entire scene: \n"
    if len(room_object_info) > 1:  # 多房间
        prompt += f"There are {len(room_object_info)} rooms in the scene: "
        for room, objects in room_object_info.items():
            prompt += f"{room}, "
        prompt = prompt[:-2] + ". \n"
        for room, objects in room_object_info.items():
            prompt += f"Room {room} has the following objects: \n"
            for index in objects:
                prompt += f"object number:{index}, object name:{scene_object_info[index][0]}, object description:{scene_object_info[index][1]}. \n"
    else:  # 单房间
        prompt += "There is only one room in the scene: "
        prompt += f"{list(room_object_info.keys())[0]}. \n"
        prompt += "The room has the following objects: \n"
        for room, objects in room_object_info.items():
            for index in objects:
                prompt += f"object number:{index}, object name:{scene_object_info[index][0]}, object description:{scene_object_info[index][1]}. \n"

    prompt += "You need to help me complete a series of tasks. The task template is as follows: \n"
    prompt += "1.Is there a {object} in the scene? Where object is a specific object in the scene. \n"
    prompt += "2.What is the name of the object {postion}? Where position is a specific location in the scene, such as on the table. \n"
    prompt += "3.What is the object next to the {object}? Where object is a specific object in the scene. \n"
    prompt += (
        "4.What color is {object}? Where object is a specific object in the scene. \n"
    )
    prompt += "5.What is the shape of {object}? Where object is a specific object in the scene. \n"
    prompt += "6.Identify all the {color} objects in the room. Where color is a specific color. \n"
    prompt += "7.Where is {object}? Where object is a specific object in the scene. \n"
    prompt += "8.Go to {object}. Where object is a specific object in the scene. \n"
    prompt += "9.Move {object} to another room. Where object is a specific object in the scene. \n"  # 多房间时修改
    prompt += "10.Move {object1} closer/further to {object2}. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "11.Put {object1} on the {object2}. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "12.Pick up {object}. Where object is a specific object in the scene. \n"
    prompt += "13.Swap the positions of {object1} and {object2}. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "14.Collect {object1, object2, ...} into {object0}. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "15.Arrange {object1, object2, ...} in a line. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "16.Arrange {object1, object2, ...} in a circle. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "17.Remove {object1, object2, ...} from {object0}. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "18.Clear the {position} of all objects. Where position is a specific location in the scene, such as the surface of the table. \n"
    prompt += "19.Position {object1} at equal distance from {object2} and {object3}. Where object1, object2 and object3 are specific objects in the scene. \n"
    prompt += "20.Stack {object1, object2, ...}. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "21.Count the number of {object}. Where object is a type of object in the scene. \n"
    prompt += "22.Which {object} is biggest/smallest/farthest/nearest? Where object is a type of object in the scene. \n"
    prompt += "23.Which room has the most {object}? Where object is a type of object in the scene. \n"
    prompt += "24.Compare the sizes of {object1} and {object2}. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "If there are multiple objects of the same type or similar types in the scene, then when constructing the task, you need to clearly and unambiguously state which vase the object in the task refers to. This can be referred to by the characteristics of the object itself, such as color, shape, or by its spatial position in the scene.  If there are three vases in a scene, then the task at this time can be structured as: go to {the vase on the edge of the table}, or: go to {the green round vase}. \n"
    prompt += "Please combine scene and object information i give you to generate a series of tasks based on the task template, for example: go to the chair farthest from me, count the number of the yellow vases. \n"
    prompt += "Note that when generating tasks, you can only use the objects I gave you numbers above. \n"
    prompt += "Please generate a corresponding task based on each template. The tasks must comply with common sense and rules to avoid tasks such as pick up the bed. \n"
    prompt += "Note that as a robot assistant, you only have visual abilities and no tactile, hearing or other abilities. Therefore, you can only see the color, size, shape and other information of the cushions, but cannot judge whether the cushions are soft or new or old. \n"
    prompt += "After you generate a task, use diverse language but be precise in your description. For example: Tell me the number of the green vases; Please go to the green cushion. \n"
    prompt += "Please follow the following format for your answer: \n"
    prompt += "Template:Go to {object}. Task:go to the red cushion. \n"
    prompt += "Template:Count the number of {object}. Task:tell me the number of the cups on the table. \n"
    prompt += "Template:What is the color of {object}? Task:Tell me the color of the vase on the shelf. \n"

    # print("\n\n" + prompt + "\n\n")

    return get_response_new(prompt)


# 使用GPT-4 根据场景描述和任务模板生成QA类任务
def description_to_task_QA(scene_description, scene_object_info, room_object_info):
    prompt = ""
    prompt += "Suppose you are an embodied robotic assistant and you are in an indoor scene. The scene is described as follows: \n"
    prompt += scene_description
    prompt += " \n"

    prompt += "Taking into account the uncertainty of language description, it is clearly stated that there are a total of the following objects in the entire scene: \n"
    if len(room_object_info) > 1:  # 多房间
        prompt += f"There are {len(room_object_info)} rooms in the scene: "
        for room, objects in room_object_info.items():
            prompt += f"{room}, "
        prompt = prompt[:-2] + ". \n"
        for room, objects in room_object_info.items():
            prompt += f"Room {room} has the following objects: \n"
            for index in objects:
                prompt += f"object number:{index}, object name:{scene_object_info[index][0]}, object description:{scene_object_info[index][1]}. \n"
    else:  # 单房间
        prompt += "There is only one room in the scene: "
        prompt += f"{list(room_object_info.keys())[0]}. \n"
        prompt += "The room has the following objects: \n"
        for room, objects in room_object_info.items():
            for index in objects:
                prompt += f"object number:{index}, object name:{scene_object_info[index][0]}, object description:{scene_object_info[index][1]}. \n"

    prompt += "You need to help me complete a series of tasks. The task template is as follows: \n"
    prompt += "1.Is there a {object} in the scene? Where object is a specific object in the scene. \n"
    prompt += "2.What is the name of the object {postion}? Where position is a specific location in the scene, such as on the table. \n"
    prompt += "3.What is the object next to the {object}? Where object is a specific object in the scene. \n"
    prompt += (
        "4.What color is {object}? Where object is a specific object in the scene. \n"
    )
    prompt += "5.What is the shape of {object}? Where object is a specific object in the scene. \n"
    prompt += "6.Identify all the {color} objects in the room. Where color is a specific color. \n"
    prompt += "7.Where is {object}? Where object is a specific object in the scene. \n"
    prompt += "8.Count the number of {object}. Where object is a type of object in the scene. \n"
    prompt += "9.Which {object} is biggest/smallest/farthest/nearest? Where object is a type of object in the scene. \n"
    prompt += "10.Which room has the most {object}? Where object is a type of object in the scene. \n"
    prompt += "11.Compare the sizes of {object1} and {object2}. Where object1 and object2 are specific objects in the scene. \n"

    prompt += "If there are multiple objects of the same type or similar types in the scene, then when constructing the task, you need to clearly and unambiguously state which vase the object in the task refers to. This can be referred to by the characteristics of the object itself, such as color, shape, or by its spatial position in the scene.  If there are three vases in a scene, then the task at this time can be structured as: Count the number of {the vases on the edge of the table}, or: What is the shape of {the green vase}. \n"
    prompt += "Please combine scene and object information to generate a series of tasks based on the task template, for example: count the number of the yellow vases. \n"
    prompt += "Please generate a corresponding task based on each template. The tasks must comply with common sense and rules to avoid tasks such as pick up the bed. \n"
    prompt += "Note that as a robot assistant, you only have visual abilities and no tactile, hearing or other abilities. Therefore, you can only see the color, size, shape and other information of the cushions, but cannot judge whether the cushions are soft or new or old. \n"
    prompt += "After you generate a task, use diverse language but be precise in your description. For example: Tell me the number of the green vases; Please go to the green cushion. \n"
    prompt += "For each task, four options are generated for me, including one correct answer and three incorrect answers, and indicate which is the correct option. \n"
    prompt += "For each generated task, you need to specify the number of the object in the task at the end. \n"
    prompt += "If the scene description and the information I give you do not have reliable information about features such as color, shape, etc., do not ask questions about these issues, as this will lead to unreliable questions and answers. \n"
    prompt += "Please follow the following format for your answer: \n"
    prompt += "Template: Count the number of {object}. \n"
    prompt += "Task: Tell me the number of the cups on the table. \n"
    prompt += "A: 1 \n"
    prompt += "B: 2 \n"
    prompt += "C: 3 \n"
    prompt += "D: 4 \n"
    prompt += "Right Answer: B \n"
    prompt += "Object Number: 37,45 \n"

    # print("\n\n" + prompt + "\n\n")

    return get_response_new(prompt)


# 使用GPT-4 根据场景描述和任务模板生成QA类任务
def description_to_task_action(scene_description, scene_object_info, room_object_info):
    prompt = ""
    prompt += "Suppose you are an embodied robotic assistant and you are in an indoor scene. The scene is described as follows: \n"
    prompt += scene_description
    prompt += " \n"

    prompt += "Taking into account the uncertainty of language description, it is clearly stated that there are a total of the following objects in the entire scene: \n"
    if len(room_object_info) > 1:  # 多房间
        prompt += f"There are {len(room_object_info)} rooms in the scene: "
        for room, objects in room_object_info.items():
            prompt += f"{room}, "
        prompt = prompt[:-2] + ". \n"
        for room, objects in room_object_info.items():
            prompt += f"Room {room} has the following objects: \n"
            for index in objects:
                prompt += f"object number:{index}, object name:{scene_object_info[index][0]}, object description:{scene_object_info[index][1]}. \n"
    else:  # 单房间
        prompt += "There is only one room in the scene: "
        prompt += f"{list(room_object_info.keys())[0]}. \n"
        prompt += "The room has the following objects: \n"
        for room, objects in room_object_info.items():
            for index in objects:
                prompt += f"object number:{index}, object name:{scene_object_info[index][0]}, object description:{scene_object_info[index][1]}. \n"

    prompt += "You need to help me complete a series of tasks. The task template is as follows: \n"
    prompt += "1.Go to {object}. Where object is a specific object in the scene. \n"
    prompt += "2.Move {object} to another room. Where object is a specific object in the scene. \n"  # 多房间时修改
    prompt += "3.Move {object1} closer to {object2}. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "4.Put {object1} on the {object2}. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "5.Pick up {object}. Where object is a specific object in the scene. \n"
    prompt += "6.Swap the positions of {object1} and {object2}. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "7.Collect {object1, object2, ...} into {object0}. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "8.Arrange {object1, object2, ...} in a line. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "9.Arrange {object1, object2, ...} in a circle. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "10.Remove {object1, object2, ...} from {object0}. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "11.Clear the {position} of all objects. Where position is a specific location in the scene, such as the surface of the table. \n"
    prompt += "12.Position {object1} at equal distance from {object2} and {object3}. Where object1, object2 and object3 are specific objects in the scene. \n"
    prompt += "13.Stack {object1, object2, ...}. Where object1 and object2 are specific objects in the scene. \n"
    prompt += "14.Move {object1} further away from {object2}. Where object1 and object2 are specific objects in the scene. \n"

    prompt += "If there are multiple objects of the same type or similar types in the scene, then when constructing the task, you need to clearly and unambiguously state which vase the object in the task refers to. This can be referred to by the characteristics of the object itself, such as color, shape, or by its spatial position in the scene.  If there are three vases in a scene, then the task at this time can be structured as: go to {the vase on the edge of the table}, or: go to {the green round vase}. \n"
    prompt += "Please combine scene and object information to generate a series of tasks based on the task template, for example: go to the chair farthest from me. \n"
    prompt += "Please generate a corresponding task based on each template. The tasks must comply with common sense and rules to avoid tasks such as pick up the bed. \n"
    prompt += "Note that as a robot assistant, you only have visual abilities and no tactile, hearing or other abilities. Therefore, you can only see the color, size, shape and other information of the cushions, but cannot judge whether the cushions are soft or new or old. \n"
    prompt += "After you generate a task, use diverse language but be precise in your description. For example: Tell me the number of the green vases; Please go to the green cushion. \n"
    prompt += "For each generated task, you need to specify the number of the object in the task at the end. \n"
    prompt += "If the scene description and the information I give you do not have reliable information about features such as color, shape, etc., do not create tasks about these issues, as this will lead to unreliable tasks. \n"
    prompt += "Please follow the following format for your answer: \n"
    prompt += "Template: Go to {object}. \n"
    prompt += "Task: Go to the red round cup on the table. \n"
    prompt += "Object Number: 37 \n"

    # print("\n\n" + prompt + "\n\n")

    return get_response_new(prompt)
