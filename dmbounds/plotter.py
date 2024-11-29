# dmbounds/plotter.py

import matplotlib.pyplot as plt

def plot_data(x, y, label):
    """Plot data with the given x and y values and a label."""
    plt.plot(x, y, label=label)
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.legend()
    plt.show()

def save_plot(filename):
    """Save the current plot to a file."""
    plt.savefig(filename)

def set_plot_style(style='seaborn'):
    """Set the style of the plot."""
    plt.style.use(style)

def clear_plot():
    """Clear the current plot."""
    plt.clf()

def plot_multiple_datasets(datasets, labels):
    """Plot multiple datasets on the same figure."""
    for data, label in zip(datasets, labels):
        plt.plot(data[0], data[1], label=label)
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.legend()
    plt.show()

# Add any additional plotting functions as needed