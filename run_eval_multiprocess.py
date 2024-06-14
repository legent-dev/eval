import sys
import multiprocessing
import os
from legent.utils.io import time_string, store_json
from run_eval import run_eval


if __name__ == "__main__":
    processes = []

    eval_folder = "./eval_folder_20240614_0251"
    eval_folder = os.path.abspath(eval_folder)
    agent = "gpt-4o"
    max_steps = 25
    max_images = 3
    save_path_prefix = f"{eval_folder}/results/{time_string()}-{agent}"
    os.makedirs(save_path_prefix)
    run_args = {"agent": agent, "max_steps": max_steps, "max_images": max_images}
    store_json(run_args, f"{save_path_prefix}/run_args.json")

    for i in range(10):
        test_case_start = 10 * i
        test_case_end = test_case_start + 10
        port = 52000 + i * 2
        save_path = f"{save_path_prefix}/{i}"
        p = multiprocessing.Process(target=run_eval, args=(agent, test_case_start, test_case_end, max_steps, max_images, port, save_path))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()
