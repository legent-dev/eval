# gemini-pro要重新跑
ps aux | grep LEGENT | grep -v grep | awk '{print $2}' | xargs kill -15
DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 53052 --test_case_start=0 --all --rerun --no_infer
DISPLAY=:7 python run_eval.py --agent gemini-pro --max_steps 24 --max_images 24 --port 53052 --test_case_start=0 --all --rerun --no_infer
DISPLAY=:7 python run_eval.py --agent gpt-4o --max_steps 24 --max_images 24 --port 53052 --test_case_start=0 --all --rerun --no_infer
DISPLAY=:7 python run_eval.py --agent gpt-4o-mini --max_steps 24 --max_images 24 --port 53052 --test_case_start=0 --all --rerun --no_infer
DISPLAY=:7 python run_eval.py --agent human --max_steps 24 --max_images 24 --port 53052 --test_case_start=0 --all --rerun --no_infer
DISPLAY=:7 python run_eval.py --agent qwen-vl-max --max_steps 24 --max_images 24 --port 53052 --test_case_start=0 --all --rerun --no_infer
DISPLAY=:7 python run_eval.py --agent qwen-vl-plus --max_steps 24 --max_images 24 --port 53052 --test_case_start=0 --all --rerun --no_infer
DISPLAY=:7 python run_eval.py --agent random --max_steps 24 --max_images 24 --port 53052 --test_case_start=0 --all --rerun --no_infer

# DISPLAY=:7 python run_eval.py --agent gemini-pro --max_steps 24 --max_images 24 --port 53052 --test_case_start=218 --test_case_end=330 --all --rerun


# # python /data41/private/legent/eval/metrics/case_study.py human
# python /data41/private/legent/eval/metrics/case_study.py gemini-flash
# python /data41/private/legent/eval/metrics/case_study.py gemini-pro
# python /data41/private/legent/eval/metrics/case_study.py gpt-4o
# python /data41/private/legent/eval/metrics/case_study.py gpt-4o-mini
# python /data41/private/legent/eval/metrics/case_study.py qwen-vl-max
# python /data41/private/legent/eval/metrics/case_study.py qwen-vl-plus


# 把文件上传到HF
# # python /data41/private/legent/eval/metrics/zip_file.py
# python /data41/private/tuyuge/scenecraft/scripts/bash/upload_to_hf.py total_cases.zip


# ps aux | grep LEGENT | grep -v grep | awk '{print $2}' | xargs kill -15
# DISPLAY=:7 python run_eval.py --agent gemini-pro --max_steps 24 --max_images 24 --port 53054 --test_case_start=280 --test_case_end=330 --all
# DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 8 --port 53052 --test_case_start=0 --all --rerun
# python /data41/private/tuyuge/concate.py /data41/private/legent/eval/EmbodiedEvalData/final_results/human/ObjectInteraction

# python /data41/private/tuyuge/scenecraft/scripts/bash/upload_to_hf.py /data41/private/legent/eval/human_trajectories.zip


# python /data41/private/tuyuge/concate.py /data41/private/legent/eval/EmbodiedEvalData/final_results/human/Navigation

# python /data41/private/tuyuge/concate.py /data41/private/legent/eval/EmbodiedEvalData/final_results/human/AttributeQA

# python /data41/private/tuyuge/concate.py /data41/private/legent/eval/EmbodiedEvalData/final_results/human/SpatialQA
# DISPLAY=:7 python run_eval.py --agent random --max_steps 24 --max_images 24 --port 50054 --test_case_start=0 --all

# # ### 最后 重跑不要thought
# # DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 53081 --test_case_start=0 --all --rerun

# # 重跑
# # DISPLAY=:7 python run_eval.py --agent qwen-vl-plus --max_steps 24 --max_images 24 --port 50054 --test_case_start=0 --all
# # DISPLAY=:7 python run_eval.py --agent qwen-vl-max --max_steps 24 --max_images 16 --port 50054 --test_case_start=0 --all
# # # random
# python /data41/private/legent/eval/metrics/merge_results.py qwen-vl-max
# python /data41/private/legent/eval/metrics/merge_results.py gemini-flash
# python /data41/private/legent/eval/metrics/merge_results.py gpt-4o-mini
# python /data41/private/legent/eval/metrics/merge_results.py qwen-vl-plus
# python /data41/private/legent/eval/metrics/merge_results.py human
# python /data41/private/legent/eval/metrics/merge_results.py random
# # python /data41/private/legent/eval/metrics/metrics.py


# 跑完以后记得把这四个文件夹都放上merge里面，也就是最近的文件夹，然后最后merge一遍，确认无误之后就算metrics
# DISPLAY=:7 python run_eval.py --agent qwen-vl-plus --max_steps 24 --max_images 24 --port 50054 --test_case_start=0 --all
# DISPLAY=:7 python run_eval.py --agent qwen-vl-max --max_steps 24 --max_images 8 --port 50052 --test_case_start=0 --all
# DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 53051 --test_case_start=0 --all
# DISPLAY=:7 python run_eval.py --agent gpt-4o-mini --max_steps 24 --max_images 24 --port 53053 --test_case_start=0 --all
# # folder=/data41/private/legent/eval/EmbodiedEvalData/final_tasks
# # task_name=SpatialQA/task-20240930022748-livingroom_15_scene_8-Considering_the_layout_of_the_house,_where_is_the_best_location_to_install_a_TV_to_achieve_a_evenly_distributed_viewing_experience____.json
# task_path="$folder/$task_name"

# # 最后跑新的task
# DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 51181 --run_one_task_instance "$task_path"
# DISPLAY=:7 python run_eval.py --agent gpt-4o --max_steps 24 --max_images 24 --port 51182 --run_one_task_instance "$task_path"

# DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 51181 --run_one_task_instance "$task_path"

# DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 51181 --run_one_task_instance "$task_path"

# 注意gemini，gpt4o和qwen需要多跑的是后来的missing，这些才是真正需要重新跑的，只能把这些更新到final_results中

# 明天要跑的：全部跑一遍
#### gemini-pro需要反复执行下面的： 9103 2 跑全新的gemini pro
# ps aux | grep LEGENT | grep -v grep | awk '{print $2}' | xargs kill -15
# python /data41/private/legent/eval/metrics/merge_results.py gemini-pro
# DISPLAY=:7 python run_eval.py --agent gemini-pro --max_steps 24 --max_images 24 --port 53051 --test_case_start=0 --all


# ### 已经跑了：
# 9101 做数据分析
# ps aux | grep LEGENT | grep -v grep | awk '{print $2}' | xargs kill -15
# python /data41/private/legent/eval/metrics/merge_results.py gpt-4o
# python /data41/private/legent/eval/metrics/merge_results.py gemini-flash
# ### 已经跑了：
# 9102 0 在跑所有剩余的task
# ps aux | grep LEGENT | grep -v grep | awk '{print $2}' | xargs kill -15
# python /data41/private/legent/eval/metrics/merge_results.py qwen-vl-max
# DISPLAY=:7 python run_eval.py --agent qwen-vl-max --max_steps 24 --max_images 16 --port 50053 --test_case_start=0 --all

# DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 53051 --test_case_start=0 --all
# DISPLAY=:7 python run_eval.py --agent gpt-4o --max_steps 24 --max_images 24 --port 50052 --test_case_start=0 --all

# DISPLAY=:7 python run_eval.py --agent qwen-vl-plus --max_steps 24 --max_images 24 --port 50054 --test_case_start=0 --all

# ### 已经跑了：
# DISPLAY=:7 python run_eval.py --agent gpt-4o-mini --max_steps 24 --max_images 24 --port 54051 --test_case_start=0 --all
# ### 已经跑了：
# DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 1 --port 53051 --test_case_start=0 --all
# DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 8 --port 53052 --test_case_start=0 --all

# #
# DISPLAY=:7 python run_eval.py --agent qwen-vl-max --max_steps 24 --max_images 16 --port 50051 --test_case_start=0 --all

# #
# # 只输出choice的要跑
# DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 53051 --test_case_start=0 --all


# # random
# DISPLAY=:7 python run_eval.py --agent random --max_steps 24 --max_images 24 --port 50090 --test_case_start=0 --all


# # gpt4-o
# DISPLAY=:7 python run_eval.py --agent gpt-4o --max_steps 24 --max_images 24 --port 50051 --test_case_start=0 --all
# DISPLAY=:7 python run_eval.py --agent gpt-4o --max_steps 24 --max_images 24 --port 50051 --test_case_start=0 --test_case_end=110 --all
# DISPLAY=:7 python run_eval.py --agent gpt-4o --max_steps 24 --max_images 24 --port 50052 --test_case_start=110 --test_case_end=220 --all
# DISPLAY=:7 python run_eval.py --agent gpt-4o --max_steps 24 --max_images 24 --port 50053 --test_case_start=220 --test_case_end=270 --all
# DISPLAY=:7 python run_eval.py --agent gpt-4o --max_steps 24 --max_images 24 --port 50054 --test_case_start=270 --test_case_end=328 --all

# # gemini-pro
# DISPLAY=:7 python run_eval.py --agent gemini-pro --max_steps 24 --max_images 24 --port 50051 --test_case_start=0 --all
# DISPLAY=:7 python run_eval.py --agent gemini-pro --max_steps 24 --max_images 24 --port 50061 --test_case_start=0 --test_case_end=110 --all
# DISPLAY=:7 python run_eval.py --agent gemini-pro --max_steps 24 --max_images 24 --port 50062 --test_case_start=110 --test_case_end=220 --all
# DISPLAY=:7 python run_eval.py --agent gemini-pro --max_steps 24 --max_images 24 --port 50063 --test_case_start=220 --test_case_end=330 --all

# # qwen-vl
# DISPLAY=:7 python run_eval.py --agent qwen-vl --max_steps 24 --max_images 24 --port 50051 --test_case_start=0 --all
# DISPLAY=:7 python run_eval.py --agent qwen-vl --max_steps 24 --max_images 24 --port 50071 --test_case_start=0 --test_case_end=110 --all
# DISPLAY=:7 python run_eval.py --agent qwen-vl --max_steps 24 --max_images 24 --port 50072 --test_case_start=110 --test_case_end=220 --all
# DISPLAY=:7 python run_eval.py --agent qwen-vl --max_steps 24 --max_images 24 --port 50073 --test_case_start=220 --test_case_end=330 --all

# # gemini-flash
# DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 53051 --test_case_start=0 --all
# DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 50081 --test_case_start=0 --test_case_end=110 --all
# DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 50082 --test_case_start=110 --test_case_end=220 --all
# DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 50083 --test_case_start=220 --test_case_end=330 --all

# # qwen-vl-plus
# DISPLAY=:7 python run_eval.py --agent qwen-vl-plus --max_steps 24 --max_images 24 --port 50070 --test_case_start=0 --all
# DISPLAY=:7 python run_eval.py --agent qwen-vl-plus --max_steps 24 --max_images 24 --port 50071 --test_case_start=0 --test_case_end=110 --all
# DISPLAY=:7 python run_eval.py --agent qwen-vl-plus --max_steps 24 --max_images 24 --port 50072 --test_case_start=110 --test_case_end=220 --all
# DISPLAY=:7 python run_eval.py --agent qwen-vl-plus --max_steps 24 --max_images 24 --port 50073 --test_case_start=220 --test_case_end=330 --all


# # gpt-4o-mini
# DISPLAY=:7 python run_eval.py --agent gpt-4o-mini --max_steps 24 --max_images 24 --port 54051 --test_case_start=0 --all
# DISPLAY=:7 python run_eval.py --agent gpt-4o-mini --max_steps 24 --max_images 24 --port 54081 --test_case_start=0 --test_case_end=110 --all
# DISPLAY=:7 python run_eval.py --agent gpt-4o-mini --max_steps 24 --max_images 24 --port 54082 --test_case_start=110 --test_case_end=220 --all
# DISPLAY=:7 python run_eval.py --agent gpt-4o-mini --max_steps 24 --max_images 24 --port 54083 --test_case_start=220 --test_case_end=330 --all



# # gemini-flash
# # DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 50072 --test_case_start=110 --test_case_end=220 --all
# # DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 50080 --test_case_start=200 --test_case_end=400 --all



# # ps aux | grep LEGENT
# # ps aux | grep LEGENT | grep -v grep | awk '{print $2}' | xargs kill -15
# # 




# python /data41/private/tuyuge/concate.py /data41/private/legent/eval/EmbodiedEvalData/results/20240927-115616-434135-random-step24-image24-case124




# DISPLAY=:7 python run_eval.py --agent random --max_steps 24 --max_images 24 --port 50051 --test_case_start=0 --all
# DISPLAY=:7 python run_eval.py --agent gpt-4o --max_steps 32 --max_images 25 --port 50051 --test_case_start=0 --all
# DISPLAY=:7 python run_eval.py --agent gemini-pro --max_steps 32 --max_images 25 --port 50051 --test_case_start=0 --all


# DISPLAY=:7 python run_eval.py --agent qwen-vl --max_steps 32 --max_images 25 --port 50051 --test_case_start=0 --all
# DISPLAY=:7 python run_eval.py --agent gpt-4o --max_steps 32 --max_images 25 --port 50051 --test_case_start=91 --test_case_end=182 --all
# DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 50051 --test_case_start=91 --test_case_end=182 --all
# DISPLAY=:7 python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 50050 --test_case_start=0 --test_case_end=400 --all

# python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 50011 --sync --run_one_task_instance /data41/private/legent/eval/EmbodiedEvalData/tasks/AttributeQA/task-20240920203402-FloorPlan5_physics-Inventory_the_item_in_the_black_refrigerator_and_place_it_in_the_sink_.json

# python run_eval.py --agent gemini-flash --max_steps 24 --max_images 24 --port 50051 --sync --run_one_task_instance /data41/private/legent/eval/EmbodiedEvalData/tasks/AttributeQA/task-20240913133202-102344094-Evaluate_whether_the_painting_above_the_living_room_sofa_is_more_colorful_than_the_carpet_.json

# python run_eval.py --agent human --max_steps 2500 --max_images 25 --port 50058 --test_case_start=14 --test_case_end=100
# python run_eval.py --agent gpt-4o --max_steps 25 --max_images 25 --port 50054 --sync
# python run_eval.py --agent gemini-flash --max_steps 25 --max_images 25 --port 50058 --sync --test_case_start=0 --test_case_end=100
# python run_eval.py --agent rotate --max_steps 25 --max_images 25 --port 50058 --sync --test_case_start=0 --test_case_end=100
# python run_eval.py --agent random --max_steps 3 --max_images 25 --port 50051 --sync --test_case_start=0 --test_case_end=100

# python run_eval.py --agent human --max_steps 30 --max_images 25 --port 50051 --sync --run_one_task_instance F:/UnityProjects/SceneProcessor/Assets/Tasks/task-20240912043700-102344094-Is_my_computer_on_in_the_bedroom_.json
# python run_eval.py --agent human --max_steps 30 --max_images 25 --port 50051 --sync --run_one_task_instance F:/Downloads/task-20240913110854-FloorPlan11_physics-Check_what_s_on_the_other_side_of_the_bread__.json


# python run_eval.py --agent human --max_steps 30 --max_images 25 --port 50051 --sync --run_one_task_instance F:/UnityProjects/SceneProcessor/Assets/Tasks/task-20240915152356-102344280-Reach_the_front_door_after_passing_through_the_hallway_and_turning_right__.json

# 运行所有测例
# python run_eval.py --agent human --max_steps 2500 --max_images 25 --port 50051 --test_case_start=0 --test_case_end=100 --all --rerun

    
