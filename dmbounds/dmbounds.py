# dmbounds/dmbounds.py

import os
from .data_reader import read_multiple_ecsv
from .plotter import plot_data, save_plot, set_plot_style, clear_plot
from .computations import compute_average  # Assuming you have computations defined

# Step 1: Define the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Gets the directory of the current script

def main():
    # Step 2: Define your instrument dictionary or file paths using the base directory
    instrument_dict = {
        'magic': os.path.join(BASE_DIR, 'bounds/magic/'),
        'Instrument2': os.path.join(BASE_DIR, 'data/instrument2/files'),
        # Add more instruments and their corresponding paths as needed
    }

    # Step 3: Read data from .ecsv files
    metadata_df = read_multiple_ecsv(instrument_dict)

    # Step 4: Process the metadata and plot data
    for index, row in metadata_df.iterrows():
        # Assuming the DataFrame has columns 'x' and 'y' for plotting
        x = row['x']  # Replace with actual column names
        y = row['y']  # Replace with actual column names
        plot_data(x, y, label=row['Instrument'])  # Use appropriate label

    # Optional: Save the plot if needed
    save_plot('output_plot.png')

    # Optional: Set plot style
    set_plot_style('seaborn')

    # Optional: Clear the plot if you want to start fresh for the next plot
    clear_plot()

if __name__ == "__main__":
    main()