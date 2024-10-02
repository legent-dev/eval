"""
每次跑完的例子在这里合并为一个文件夹
"""

import os
from legent import load_json, store_json
from legent.utils.io import log_green
import shutil
from concurrent.futures import ThreadPoolExecutor
import glob
import re

COVER = False # 把之前所有的文件夹覆盖掉（删掉）


def get_subfolders(directory):
    subfolders = sorted([f.path for f in os.scandir(
        directory) if f.is_dir()], reverse=True)
    return subfolders

old_tasks = []
new_tasks = load_json(
    "/data41/private/legent/eval/scripts/index2json_0929.json")
# 互换键值
inverted_new_tasks = {v.split("/")[-1]: [k,v.split("/")[0]] for k, v in new_tasks.items()}

# if COPY:
results_folder = "/data41/private/legent/eval/EmbodiedEvalData/final_results"
# else:
#     results_folder = "/data41/private/legent/eval/EmbodiedEvalData/missing_results"
os.makedirs(results_folder, exist_ok=True)

def get_already_complete_tasks(model_results_folder):
    # Use glob to find all sub-subdirectories
    sub_sub_dirs = glob.glob(os.path.join(model_results_folder, '*/*/'), recursive=False)
    # Convert absolute paths to relative paths
    relative_paths = [re.sub(r'traj\d{4}_', '', os.path.relpath(path, model_results_folder)) for path in sub_sub_dirs]
    return relative_paths

def record_episode(episode_folder, max_step=20):
    # first check if trajectory is complete and there is no api_crash
    complete = False 
    files = sorted(f for f in os.listdir(episode_folder) if f.endswith("a.json"))
    result_list = []
    for file_name in files:
        data = load_json(f"{episode_folder}/{file_name}")
        result = {k:v for k,v in data.items() if k not in "payload"}
        result_list.append(result)
        
        # check response == option
        # 匹配错误的要重新跑
        # response = result["response"]
        # if response:
        #     # new action choice
        #     try:
        #         # Match "Choice: [4]" or "Choice: 4" using a regular expression
        #         action_choice = int(re.search(r"Choice:?[\n\s]*\[?(\d+)\]?", response, re.IGNORECASE).group(1))
        #     except:
        #         try:
        #             action_choice = int(re.search(r"(\d+)(?!.*\d)", response, re.DOTALL).group(1))
        #         except:
        #             action_choice = -1 # cannot match any number
                    
        #     try:
        #         original_action_choice = int(re.search(r"\[(\d+)\]", response).group(1))
        #     except:
        #         try:
        #             original_action_choice = int(re.search(r"(\d+)", response).group(1))
        #         except:
        #             original_action_choice = -1

        #     # print(episode_folder, action_choice)
        #     if action_choice != original_action_choice: #如果不匹配就不完整
        #         return complete
    if result_list:
        # # # 成功或失败说明是完整的
        if result_list[-1]["done_after_action"] in [1, -1]:
            complete = True
        # 只要不是api_crash导致结束的，也算作完整 比如这种情况："option out of range", -2
        elif "action_error" in result_list[-1] and result_list[-1]["action_error"] not in ["api_crash"]:
            complete = True 
         # 达到最大步数，且action不是空，也是完整的
        elif len(result_list) >= max_step and "action" in result_list[max_step-1] and result_list[max_step-1]["action"]:
            complete = True   
    else:
        log_green(f"Empty traj: {episode_folder}")  

    store_json(result_list, f"{episode_folder}/traj.json")
    return complete

def merge_folders(cases_folder, model, results_folder, max_step=20):
    '''
    把所有实例的folders复制到汇总的新文件夹，每个episode命名为task编号+task全名
    '''
    tasks_to_copy = {}
    incomplete_tasks = {}
    model_results_folder = f"{results_folder}/{model}"
            
    already_complete_tasks = get_already_complete_tasks(model_results_folder)
                    
    for episode_folder in get_subfolders(cases_folder):  # 从新到旧
        task_data = load_json(f"{episode_folder}/task.json")
        save_path = task_data["scene"]["task_instance"]["savePath"]
        task_name = save_path.replace("\\","/").split("/")[-1]
        if task_name.split("-")[-1] == "Assess_whether_the_painting_on_the_sofa_in_the_living_room_is_more_colorful_than_the_carpet_.json":
            task_name = "task-20240913133202-102344094-Evaluate_whether_the_painting_above_the_living_room_sofa_is_more_colorful_than_the_carpet_.json"
        if record_episode(episode_folder, max_step=max_step): # 
            try:
                # 根据task_name找到对应的索引
                task_i, task_type = inverted_new_tasks[task_name]
                traj_save_dir = f"{model_results_folder}/{task_type}/traj{int(task_i):04d}_{task_name.split('.')[0]}"
                tasks_to_copy[task_name] = [episode_folder, traj_save_dir]
            except Exception as e:
                print(e)
                # 如果找不到，说明这个task是旧的
                old_tasks.append(task_name)
                continue
        else:
            incomplete_tasks[task_name] = episode_folder
    return tasks_to_copy, incomplete_tasks, already_complete_tasks
    
def copy_folder_task(v):
    episode_folder, traj_save_dir = v[0], v[1]
    try:
        shutil.copytree(episode_folder, traj_save_dir, dirs_exist_ok=True)
        # print(f"Copy folder success: '{episode_folder}'")
    except Exception as e:
        print(f"Error during copying: {e}")

    # After copying, remove empty task_raw.json if it exists and is empty
    file_path = os.path.join(episode_folder, "task_raw.json")
    if os.path.exists(file_path):
        data = load_json(file_path)
        if not data:
            os.remove(file_path)

def copy_folders(all_folders_to_copy):
    with ThreadPoolExecutor() as executor:
        executor.map(copy_folder_task, all_folders_to_copy.values())

def merge_folders_for_model(folders_to_merge, model, max_step=20):
    print("#"*50)
    log_green(model)
    all_folders_to_copy = {}
    all_incomplete_tasks = {}
    for folder in folders_to_merge:
        tasks_to_copy, incomplete_tasks, already_complete_tasks = merge_folders(folder, model, results_folder)
        all_folders_to_copy.update(tasks_to_copy)
        all_incomplete_tasks.update(incomplete_tasks)
    
    if COVER:
        model_results_folder = f"{results_folder}/{model}"
        # 如果模型的文件夹存在，删除这个文件夹中的所有内容
        if os.path.exists(model_results_folder):
            shutil.rmtree(model_results_folder)  # 删除文件夹及其所有内容
            print("delete the folder", model_results_folder)
            os.makedirs(model_results_folder)    # 重新创建文件夹
        else:
            os.makedirs(model_results_folder)
            
    copy_folders(all_folders_to_copy)
    
    print(f"There are {len(old_tasks)} old tasks not to be copied!")
    print(old_tasks)
    print(f"There are {len(all_folders_to_copy)} folders to be copied")
    # 找出所有不完整的tasks，这些需要重新做
    
    # 找出没有测到的folder，这些也需要测
    all_incomplete_tasks_keys = [item.split("/")[-1] for item in new_tasks.values() if item.split("/")[-1] in all_incomplete_tasks]
    all_incomplete_tasks = {k:v for k,v in all_incomplete_tasks.items() if k in all_incomplete_tasks_keys}
    print(f"There are {len(all_incomplete_tasks)} incomplete tasks, please go to ", f"{results_folder}/{model}/all_incomplete_tasks.json")
    store_json(all_incomplete_tasks, f"{results_folder}/{model}/all_incomplete_tasks.json")
    
    # 找出没有测到的folder，这些也需要测
    missed_tasks = [item for item in new_tasks.values() if item.split("/")[-1] not in all_folders_to_copy and item.split(".")[0] not in already_complete_tasks]
    print(f"There are {len(missed_tasks)} missing tasks to run, please go to ", f"{results_folder}/{model}/missed_tasks.json")

    store_json(missed_tasks, f"{results_folder}/{model}/missed_tasks.json")


import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: python script_name.py <model>")
        sys.exit(1)
    
    model = sys.argv[1]
    
    if model == "human":
        print("Add the folder to copy")
        folders_to_merge = [
            "/data41/private/legent/eval/EmbodiedEvalData/results/traj-human_0930" 
        ]
        merge_folders_for_model(folders_to_merge, model)

    elif model == "gemini-pro":
        print("Add the folder to copy")
        folders_to_merge = [
            "/data41/private/legent/eval/EmbodiedEvalData/results/20240929-183025-985943-gemini-pro-step24-image24-case0",
            "/data41/private/legent/eval/EmbodiedEvalData/results/20240929-231631-935423-gemini-pro-step24-image24-case0",
            "/data41/private/legent/eval/EmbodiedEvalData/results/20240930-072746-149158-gemini-pro-step24-image24-case230",
            "/data41/private/legent/eval/EmbodiedEvalData/results/20240930-072904-057852-gemini-pro-step24-image24-case280"
        ]
        merge_folders_for_model(folders_to_merge, model)

    elif model == "qwen-vl-max":
        folders_to_merge = (
            get_subfolders("/data41/private/legent/eval/EmbodiedEvalData/reported_results/qwen")
            + 
            [
                "/data41/private/legent/eval/EmbodiedEvalData/results/20240928-220458-777978-qwen-vl-step24-image24-case0",
                "/data41/private/legent/eval/EmbodiedEvalData/results/20240929-233448-051900-qwen-vl-max-step24-image16-case0",
                "/data41/private/legent/eval/EmbodiedEvalData/results/20240930-051735-574957-qwen-vl-max-step24-image16-case0",
                "/data41/private/legent/eval/EmbodiedEvalData/results/20240930-063626-094235-qwen-vl-max-step24-image8-case0"
            ]
        )
        merge_folders_for_model(folders_to_merge, model, max_step=16)

    elif model == "gpt-4o-mini":
        folders_to_merge = [
            "/data41/private/legent/eval/EmbodiedEvalData/results/20240929-014822-431803-gpt-4o-mini-step24-image24-case0",
            "/data41/private/legent/eval/EmbodiedEvalData/results/20240929-185717-697021-gpt-4o-mini-step24-image24-case0",
            "/data41/private/legent/eval/EmbodiedEvalData/results/20240930-065602-854388-gpt-4o-mini-step24-image24-case0" 
        ]
        merge_folders_for_model(folders_to_merge, model)

    elif model == "qwen-vl-plus":
        folders_to_merge = [
            "/data41/private/legent/eval/EmbodiedEvalData/results/20240929-021800-251259-qwen-vl-plus-step24-image24-case0",
            "/data41/private/legent/eval/EmbodiedEvalData/results/20240929-101336-078598-qwen-vl-plus-step24-image24-case0",
            "/data41/private/legent/eval/EmbodiedEvalData/results/20240930-051148-108512-qwen-vl-plus-step24-image24-case0"
        ]
        merge_folders_for_model(folders_to_merge, model)

    elif model == "gpt-4o":
        folders_to_merge = (
            # get_subfolders("/data41/private/legent/eval/EmbodiedEvalData/reported_results/gpt-4o")
            # + 
            [
                # "/data41/private/legent/eval/EmbodiedEvalData/results/20240928-213103-435426-gpt-4o-step24-image24-case0",
                # "/data41/private/legent/eval/EmbodiedEvalData/results/20240929-193624-455703-gpt-4o-step24-image24-case0",
                "/data41/private/legent/eval/EmbodiedEvalData/results/20240930-055502-647410-gpt-4o-step24-image24-case0"
            ]
        )
        merge_folders_for_model(folders_to_merge, model)

    elif model == "gemini-flash":
        folders_to_merge = (
            get_subfolders("/data41/private/legent/eval/EmbodiedEvalData/reported_results/gemini-flash")
            + 
            [
                "/data41/private/legent/eval/EmbodiedEvalData/results/20240928-213756-009977-gemini-flash-step24-image24-case0",
                # "/data41/private/legent/eval/EmbodiedEvalData/results/20240929-122803-489394-gemini-flash-step24-image24-case0"
                "/data41/private/legent/eval/EmbodiedEvalData/results/20240929-185620-558545-gemini-flash-step24-image24-case0",
                "/data41/private/legent/eval/EmbodiedEvalData/results/20240930-055732-215224-gemini-flash-step24-image24-case0"
            ]
        )
        merge_folders_for_model(folders_to_merge, model)

    elif model == "random":
        folders_to_merge = (
            get_subfolders("/data41/private/legent/eval/EmbodiedEvalData/reported_results/random")
            + 
            [
                "/data41/private/legent/eval/EmbodiedEvalData/results/20240928-185208-460531-random-step24-image25-case0",
                "/data41/private/legent/eval/EmbodiedEvalData/results/20240930-085320-003201-random-step24-image24-case0"
            ]
        )
        merge_folders_for_model(folders_to_merge, model)

    else:
        print(f"Model '{model}' is not recognized.")
        sys.exit(1)

if __name__ == "__main__":
    main()

    
     

    
    
    
    
    
    