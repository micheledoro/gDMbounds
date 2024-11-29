# dmbounds/data_reader.py

import pandas as pd
from astropy.io import ascii
import glob
import os

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

def read_ecsv(file_path):
    """Read a single .ecsv file and return its contents."""
    return ascii.read(file_path)

def read_multiple_ecsv(instrument_dict):
    """Initialize the pandas DataFrame with metadata from all bounds present in the database."""
    files_all = []
    for name in instrument_dict.keys():
        files_all.append(glob.glob(MODULE_DIR + "/bounds/" + name + "/*.ecsv"))
    files_all = [x for row in files_all for x in row]

    metadata_df = pd.DataFrame(
        columns=(
            'Instrument',
            'Target',
            'Mode',
            'Channel',
            'Year',
            'Observation time',
            'Title',
            'DOI',
            'Arxiv',
            'Comment',
            'File name'))

    for i, file in enumerate(files_all):
        filename = file.split("/")[-1][:-5]
        # Extract metadata from the filename and the file itself
        # (You would include the logic to populate the DataFrame here)

    return metadata_df

def table_to_dict(table, keycolumn_name, valuecolumn_name):
    """Transform an astropy table with two specified columns into a dictionary."""
    dictionary = {}
    for column in range(len(table)):
        dictionary[table[keycolumn_name][column]] = table[valuecolumn_name][column]
    return dictionary