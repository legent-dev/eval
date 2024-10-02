import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from math import pi
from matplotlib import font_manager

# 添加字体路径
font_path = '/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf'
font_manager.fontManager.addfont(font_path)

# 指定字体名称
plt.rcParams['font.family'] = 'Times New Roman'


def plot_radar_chart_from_csv(file_path, exclude_models=[], y_min=0, y_max=45, custom_labels_order=None, metric_name='Success Rate (%)'):

    # Load the data from the CSV file
    df = pd.read_csv(file_path)

    # Get unique labels for the radar chart, apply custom order if provided
    labels = df['Task Type'].unique()
    if custom_labels_order:
        labels = custom_labels_order  # Use custom order if provided

    num_vars = len(labels)

    # Determine appropriate y-ticks and limits
    y_ticks = np.linspace(y_min, y_max, num=5)  # Generate 5 ticks

    # 初始化颜色列表，确保有足够的颜色
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2'] 

    # Function to add radar chart for a specific model
    def add_radar_chart(data, model_name, color):
        # Calculate angles based on number of variables
        angles = [n / float(num_vars) * 2 * pi for n in range(num_vars)]
        angles += angles[:1]  # Complete the loop

        # Ensure the data is aligned with the labels
        values = list(data.reindex(labels)) + [data.reindex(labels).iloc[0]]

        if len(values) != len(angles):
            raise ValueError("The number of values does not match the number of angles")

        ax = plt.subplot(111, polar=True)
        ax.set_theta_offset(pi / 2)
        ax.set_theta_direction(-1)

        plt.xticks(angles[:-1], labels, color='grey', size=12)
        ax.set_rlabel_position(0)
        plt.yticks(y_ticks[:-1], [str(round(y, 2)) for y in y_ticks[:-1]], color="grey", size=7)
        plt.ylim(y_min, y_max)

        ax.plot(angles, values, linewidth=1, linestyle='solid', label=model_name)
        ax.fill(angles, values, color, alpha=0.1)

    # Initialize the plot
    plt.figure(figsize=(6, 6))

    # Iterate over each model and add its radar chart, excluding the specified models
    for i, model in enumerate(df['Model'].unique()):
        if model in exclude_models:
            continue

        # Ensure we align task types across models by reindexing the task_type
        model_data = df[df['Model'] == model].set_index('Task Type').reindex(labels)[metric_name]

        add_radar_chart(model_data, model, colors[i % len(colors)])  # 使用循环颜色列表

    # Add legend and save the figure
    plt.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
    plt.savefig(f"/data41/private/legent/eval/metrics/plots/radar_chart_{metric_name}.png", format="png", bbox_inches='tight', dpi=300)

    # Optionally, show the plot
    # plt.show()

# Example usage with custom label order and metric_name
# plot_radar_chart_from_csv('/path/to/your/file.csv', exclude_models=['model_a', 'model_b'], custom_labels_order=['label3', 'label1', 'label5', 'label2', 'label4'], metric_name='average_spl')



def plot_success_rate(csv_file):
    # 读取CSV文件
    df = pd.read_csv(csv_file)
    
    model_names = df['model'].unique()
    step_sizes = df['step_size'].unique()
    
    # 将数据转化为字典形式 {模型名称: 成功率列表}
    model_success_rates = {model: df[df['Model'] == model]['accuracy'].values for model in model_names}
    
    # 开始绘制图表
    plt.figure(figsize=(10, 8))
    
    # 使用更专业的配色和较粗的线条
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    markers = ['o', 's', 'D', '^', 'v', '*']
    
    for (model_name, success_rate), color, marker in zip(model_success_rates.items(), colors, markers):
        plt.plot(step_sizes, success_rate, marker=marker, linestyle='-', color=color, label=model_name, linewidth=2.5, markersize=8)
    
    # 美化图表
    plt.title('Step Size vs Accuracy', fontsize=18, weight='bold')
    plt.xlabel('Step Size', fontsize=14)
    plt.ylabel('Accuracy', fontsize=14)
    plt.legend(loc='upper right', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xlim(0, 25)  # 根据你的数据调整坐标轴范围
    plt.ylim(0, 1.1)
    
    # 改善刻度字号以提高可读性
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    
    # 隐藏顶部和右侧的边框线条
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    # 显示图表
    plt.show()

# 使用示例
# plot_success_rate('your_file.csv')


def plot_metric_from_csv(csv_file, metric, exclude_models=[]):
    # 从CSV读取数据
    data = pd.read_csv(csv_file)

    # 确认metric是否在CSV文件中
    if metric not in data.columns:
        raise ValueError(f"Metric '{metric}' not found in the CSV file.")

    # 过滤掉需要排除的模型
    if exclude_models:
        data = data[~data['Model'].isin(exclude_models)]

    # 根据metric值进行升序排序
    data = data.sort_values(by=metric, ascending=True)

    models = data['Model']
    metric_values = data[metric]

    # 创建柱形图
    plt.figure(figsize=(10, 6))
    bars = plt.bar(models, metric_values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2'])

    # 添加标题和标签
    plt.xlabel('Models', fontsize=14)
    plt.ylabel(metric, fontsize=14)

    # 在每个柱形上方显示模型名称和metric值
    for bar, model in zip(bars, models):
        yval = bar.get_height()
        # 将metric值放置在柱形上
        plt.text(bar.get_x() + bar.get_width()/2, yval + 1, f'{yval:.2f}', ha='center', va='bottom', fontsize=12)
        # 将模型名称放置在柱形的上方
        plt.text(bar.get_x() + bar.get_width()/2, yval + 4, model, ha='center', va='bottom', fontsize=12, color='gray')

    # 显示网格
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # 保存图形为PNG
    plt.tight_layout()
    plt.savefig(f"/data41/private/legent/eval/metrics/plots/bar_{metric}.png", format="png", bbox_inches='tight', dpi=300)