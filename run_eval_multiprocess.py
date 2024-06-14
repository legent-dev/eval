import sys
import multiprocessing
import os
from legent.utils.io import time_string, store_json, load_json
from run_eval import run_eval
from task import get_task_settings


def sumup(result_folder):
    result_folder = os.path.abspath(result_folder)
    dirs = [dir for dir in os.listdir(result_folder) if os.path.isdir(f"{result_folder}/{dir}")]
    failed = []
    acc_count, total_count = 0, 0
    for dir in dirs:
        res = load_json(f"{result_folder}/{dir}/result_temp.json")
        acc, total = res["Success Rate"].split("/")
        acc_count += int(acc)
        total_count += int(total)

    result = {"Success Rate": f"{acc_count}/{total_count}", "failed cases": failed}
    store_json(result, f"{result_folder}/result.json")
    exit(0)


# sumup("./eval_folder_20240614_0251/results/20240614-222415-579503-gpt-4o")
# exit(0)
if __name__ == "__main__":
    processes = []

    eval_folder = "./eval_folder_20240614_0251"
    eval_folder = os.path.abspath(eval_folder)
    task_settings = get_task_settings(eval_folder)
    agent = "gpt-4o"
    max_steps = 25
    max_images = 1
    save_path_prefix = f"{eval_folder}/results/{time_string()}-{agent}"
    os.makedirs(save_path_prefix)
    run_args = {"agent": agent, "max_steps": max_steps, "max_images": max_images, "max_images_history": max_images - 1}
    store_json(run_args, f"{save_path_prefix}/run_args.json")

    for i in range(10):
        test_case_start = 10 * i
        test_case_end = test_case_start + 10
        # test_case_start = 50 + i
        # test_case_end = test_case_start + 1
        port = 52000 + i * 2
        save_path = f"{save_path_prefix}/{i}"
        p = multiprocessing.Process(target=run_eval, args=(agent, test_case_start, test_case_end, max_steps, max_images, port, eval_folder, save_path, task_settings))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()
    sumup(save_path_prefix)
