import sys
import multiprocessing
import os
from legent.utils.io import time_string
from run_eval import run_eval


if __name__ == "__main__":
    processes = []

    eval_folder = "./eval_folder_20240614_0251"
    eval_folder = os.path.abspath(eval_folder)
    agent = "gpt-4o"
    max_steps = 25
    save_path_prefix = f"{eval_folder}/results/{time_string()}-{agent}"
    max_images = 3
    for i in range(10):
        test_case_start = 10 * i
        port = 52000 + i*2
        save_path = f"{save_path_prefix}/{i}"
        p = multiprocessing.Process(target=run_eval, args=(agent, test_case_start, max_steps, max_images, port, save_path))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()
