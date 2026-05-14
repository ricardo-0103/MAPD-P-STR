import yaml
import matplotlib.pyplot as plt
import numpy as np
import argparse
import os
from matplotlib.lines import Line2D

def python_tuple_constructor(loader, node):
    return tuple(loader.construct_sequence(node))

yaml.SafeLoader.add_constructor('tag:yaml.org,2002:python/tuple', python_tuple_constructor)
# -------------------------------------------------------

def visualize_warehouse(yaml_path):
    if not os.path.exists(yaml_path):
        print(f"Error: File not found at {yaml_path}")
        return

    with open(yaml_path, 'r') as f:
        # Now safe_load can handle !!python/tuple
        data = yaml.safe_load(f)

    height, width = data['map']['dimensions']
    
    fig, ax = plt.subplots(figsize=(12, 8))

    # 1. Draw Grid Background
    ax.set_xlim(-0.5, width - 0.5)
    ax.set_ylim(-0.5, height - 0.5)
    ax.set_xticks(np.arange(0, width, 1))
    ax.set_yticks(np.arange(0, height, 1))
    ax.grid(which='both', color='lightgrey', linestyle='-', linewidth=0.5)
    ax.set_aspect('equal')
    ax.invert_yaxis() 

    # 2. Draw Obstacles (Black Cells)
    for obs in data['map']['obstacles']:
        y, x = obs
        rect = plt.Rectangle((x - 0.2, y - 0.2), 0.4, 0.4, color='black')
        ax.add_patch(rect)

    # 3. Draw Pickups (Cyan Squares)
    for loc in data['map']['start_locations']:
        y, x = loc
        ax.scatter(x, y, color='cyan', marker='s', s=80, zorder=3)

    # 4. Draw Deliveries (Magenta Triangles)
    for loc in data['map']['goal_locations']:
        y, x = loc
        ax.scatter(x, y, color='magenta', marker='^', s=80, zorder=3)

    # 5. Draw Agents (Yellow Circles)
    for agent in data.get('agents', []):
        y, x = agent['start']
        circle = plt.Circle((x, y), 0.3, color='yellow', ec='black', zorder=5)
        ax.add_patch(circle)
        ax.text(x, y, agent['name'], color='black', fontsize=7, ha='center', va='center', fontweight='bold', zorder=6)

    # 6. Formatting & Legend
    file_name = os.path.basename(yaml_path)
    plt.title(f"Warehouse Map: {file_name} ({width}x{height})")
    
    legend_elements = [
        Line2D([0], [0], color='black', lw=4, label='Obstacle'),
        Line2D([0], [0], marker='s', color='w', label='Pickup', markerfacecolor='cyan', markersize=10),
        Line2D([0], [0], marker='^', color='w', label='Delivery', markerfacecolor='magenta', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Agent', markerfacecolor='yellow', markeredgecolor='black', markersize=10)
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.2, 1))

    # Save Logic
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "..", "Maps_Output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    save_path = os.path.join(output_dir, f"{os.path.splitext(file_name)[0]}.png")
    plt.savefig(save_path, bbox_inches='tight', dpi=300)
    print(f"Image successfully saved to: {save_path}")
    
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Visualize and save warehouse YAML environments.")
    parser.add_argument("-name", type=str, required=True, help="Name of the YAML file in Environments folder")
    
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_dir = os.path.join(script_dir, "..", "Environments")
    full_path = os.path.join(env_dir, args.name)

    visualize_warehouse(full_path)