import os
import pandas as pd
import json  # Added for JSON operations
from legent import load_json

PLOT = True
if PLOT:
    from plot import *
    
# Rename columns for better presentation
column_mapping_type = {
    'model_name': 'Model',
    'task_type': 'Task Type',
    'accuracy': 'Success Rate (%)',
    'avg_goal_condition_success': 'Partial Success Rate (%)',
    'success_count': 'Success Count',
    'max_step_exceed_rate': 'Max Step Exceeded Rate (%)',
    'fail_rate': 'Fail Rate (%)',  # Added fail_rate mapping
    'no_option_match_rate': 'No Option Match Rate (%)',  # Added no_option_match_rate mapping
    'option_out_of_range_rate': 'Option Out Of Range Rate (%)',  # Added option_out_of_range_rate mapping
    'api_crash_rate': 'API Crash Rate (%)',  # Added api_crash_rate mapping
    'average_trajectory_length': 'Average Trajectory Length',
    'average_spl': 'Average SPL (%)',
    'total_episodes': 'Total Episodes',
    'interaction_accuracy': 'Interaction Accuracy (%)',
    'interaction_rate': 'Interaction Rate (%)',
    }

# Map task type names to more formal versions
task_type_mapping = {
    'SpatialQA': 'Spatial QA',
    'SocialInteraction': 'Social Interaction',
    'ObjectInteraction': 'Object Interaction',
    'Navigation': 'Navigation',
    'AttributeQA': 'Attribute QA'
}

model_name_mapping = {
    'random': 'Random',
    'qwen-vl-plus': 'Qwen-VL-Plus',
    'qwen-vl-max': 'Qwen-VL-Max',
    'human': 'Human',
    'gpt-4o-mini': 'GPT-4o-Mini',
    'gpt-4o': 'GPT-4o',
    'gemini-flash': 'Gemini-Flash',
    'gemini-pro': 'Gemini-Pro',
    'VILA-40B': 'VILA-40B',
    'InternVL2-Llama3-76B': 'InternVL2-Llama3-76B',
    'LLaVA-NEXT-72B': 'LLaVA-NEXT-72B',
    'InternVL2-40B': 'InternVL2-40B',
    'LLaVA-OneVision-72B': 'LLaVA-OneVision-72B'
}

old_tasks = []
new_tasks = load_json(
    "scripts/index2json_0929.json")
# 互换键值
inverted_new_tasks = {v.split(".")[0]: k for k, v in new_tasks.items()}
# print(list(inverted_new_tasks.keys())[0])

def calculate_goal_conditioned_success(goal_condition):
    """
    Calculate the goal-conditioned success rate based on the given list of final goal conditions.
    """
    total_goals = len(goal_condition)  # Total number of goals (assumed same for all time points)
    # Return the average success rate
    return goal_condition.count(1) / total_goals

def get_subfolders(directory):
    subfolders = sorted([f.path for f in os.scandir(
        directory) if f.is_dir()], reverse=True)
    return subfolders

def replace_third_last_folder(path):
    path_parts = path.split(os.sep)
    if len(path_parts) > 4:
        path_parts[-4] = "human"
    return os.sep.join(path_parts)

def extract_dataset_and_trajectory(path):
    # Remove leading and trailing slashes and split the path into parts
    parts = path.strip('/').split('/')
    if len(parts) >= 2:
        # The dataset name is the second last part
        dataset_name = parts[-2]
        # The trajectory name is the last part
        trajectory_name = "_".join(parts[-1].split("_")[1:])
        return dataset_name + "/" + trajectory_name

# Helper function for safe division
def safe_divide(numerator, denominator):
    return round((numerator / denominator) * 100, 2) if denominator > 0 else 0

def compute_metrics_for_each_type(task_type_folder, max_step=8):
    max_step_exceeded, success, failure, errors, traj_lengths, no_option_match, option_out_of_range, api_crash = [], [], [], [], [], [], [], []
    interaction_success_count, interaction_total_count = 0, 0  # 用于计算interaction accuracy
    spls = []  # List to store SPL for each episode
    total_goal_condition_success = 0

    for episode_folder in get_subfolders(task_type_folder):
        traj_list = load_json(f"{episode_folder}/traj.json")
        try:
            optimal_traj = load_json(replace_third_last_folder(f"{episode_folder}/traj.json"))
        except:
            print(episode_folder)
        traj_lengths.append(len(traj_list))

        # 计算 done 状态
        done_status = traj_list[-1]["done_after_action"]
        
        # 计算各种错误
        final_traj = traj_list[-1]
        if done_status == 0 and len(traj_list) >= max_step and final_traj["action_choice"] not in [-1, -2, None]: # 超出一定的步长
            max_step_exceeded.append(episode_folder)
        if final_traj["action_choice"] == -1 or ("action_error" in final_traj and final_traj["action_error"] == "no option match"):
            no_option_match.append(episode_folder)
        elif final_traj["action_choice"] == -2 or ("action_error" in final_traj and final_traj["action_error"] == "option out of range"):
            option_out_of_range.append(episode_folder)
        elif final_traj["action_choice"] == None or ("action_error" in final_traj and final_traj["action_error"] == "api_crash"):
            api_crash.append(episode_folder)

        if done_status == 1:
            success.append(episode_folder) # 只有最后一步状态成功才算成功
        elif done_status == -1:
            failure.append(episode_folder) # 
        else:
            errors.append(episode_folder) # 否则都算错误（包括选错、超出步长、no option match、option out of range、api crash）
            
        # Compute SPL
        S_i = 1 if done_status == 1 else 0
        L_i = len(optimal_traj)
        P_i = len(traj_list)
        denominator = max(L_i, P_i)
        spl_i = S_i * (L_i / denominator) if denominator > 0 else 0
        spls.append(spl_i)
        
        # calculate_goal_conditioned_success
        predicates = load_json(f"{episode_folder}/task.json")["predicates"]
        if len(predicates) == 1:
            final_predicates_done = [done_status]
        else:
            final_predicates_done = traj_list[-1]["predicates_done"]

        goal_conditioned_success = calculate_goal_conditioned_success(final_predicates_done)
        total_goal_condition_success += goal_conditioned_success

        # 计算 interaction accuracy
        interaction_traj = [step for step in traj_list if step.get("feedback")] # 只有有feedback的才算interaction steps
        interaction_total_count += len(interaction_traj)  # 计算所有interaction step的总数
        interaction_success_count += sum(1 for step in interaction_traj if step["feedback"] != "failed")  # 成功interaction的数量

    total_episodes = len(success) + len(failure) + len(errors)
    assert len(errors) == len(max_step_exceeded) + len(no_option_match) + len(option_out_of_range) + len(api_crash)

    # 计算各类metrics
    accuracy = safe_divide(len(success), total_episodes)
    max_exceed_rate = safe_divide(len(max_step_exceeded), total_episodes)
    fail_rate = safe_divide(len(failure), total_episodes)  # Calculate fail rate
    no_option_match_rate = safe_divide(len(no_option_match), total_episodes)  # Calculate no_option_match_rate
    option_out_of_range_rate = safe_divide(len(option_out_of_range), total_episodes)  # Calculate option_out_of_range_rate
    api_crash_rate = safe_divide(len(api_crash), total_episodes)  # Calculate api_crash_rate
    avg_traj_length = sum(traj_lengths) / len(traj_lengths)
    avg_goal_condition_success = safe_divide(total_goal_condition_success, total_episodes)

    # 计算 interaction accuracy
    interaction_accuracy = safe_divide(interaction_success_count, interaction_total_count)

    # Compute average SPL and convert it to percentage
    average_spl = safe_divide(sum(spls), total_episodes)

    return {
        "accuracy": accuracy,
        "max_step_exceed_rate": max_exceed_rate,
        "fail_rate": fail_rate,  # Add fail_rate to the returned dictionary
        "no_option_match_rate": no_option_match_rate,  # Add no_option_match_rate
        "option_out_of_range_rate": option_out_of_range_rate,  # Add option_out_of_range_rate
        "api_crash_rate": api_crash_rate,  # Add api_crash_rate
        "average_trajectory_length": round(avg_traj_length, 2),
        "average_spl": average_spl,  # SPL now in percentage format
        "total_episodes": total_episodes,
        "success_count": len(success),
        "failure_count": len(failure),
        "max_step_exceeded_count": len(max_step_exceeded),
        "interaction_accuracy": interaction_accuracy,
        "total_interactions": interaction_total_count,
        "interaction_rate": interaction_total_count / total_episodes,
        "successful_interactions": interaction_success_count,
        "avg_goal_condition_success": avg_goal_condition_success,
        "success": success,
        "failure": failure,
        "max_exceed": max_step_exceeded
    }

def compute_metrics_for_all_types(total_result_folder, model_name):
    total_metrics = {
        "model_name": model_name,
        "accuracy": 0.0,
        "max_step_exceed_rate": 0.0,
        "fail_rate": 0.0,  # Add fail_rate to total_metrics
        "no_option_match_rate": 0.0,  # Add no_option_match_rate
        "option_out_of_range_rate": 0.0,  # Add option_out_of_range_rate
        "api_crash_rate": 0.0,  # Add api_crash_rate
        "average_trajectory_length": 0.0,
        "average_spl": 0.0,
        "total_episodes": 0,
        "success_count": 0,
        "failure_count": 0,
        "max_step_exceeded_count": 0,
        "interaction_accuracy": 0.0,
        "total_interactions": 0,
        "successful_interactions": 0,
        "avg_goal_condition_success": 0.0
    }

    type_metrics = []

    for task_type_folder in get_subfolders(total_result_folder):
        metrics = compute_metrics_for_each_type(task_type_folder)
        type_metrics.append({
            "model_name": model_name,  # Add model name for tracking
            "task_type": os.path.basename(task_type_folder),
            **{k: v for k, v in metrics.items() if k not in ["success", "failure", "max_exceed"]},  # Unpack metrics excluding lists
            "success": metrics["success"],  # Include the lists
            "failure": metrics["failure"],
            "max_exceed": metrics["max_exceed"]
        })

        # 更新总计数和总数
        total_metrics["accuracy"] += metrics["accuracy"] * metrics["total_episodes"]
        total_metrics["avg_goal_condition_success"] += metrics["avg_goal_condition_success"] * metrics["total_episodes"]
        total_metrics["max_step_exceed_rate"] += metrics["max_step_exceed_rate"] * metrics["total_episodes"]
        total_metrics["fail_rate"] += metrics["fail_rate"] * metrics["total_episodes"]  # Aggregate fail_rate
        total_metrics["no_option_match_rate"] += metrics["no_option_match_rate"] * metrics["total_episodes"]  # Aggregate no_option_match_rate
        total_metrics["option_out_of_range_rate"] += metrics["option_out_of_range_rate"] * metrics["total_episodes"]  # Aggregate option_out_of_range_rate
        total_metrics["api_crash_rate"] += metrics["api_crash_rate"] * metrics["total_episodes"]  # Aggregate api_crash_rate
        total_metrics["average_trajectory_length"] += metrics["average_trajectory_length"] * metrics["total_episodes"]
        total_metrics["average_spl"] += metrics["average_spl"] * metrics["total_episodes"]
        total_metrics["total_episodes"] += metrics["total_episodes"]
        total_metrics["success_count"] += metrics["success_count"]
        total_metrics["failure_count"] += metrics["failure_count"]
        total_metrics["max_step_exceeded_count"] += metrics["max_step_exceeded_count"]

        # 更新interaction相关的计数
        total_metrics["interaction_accuracy"] += metrics["interaction_accuracy"] * metrics["total_episodes"]
        total_metrics["total_interactions"] += metrics["total_interactions"]
        total_metrics["successful_interactions"] += metrics["successful_interactions"]

    # Normalize total metrics
    if total_metrics["total_episodes"] > 0:
        for key in ["accuracy", "avg_goal_condition_success", "max_step_exceed_rate", "fail_rate", "no_option_match_rate", "option_out_of_range_rate", "api_crash_rate", "average_trajectory_length", "interaction_accuracy", "average_spl"]:
            total_metrics[key] /= total_metrics["total_episodes"]

    total_metrics["interaction_rate"] = total_metrics["total_interactions"] / total_metrics["total_episodes"]  # Removed safe_divide
    return total_metrics, type_metrics

def compute_metrics_for_models(base_path, output_folder):
    # Ensure the output folder exists, if not, create it
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    all_total_metrics = []
    all_type_metrics = []
    final_json = []  # Added to collect final JSON data

    for model_folder in get_subfolders(base_path):
        model_name = os.path.basename(model_folder)  # Extract the model name (without full path)
        total_result_folder = os.path.join(base_path, model_name)
        total_metrics, type_metrics = compute_metrics_for_all_types(total_result_folder, model_name)
        all_total_metrics.append(total_metrics)
        all_type_metrics.extend(type_metrics)  # Combine type metrics for all models

        # Collect per task_type lists for JSON
        model_entry = {"model": model_name}
        for type_metric in type_metrics:
            task_type = type_metric["task_type"]
            model_entry[task_type] = {
                "success": type_metric["success"],
                "failure": type_metric["failure"],
                "max_exceed": type_metric["max_exceed"]
            }
        final_json.append(model_entry)  # Add the model entry to final_json

    # Save only the required columns for total_metrics_df
    total_metrics_df = pd.DataFrame(all_total_metrics)
    total_metrics_df['model_name'] = total_metrics_df['model_name'].map(model_name_mapping)
    # Rename the columns in total_metrics_df using the same mapping
    filtered_total_metrics_df = total_metrics_df.rename(columns=column_mapping_type)

    # Include the new error rates in the filtered DataFrame
    filtered_total_metrics_df = filtered_total_metrics_df[
        ['Model', 'Success Rate (%)', 'Partial Success Rate (%)', 
         'Max Step Exceeded Rate (%)', 'Fail Rate (%)', 'No Option Match Rate (%)', 
         'Option Out Of Range Rate (%)', 'API Crash Rate (%)', 
         'Average Trajectory Length', 'Average SPL (%)',
         'Interaction Accuracy (%)', 'Interaction Rate (%)']
    ]

    # Round numerical values to two decimal places
    filtered_total_metrics_df = filtered_total_metrics_df.round(2)

    # Save the updated DataFrame to a CSV file
    filtered_total_metrics_df.to_csv(os.path.join(output_folder, 'all_models_total_metrics.csv'), index=False)
    
    # Filter type_metrics_df to include task_type along with other required columns
    type_metrics_df = pd.DataFrame(all_type_metrics)
    type_metrics_df['model_name'] = type_metrics_df['model_name'].map(model_name_mapping)
    type_metrics_df['task_type'] = type_metrics_df['task_type'].map(task_type_mapping)
    filtered_type_metrics_df = type_metrics_df[
        [col for col in list(column_mapping_type.keys()) if col not in ['total_episodes', 'success_count']]  # Exclude total_episodes
    ]

    filtered_type_metrics_df = filtered_type_metrics_df.rename(columns=column_mapping_type)
    # Round numerical values to two decimal places
    filtered_type_metrics_df = filtered_type_metrics_df.round(2)
    filtered_type_metrics_df.to_csv(os.path.join(output_folder, 'all_models_type_metrics.csv'), index=False)

    # Save the final JSON with success, failure, and max_exceed lists
    final_json_path = "EmbodiedEvalData/final_results/final.json"
    with open(final_json_path, 'w') as f:
        json.dump(final_json, f, indent=4)
    print(f"Final results saved to {final_json_path}")  # Optional: Print confirmation

def convert_final(input_json_file, output_json_file):
    # Load data from the input JSON file
    with open(input_json_file, 'r') as infile:
        data = json.load(infile)

    # Extract success paths for all tasks except SpatialQA
    success_paths = {}
    for model in data:
        model_name = model["model"]
        success_paths[model_name] = []
        for task, task_data in model.items():
            if task != "model":
                success_path_list = task_data.get("success", [])
                success_paths[model_name].extend([int(inverted_new_tasks[extract_dataset_and_trajectory(success_path)]) for success_path in success_path_list])

    # Save success paths to the output JSON file
    with open(output_json_file, 'w') as outfile:
        json.dump(success_paths, outfile, indent=4)

if __name__ == "__main__":
    compute_metrics_for_models("EmbodiedEvalData/final_results", "metrics/output")
    
    convert_final("EmbodiedEvalData/final_results/final.json", "EmbodiedEvalData/final_results/final_index.json")
    
    if PLOT:
        plot_radar_chart_from_csv(
            'metrics/output/all_models_type_metrics.csv', 
            exclude_models=['Human'], 
            custom_labels_order=["Spatial QA", "Navigation", "Social Interaction", "Object Interaction", "Attribute QA"], 
            y_max=40, 
            metric_name='Average SPL (%)'
        )
        
        plot_radar_chart_from_csv(
            'metrics/output/all_models_type_metrics.csv', 
            exclude_models=['Human'], 
            custom_labels_order=["Spatial QA", "Navigation", "Social Interaction", "Object Interaction", "Attribute QA"], 
            y_max=50, 
            metric_name='Success Rate (%)'
        )
        
        plot_radar_chart_from_csv(
            'metrics/output/all_models_type_metrics.csv', 
            exclude_models=['Human'], 
            custom_labels_order=["Spatial QA", "Navigation", "Social Interaction", "Object Interaction", "Attribute QA"], 
            y_max=20, 
            metric_name='Interaction Rate (%)'
        )
        
        csv_file = 'metrics/output/all_models_total_metrics.csv'
        df = pd.read_csv(csv_file)
        # Assuming the first column is 'Model' and second is 'Step', start from third column
        metrics = df.columns[1:]
        
        # Loop through each metric and plot
        for metric in metrics:
            if metric in ["Success Count", "Total Episodes"]:
                continue
            if metric in ["Success Rate (%)", "Average SPL (%)", "Interaction Accuracy", "Partial Success Rate (%)"]:
                plot_metric_from_csv(csv_file, metric, exclude_models=['Human'])
            else:
                plot_metric_from_csv(csv_file, metric)