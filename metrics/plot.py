import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from math import pi

def plot_radar_chart_from_csv(file_path, exclude_models=[], y_min=0, y_max=45, custom_labels_order=None, metric_name='accuracy'):
    # Load the data from the CSV file
    df = pd.read_csv(file_path)

    # Get unique labels for the radar chart, apply custom order if provided
    labels = df['task_type'].unique()
    if custom_labels_order:
        labels = custom_labels_order  # Use custom order if provided

    num_vars = len(labels)

    # Compute min and max values of the metric
    min_value = df[metric_name].min()
    max_value = df[metric_name].max()

    # Determine appropriate y-ticks and limits
    y_ticks = np.linspace(y_min, y_max, num=5)  # Generate 5 ticks

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
    for model in df['model_name'].unique():
        if model in exclude_models:
            continue

        # Ensure we align task types across models by reindexing the task_type
        model_data = df[df['model_name'] == model].set_index('task_type').reindex(labels)[metric_name]

        add_radar_chart(model_data, model, np.random.rand(3,))  # Using random colors for each model

    # Add legend and save the figure
    plt.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
    plt.savefig(f"/data41/private/legent/eval/metrics/plots/radar_chart_{metric_name}.png", format="png", bbox_inches='tight', dpi=300)

    # Optionally, show the plot
    # plt.show()

# Example usage with custom label order and metric_name
# plot_radar_chart_from_csv('/path/to/your/file.csv', exclude_models=['model_a', 'model_b'], custom_labels_order=['label3', 'label1', 'label5', 'label2', 'label4'], metric_name='average_spl')
