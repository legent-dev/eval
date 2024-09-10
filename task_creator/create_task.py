import os
import random
import time
from PIL import Image
from legent import store_json, load_json, time_string
from llms import gpt4_mini, gpt_4o, gemini
from prompts import SEED_GENERATE_PROMPT, QUESTION_GENERATE_PROMPT, QA_OPTION_GENERATE_PROMPT, ACTION_OPTION_GENERATE_PROMPT
from datetime import datetime
from itertools import groupby
from operator import itemgetter
import json
import re
from legent.utils.io import log_green
from itertools import chain


## 任务生成思路
## Step 1. brainstorm question seeds (for diversity in language and design) + templates
## Step 2. photo+template+scene_graph -> question+solution (for suitability to the scene)
## Step 3. question+solution+scene_graph-> options+predicates (for accuracy and approachability)
### 不需要图片也可以

class TaskGenerator:
    def __init__(self, eval_folder, task_strings_name="task_strings_1.0", task_template_name="task_template_1.0", requests_per_minute=60, num_proc=1):
        self.scene_folder = f"{eval_folder}/tasks/bedroom_18"
        self.task_strings_path = f"{eval_folder}/task_creator/database/{task_strings_name}.json"
        self.task_template_path = f"{eval_folder}/task_creator/database/{task_template_name}.json"
        self.delay_between_requests = 60 / (requests_per_minute * num_proc)
        self.task_strings = load_json(self.task_strings_path)
        self.task_templates = load_json(self.task_template_path)
        
        original_task_templates = load_json(self.task_template_path)
        self.original_qa_templates = [item for item in original_task_templates if item["type"] == "QA"]
        self.original_action_templates = [item for item in original_task_templates if item["type"] == "action"]
        self.used_category = set()


    def generate_additional_examples(self, num_examples=5):
        for ability_group in self.task_strings:
            main_ability = ability_group["ability"]
            for component in ability_group["components"]:
                sub_ability = component["ability"]
                ability = main_ability+"-"+sub_ability
                if "QA" in component:
                    existing_examples = component["QA"]
                    random.shuffle(existing_examples)
                    if len(existing_examples) < num_examples:
                        prompt = SEED_GENERATE_PROMPT.format(num_examples=num_examples-len(existing_examples),ability=ability, existing_examples=existing_examples)
                        print("#"*100, "\n", prompt)
                        gpt_output = gpt4_mini(content=prompt)
                        log_green(gpt_output)

                        parsed_output = self._eval_output(gpt_output)
                        if parsed_output:
                            component["QA"].extend(parsed_output)
                    elif len(existing_examples) > num_examples:
                        component["QA"] = random.sample(component["QA"], num_examples)
                if "action" in component:
                    existing_examples = component["action"]
                    random.shuffle(existing_examples)
                    if len(existing_examples) < num_examples:
                        prompt = SEED_GENERATE_PROMPT.format(num_examples=num_examples-len(existing_examples),ability=ability, existing_examples=existing_examples)
                        print("#"*100, "\n", prompt)
                        gpt_output = gpt4_mini(content=prompt)
                        log_green(gpt_output)

                        parsed_output = self._eval_output(gpt_output)
                        if parsed_output:
                            component["action"].extend(parsed_output)
                    elif len(existing_examples) > num_examples:
                        component["action"] = random.sample(component["action"], num_examples)
        store_json(self.task_strings, self.task_strings_path.replace(".json", f"_{datetime.now():%Y-%m-%d_%H-%M-%S}.json"))


    def _eval_output(self, gpt_output, expected_type=list):
        if expected_type == list:
            match = re.search(r'\[.*?\]', gpt_output, re.DOTALL)
        elif expected_type == dict:
            match = re.search(r'\{(?:[^\{\}]|\{[^\{\}]*\})*\}', gpt_output, re.DOTALL)
        if match:
            try:
                parsed_output = eval(match.group(0))  
                if isinstance(parsed_output, expected_type):
                    return parsed_output
                else:
                    print(f"Error: Expected a {expected_type} but got {type(parsed_output)}. Output: {gpt_output}")
            except:
                print(f"Error: Failed to parse the output as a list. Output: {gpt_output}")
        else:
            print(f"Error: Failed to find a list in the output. Output: {gpt_output}")


    # def _process_ability_component(self, main_ability, sub_ability, example_questions, example):
    #     tasks = []

    #     for question in example_questions:
    #         prompt = OPTIONS_GENERATE_PROMPT.format(question=question, example=example)
    #         print("#"*100, "\n", prompt)
    #         # generate a dict and parse the dict
    #         gpt_response = gpt4_mini(content=prompt)
    #         output_dict = self._eval_output(gpt_response, expected_type=dict)
    #         if output_dict:
    #             print(output_dict)
    #             task_data = {
    #             "ability": main_ability,
    #             "sub_ability": sub_ability,
    #             "task": question,
    #             "type": output_dict["type"],
    #             "object_id": output_dict["object_id"],
    #             "predicates": output_dict["predicates"] if "predicates" in output_dict else [],
    #             "answer": output_dict["answer"] if "answer" in output_dict else [],
    #             "options": output_dict["options"],
    #             }
    #             tasks.append(task_data)
            
    #     return tasks


    # def generate_options(self):
    #     for ability_group in self.task_strings:
    #         main_ability = ability_group["ability"]
    #         components = ability_group["components"]

    #         for component in components:
    #             sub_ability = component["ability"]
    #             example_questions = component["examples"]
    #             example = f"{self._remove_keys(random.choice(self.original_qa_templates))}\n{self._remove_keys(random.choice(self.original_action_templates))}"
    #             tasks = self._process_ability_component(main_ability, sub_ability, example_questions, example)
    #             self.task_templates.extend(tasks)
    #     store_json(self.task_templates, self.task_template_path.replace(".json", f"_{datetime.now():%Y-%m-%d_%H-%M-%S}.json"))


    def _remove_keys(self, example):
        # Removing 'ability' and 'sub_ability'
        example = {k: v for k, v in example.items() if k not in ['ability', 'sub_ability']}
        return example

    def get_question(self,spatial_relations, remaining_objects, task_type, target_objects, ability, example, example_questions):
        sub_abilities = "Temporal Awareness"
        prompt = QUESTION_GENERATE_PROMPT.format(spatial_relations=spatial_relations, ability=ability,task_type=task_type, remaining_objects=remaining_objects, example=example, example_questions=example_questions, sub_abilities=sub_abilities, target_objects=target_objects)
        
        # if ability == "Planning":
        #     prompt += PLAN_REQUIREMENT
        # elif ability == "Spatial Reasoning":
        #     prompt += SPACE_REQUIREMENT
        # elif ability == "Grounding":
        #     prompt += GROUND_REQUIREMENT
        #     # print(prompt)
        #     # exit()
        prompt += "\nYour task should involve at least two rooms."
        print("#"*100, "\n", prompt)
        
        return prompt

    def get_scene_info(self, scene_folder, used_objects):
        image_path = f"{scene_folder}/topdown.png"
        compressed_image_path = self.compress_image(image_path)
        image_list = [compressed_image_path]
        spatial_relations, object_description, target_objects, remaining_objects = self._concatenate_descriptions_to_string(scene_folder, used_objects)
        return image_list, spatial_relations, object_description, target_objects, remaining_objects




    def compress_image(self, input_file_path, new_width=1024):
        output_file_path = input_file_path.replace('.png', '_compressed.png')
        original_size = os.path.getsize(input_file_path)
        
        with Image.open(input_file_path) as img:
            aspect_ratio = img.height / img.width
            new_height = int(new_width * aspect_ratio)
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)
            resized_img.save(output_file_path, format='PNG', optimize=True)
        
        compressed_size = os.path.getsize(output_file_path)
        
        print(f"Original image size: {input_file_path}: {original_size / 1024:.2f} KB")
        print(f"Compressed image size: {output_file_path}: {compressed_size / 1024:.2f} KB")
        
        return output_file_path

    def _concatenate_descriptions_to_string(self, scene_folder, used_objects):
        room_object_info_path = f"{scene_folder}/room_object_info.json"
        scene_object_info_path = f"{scene_folder}/scene_object_info.json"
        spatial_relations_path = f"{scene_folder}/spatial_relations.json"
        room_object_indexes = load_json(room_object_info_path)
        scene_object_info = load_json(scene_object_info_path)
        try:
            spatial_relations = self.get_spatial_relation(load_json(spatial_relations_path), scene_object_info, room_object_indexes)
        except:
            spatial_relations = ""

        # get the dict that contains only indexes from room_object_indexes
        result = []
        for index, value in scene_object_info.items():
            if int(index) not in next(iter(room_object_indexes.values())):
                continue
            if int(index) in used_objects:
                continue
            category = value[0]
            description = value[1]
            if category in self.used_category:
                continue
            if category == "carpet":
                description = "carpet"
            if category:
                result.append(f"{index}. {category}")
            else:
                result.append(f"{index}. {value[2]}")
        sampled_objects = random.sample(result, 5)
        remaining_objects = [obj for obj in result if obj not in sampled_objects]
        log_green(str(len(remaining_objects)))
        return spatial_relations, "\n".join(result), "\n".join(sorted(sampled_objects)), "\n".join(sorted(remaining_objects))
    

    def get_spatial_relation(self, data, scene_object_info, room_object_indexes):
        new_json = {}

        # Populate the new JSON structure
        for item in data:
            obj_id, on_what, in_what = item["id"], item["on_what"], item["in_what"]
            
            if on_what != -1:
                new_json.setdefault(on_what, {"on_children": [], "in_children": []})["on_children"].append(obj_id)
            if in_what != -1:
                new_json.setdefault(in_what, {"on_children": [], "in_children": []})["in_children"].append(obj_id)
            new_json.setdefault(obj_id, {"on_children": [], "in_children": []})

        # Collect children IDs to filter out non-root nodes
        children_ids = {child for value in new_json.values() for child in value["on_children"] + value["in_children"]}

        # Filter the JSON to keep only root nodes
        filtered_json = {key: value for key, value in new_json.items() if key not in children_ids}

        # Generate the formatted string
        formatted_string = ""
        items= random.sample(room_object_indexes.items(), 2) if len(room_object_indexes.items()) > 2 else room_object_indexes.items()
        for room_type, room_objects in items:
            formatted_string += room_type.upper() + ":\n"
            extra_objects = "OTHERS:\n"
            for parent_id, children in filtered_json.items():
                if parent_id not in room_objects:
                    continue
                if children["on_children"]:
                    formatted_string += f"ON {self.convert_index_to_string(parent_id, scene_object_info)}:\n" + "".join(f"- {self.convert_index_to_string(child_id, scene_object_info)}\n" for child_id in children["on_children"])
                if children["in_children"]:
                    formatted_string += f"IN {self.convert_index_to_string(parent_id, scene_object_info)}:\n" + "".join(f"- {self.convert_index_to_string(child_id, scene_object_info)}\n" for child_id in children["in_children"])
                if (not children["on_children"]) and not (children["in_children"]):
                    extra_objects += f"{self.convert_index_to_string(parent_id, scene_object_info)}\n"
            formatted_string += extra_objects
            formatted_string += "\n"
        return formatted_string
    

    def convert_index_to_string(self, item_id, scene_object_info):
        try:
            data = scene_object_info[str(item_id)]
            category = data[0]
            description = data[1]
            if category:
                return f"{item_id}. {category} - {description}"
            else:
                return f"{item_id}. {data[2]}"
        except:
            return ""

    def generate_questions(self):
        scene_folder_list = [f.path for f in os.scandir(self.scene_folder) if f.is_dir()]
        # shuffle the list
        random.shuffle(scene_folder_list)
        # group templates into ability groups
        # Sort the data by the key to ensure groupby works correctly
        # Group the data
        grouped_templates = {k: list(v) for k, v in groupby(self.task_templates, key=itemgetter("ability"))}

        # Shuffle the keys
        keys = list(grouped_templates.keys())
        random.shuffle(keys)

        # Create a new dictionary with shuffled keys
        shuffled_templates = {key: grouped_templates[key] for key in keys}

        for scene_folder in scene_folder_list:
            count = 0
            used_objects = set()
            for sub_ability, examples in shuffled_templates.items():
                examples = [e for e in examples if e["type"]=="action"]
                example = random.choice(examples)
                ability = example["ability"]
                qa_grouped_dict, action_grouped_dict = self.group_abilities(self.task_strings)
                
                example = {k: v for k, v in example.items() if k not in ['sub_ability']}
                image_list, spatial_relations, object_description, target_objects, remaining_objects = self.get_scene_info(scene_folder, used_objects)
                task_type = random.choice(["action", "QA"])
                if not action_grouped_dict[ability]:
                    task_type = "QA"
                if not qa_grouped_dict[ability]:
                    task_type = "action"
                
                if task_type == "action":
                    example_questions = random.choice(action_grouped_dict[ability])
                else:
                    example_questions = random.choice(qa_grouped_dict[ability])
                question_prompt = self.get_question(spatial_relations, remaining_objects, task_type, target_objects, ability, example, example_questions)
                
                for i in range(10):
                    if not spatial_relations:
                        gpt_response = self.use_mm_model(image_list, question_prompt)
                    else:
                        gpt_response = gpt4_mini(content=question_prompt)
                    log_green(gpt_response)
                    question_dict = self._eval_output(gpt_response, expected_type=dict)
                    question_dict["type"] = task_type
                    if question_dict:
                        store_json(question_dict, f"{scene_folder}/question_{count}_ability_{ability}_{time_string()}.json")
                        count += 1
                        break
                
                if question_dict:
                    option_prompt = self.get_options(question_dict, spatial_relations)
                    for i in range(10):
                        gpt_response = gpt4_mini(content=option_prompt)
                        log_green(gpt_response)
                        task_dict = self._eval_output(gpt_response, expected_type=dict)
                        if task_dict:
                            try:
                                index_list = list(chain.from_iterable(task_dict["object_id"].values()))
                            except TypeError:
                                index_list = list(task_dict["object_id"].values())

                            used_objects.update(set(index_list))
                            self.used_category.update(set(task_dict["object_id"].keys()))
                            log_green(str(self.used_category))
                            task_dict["ability"] = ability
                            task_dict["template"] = example_questions
                            task_dict["solution"] = question_dict["solution"]
                            store_json(task_dict, f"{scene_folder}/task_{count}_ability_{ability}{time_string()}.json")
                            count += 1
                            break
                

    def get_options(self, task_dict, object_description):
        question = task_dict["task"]
        type = task_dict["type"]
        solution = task_dict["solution"]
        if type == "QA":
            example = str(self._remove_keys(random.choice(self.original_qa_templates)))
            prompt = QA_OPTION_GENERATE_PROMPT.format(question=question, solution=solution, example=example, object_description=object_description)
        else:
            example = str(self._remove_keys(random.choice(self.original_action_templates)))
            prompt = ACTION_OPTION_GENERATE_PROMPT.format(question=question, solution=solution, example=example, object_description=object_description)
        # print("#"*100, "\n", prompt)
        return prompt
    

    def use_mm_model(self, image_list, prompt, model="gpt-4o"):
        log_green(f"Using model {model}")
        
        while True:
            if model == "gemini":
                response = gemini(image_list, prompt)
            else:
                response = gpt_4o(image_list, prompt)
            if response:
                break
            time.sleep(self.delay_between_requests)
        return response



    def group_abilities(self, json_data):
        qa_grouped_dict = {}
        action_grouped_dict = {}
        
        for item in json_data:
            ability = item['ability']
            components = item.get('components', [])
            
            if ability not in qa_grouped_dict:
                qa_grouped_dict[ability] = []
                action_grouped_dict[ability] = []
            
            for component in components:
                qa_examples = component.get('QA', [])
                action_examples = component.get('action', [])
                qa_grouped_dict[ability].extend(qa_examples)
                action_grouped_dict[ability].extend(action_examples)
        
        return qa_grouped_dict, action_grouped_dict
    

    def collect_jsons(self, folder_path):
        task_list = []
        question_list = []

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.startswith("task") and file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    
                    relative_path = os.path.relpath(file_path, folder_path)
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    data['scene'] = relative_path
                    task_list.append(data)
                    data = {k: v for k, v in data.items() if k in ['question', 'template']}
                    question_list.append(data)

                    # Delete the file after processing
                    os.remove(file_path)
                if file.startswith("question") and file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    os.remove(file_path)
        
        
        if task_list:
            output_file = f"{folder_path}/final_task_{time_string()}.json"
            # Save the result list to a JSON file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(task_list, f, ensure_ascii=False, indent=4)

            print(f"Result saved to {output_file}")

            output_file = f"{folder_path}/final_question_{time_string()}.json"
            # Save the result list to a JSON file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(question_list, f, ensure_ascii=False, indent=4)

            print(f"Result saved to {output_file}")
        
# Example usage
if __name__ == "__main__":
    generator = TaskGenerator(eval_folder)
    # # 首先把task_strings扩充一下
    # generator.generate_additional_examples(num_examples=10)
    # exit()
    eval_folder = ""

    # ## 根据seed生成对应的task
    generator.collect_jsons(generator.scene_folder)
    generator.generate_questions()
    generator.collect_jsons(generator.scene_folder)

