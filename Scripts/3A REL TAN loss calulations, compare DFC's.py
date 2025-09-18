### Script Description ###
# read the csw-files with converted data created by script 2
# loop through the collums
#
# based on the valve id's extract data for each id, save these data as a temporary object
# loop though valve id-data, perfom linear interpolation between datapoint k and k+1
# add these to the valve id-data such that these wont be used in the interpolation-calculation (per s or per min)
# hereafter, cumulate the TAN mass loss using integration, save this value
# compare the found loss agianst total loss, save this factor
# 
# identify the methods used for each valve
# Find Median & standard deviation from equivalent methods - on relative loss, others???

### Script version ###

### Packages ####
import pandas as pd
from pathlib import Path

### Script Initalization - defining constants ###
# Folders
# copy the filepath.Put r in front so python knows to handle it as a raw string
input_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Speciale kodning - store filer\testdata - dummy data for coding\2 Dummy_converted")
input_file_name = 'dummy_test_1_converted.csv'

# Loading the csv-file as a df:
combined_df = pd.read_csv(input_folder / input_file_name) # notice the / to combine the names

### Actual Script ### 

### Coding references ### 