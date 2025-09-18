# plotting.py

import matplotlib.pyplot as plt
from data_handler import DataManager # Not strictly needed here, but good practice

def setup_plot():
    """Initializes and configures the Matplotlib plot."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 'line,' unpacks the single Line2D object returned by ax.plot
    line, = ax.plot([], [], marker='o', linestyle='-', label='Remote Data') 
    
    ax.set_xlabel("Time")
    ax.set_ylabel("Value")
    ax.set_title("Real-time UDP Data Reception")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout() 
    
    return fig, ax, line

def update_plot(frame, ax, line, data_manager: DataManager):
    """Function called periodically by FuncAnimation to update the plot."""
    
    # Get thread-safe copies of data
    data_points, timestamps = data_manager.get_data()

    if not data_points:
        return line, 
    
    # X-data is the index (0, 1, 2, ...), Y-data is the collected values
    x_data = list(range(len(data_points)))
    y_data = data_points

    line.set_data(x_data, y_data)
    
    # Rescale axes automatically
    ax.relim()
    ax.autoscale_view()

    # Update x-axis labels to show timestamps
    ax.set_xticks(x_data) 
    ax.set_xticklabels(timestamps, rotation=45, ha='right')

    # Return the line artist (required by FuncAnimation)
    return line,