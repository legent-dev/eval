import os
import pandas as pd
from legent import load_json
from plot import plot_radar_chart_from_csv

def get_subfolders(directory):
    subfolders = sorted([f.path for f in os.scandir(
        directory) if f.is_dir()], reverse=True)
    return subfolders

def replace_third_last_folder(path):
    path_parts = path.split(os.sep)
    if len(path_parts) > 4:
        path_parts[-4] = "human"
    return os.sep.join(path_parts)

# Helper function for safe division
def safe_divide(numerator, denominator):
    return round((numerator / denominator) * 100, 2) if denominator > 0 else 0
    
def compute_metrics_for_each_type(task_type_folder):
    max_step_exceeded, success, failure, traj_lengths = [], [], [], []
    interaction_success_count, interaction_total_count = 0, 0  # 用于计算interaction accuracy
    spls = []  # List to store SPL for each episode

    for episode_folder in get_subfolders(task_type_folder):
        traj_list = load_json(f"{episode_folder}/traj.json")
        optimal_traj = load_json(replace_third_last_folder(f"{episode_folder}/traj.json"))
        traj_lengths.append(len(traj_list))
        
        # 计算 done 状态
        done_status = traj_list[-1]["done_after_action"]
        if done_status == 0:
            max_step_exceeded.append(episode_folder)
        elif done_status == 1:
            success.append(episode_folder)
        else:
            failure.append(episode_folder)

        # Compute SPL
        S_i = 1 if done_status == 1 else 0
        L_i = len(optimal_traj)
        P_i = len(traj_list)
        denominator = max(L_i, P_i)
        spl_i = S_i * (L_i / denominator) if denominator > 0 else 0
        spls.append(spl_i)

        # 计算 interaction accuracy
        interaction_traj = [step for step in traj_list if step.get("feedback")]
        interaction_total_count += len(interaction_traj)  # 计算所有interaction step的总数
        interaction_success_count += sum(1 for step in interaction_traj if step["feedback"] != "failed")  # 成功interaction的数量

    total_episodes = len(success) + len(failure) + len(max_step_exceeded)

    # 计算各类metrics
    accuracy = safe_divide(len(success), total_episodes)
    max_exceed_rate = round(len(max_step_exceeded) / total_episodes, 2)
    avg_traj_length = sum(traj_lengths) / len(traj_lengths) if traj_lengths else 0

    # 计算 interaction accuracy
    interaction_accuracy = safe_divide(interaction_success_count, interaction_total_count)

    # Compute average SPL and convert it to percentage
    average_spl = safe_divide(sum(spls), total_episodes)

    return {
        "accuracy": accuracy,
        "max_step_exceed_rate": max_exceed_rate,
        "average_trajectory_length": round(avg_traj_length, 2),
        "average_spl": average_spl,  # SPL now in percentage format
        "total_episodes": total_episodes,
        "success_count": len(success),
        "failure_count": len(failure),
        "max_step_exceeded_count": len(max_step_exceeded),
        "interaction_accuracy": interaction_accuracy,
        "total_interactions": interaction_total_count,
        "interaction_rate": round(interaction_total_count / total_episodes, 2),
        "successful_interactions": interaction_success_count 
    }

def compute_metrics_for_all_types(total_result_folder, model_name):
    total_metrics = {
        "model_name": model_name,
        "accuracy": 0.0,
        "max_step_exceed_rate": 0.0,
        "average_trajectory_length": 0.0,
        "average_spl": 0.0,
        "total_episodes": 0,
        "success_count": 0,
        "failure_count": 0,
        "max_step_exceeded_count": 0,
        "interaction_accuracy": 0.0,
        "total_interactions": 0,
        "successful_interactions": 0
    }

    type_metrics = []

    for task_type_folder in get_subfolders(total_result_folder):
        metrics = compute_metrics_for_each_type(task_type_folder)
        type_metrics.append({
            "model_name": model_name,  # Add model name for tracking
            "task_type": os.path.basename(task_type_folder),
            **metrics  # Unpack metrics directly
        })

        # 更新总计数和总数
        total_metrics["accuracy"] += metrics["accuracy"] * metrics["total_episodes"]
        total_metrics["max_step_exceed_rate"] += metrics["max_step_exceed_rate"] * metrics["total_episodes"]
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
        for key in ["accuracy", "max_step_exceed_rate", "average_trajectory_length", "interaction_accuracy", "average_spl"]:
            total_metrics[key] /= total_metrics["total_episodes"]

    total_metrics["interaction_rate"] = round(total_metrics["total_interactions"] / total_metrics["total_episodes"], 2)
    return total_metrics, type_metrics

def compute_metrics_for_models(base_path, output_folder):
    # Ensure the output folder exists, if not, create it
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    all_total_metrics = []
    all_type_metrics = []

    for model_folder in get_subfolders(base_path):
        model_name = os.path.basename(model_folder)  # Extract the model name (without full path)
        total_result_folder = os.path.join(base_path, model_name)
        total_metrics, type_metrics = compute_metrics_for_all_types(total_result_folder, model_name)
        all_total_metrics.append(total_metrics)
        all_type_metrics.extend(type_metrics)  # Combine type metrics for all models

    # Save only the required columns for total_metrics_df
    total_metrics_df = pd.DataFrame(all_total_metrics)
    filtered_total_metrics_df = total_metrics_df[
        ['model_name', 'accuracy', 'success_count', 'max_step_exceed_rate', 'average_trajectory_length', 'average_spl', 'total_episodes', 'interaction_accuracy', 'interaction_rate']
    ]
    filtered_total_metrics_df.to_csv(os.path.join(output_folder, 'all_models_total_metrics.csv'), index=False)

    # Filter type_metrics_df to include task_type along with other required columns
    type_metrics_df = pd.DataFrame(all_type_metrics)
    filtered_type_metrics_df = type_metrics_df[
        ['model_name', 'task_type', 'success_count', 'accuracy', 'max_step_exceed_rate', 'average_trajectory_length', 'average_spl', 'total_episodes', 'interaction_accuracy', 'interaction_rate']
    ]
    filtered_type_metrics_df.to_csv(os.path.join(output_folder, 'all_models_type_metrics.csv'), index=False)

if __name__ == "__main__":
    compute_metrics_for_models("/data41/private/legent/eval/EmbodiedEvalData/final_results", "/data41/private/legent/eval/metrics/output")

    plot_radar_chart_from_csv('/data41/private/legent/eval/metrics/output/all_models_type_metrics.csv', exclude_models=['human', "gpt-4o-mini"], custom_labels_order=["SpatialQA", "Navigation", "SocialInteraction", "ObjectInteraction", "AttributeQA"], y_max=40, metric_name='average_spl')
