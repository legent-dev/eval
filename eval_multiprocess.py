import sys
import multiprocessing
import os
from legent.utils.io import time_string
from .eval import run_eval


if __name__ == "__main__":
    processes = []

    # 创建并启动10个进程
    for i in range(10):
        eval_folder = "./eval_folder_20240614_0251"
        eval_folder = os.path.abspath(eval_folder)
        agent = "gpt-4o"
        test_case_start = 10 * i
        max_steps = 25
        max_images = 3
        port = 51000 + i
        save_path = f"{eval_folder}/results/{time_string()}-{agent.model_name}/{i}"
        p = multiprocessing.Process(target=run_eval, args=(agent, test_case_start, max_steps, max_images, port, save_path))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()
