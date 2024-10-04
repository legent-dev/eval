from legent import load_json, store_json
import os
old_tasks = load_json(
    "/data41/private/legent/eval/scripts/index2json_0928.json")
new_tasks = load_json(
    "/data41/private/legent/eval/scripts/index2json_0929.json")
new_tasks = set(new_tasks.values())

def get_subfolders(directory):
    subfolders = sorted([f.path for f in os.scandir(
        directory) if f.is_dir()], reverse=True)
    # 文件夹顺序不同会导致结果不同
    # import random
    # random.shuffle(subfolders)
    return subfolders


def compute_tested(_folder):
    failed_case = set()
    success_case = set()
    for folder in get_subfolders(_folder):  # 从新到旧
        result = load_json(f"{folder}/result_temp.json")
        for case in result["failed cases"]:
            if (case not in success_case) and (case not in failed_case):
                failed_case.add(case)
        for case in result["success cases"]:
            if (case not in success_case) and (case not in failed_case):
                success_case.add(case)
    failed_cases = [old_tasks[i] for i in old_tasks if int(i) not in success_case]
    success_cases = [old_tasks[str(i)] for i in success_case]
    # print(len(success_case)/(len(failed_case)+len(success_case)))
    # print(len(success_case),"/",len(failed_case)+len(success_case))
    # print(failed_case)
    # print(success_case)
    # print(failed_cases)
    # print(success_cases)
    new_failed_cases = []
    new_success_cases = []
    for case in failed_cases:
        if case in new_tasks:
            new_failed_cases.append(case)
    for case in success_cases:
        if case in new_tasks:
            new_success_cases.append(case)
    failed_cases, success_cases = new_failed_cases, new_success_cases
    # print(failed_cases)
    # print(success_cases)
    # print(failed_case)
    # print(success_case)
    print(len(success_cases)/(len(failed_cases)+len(success_cases)))
    print(len(success_cases), "/", len(failed_cases)+len(success_cases))
    total_cases = []
    total_cases.extend(failed_cases)
    total_cases.extend(success_cases)
    return total_cases, failed_cases, success_cases



def get_gpt4o_partial_final_results():
    total, failed, success = compute_tested("/data41/private/legent/eval/EmbodiedEvalData/reported_results/gpt4-o")
    total = set([task.split("/")[1] for task in total])
    store_json(failed, "/data41/private/legent/eval/scripts/yuge_results/gpt-4o/failed.json")
    store_json(success, "/data41/private/legent/eval/scripts/yuge_results/gpt-4o/success.json")
    return total

def get_gemini_flash_partial_final_results():
    total, failed, success = compute_tested("/data41/private/legent/eval/EmbodiedEvalData/reported_results/gemini-flash")
    total = set([task.split("/")[1] for task in total])
    store_json(failed, "/data41/private/legent/eval/scripts/yuge_results/gemini-flash/failed.json")
    store_json(success, "/data41/private/legent/eval/scripts/yuge_results/gemini-flash/success.json")
    return total

def get_qwen_partial_final_results():
    total, failed, success = compute_tested("/data41/private/legent/eval/EmbodiedEvalData/reported_results/qwen")
    store_json(failed, "/data41/private/legent/eval/scripts/yuge_results/qwen/failed.json")
    store_json(success, "/data41/private/legent/eval/scripts/yuge_results/qwen/success.json")
    total = set([task.split("/")[1] for task in total])
    return total

if __name__ == "__main__":
    print("4o")
    get_gpt4o_partial_final_results()
    print("flash")
    get_gemini_flash_partial_final_results()
    print("qwen")
    get_qwen_partial_final_results()