### Script Description ###
# Loads the combined CSW-file outputted by script
# Plotting data related specefic DFC's, using the valve ID - can plot muliple in the same figure
# Set up to plot a specified collum as a function of normalized time

### Script version ###

### Packages ####
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

### Script Initalization - defining constants ###
# Folders
# copy the filepath.Put r in front so python knows to handle it as a raw string
input_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Speciale kodning - store filer\testdata - dummy data for coding\2 Dummy_converted")
input_file_name = 'dummy_test_1_converted.csv'

# which vales to analyze
valve_ids = [1, 16] # specifies the valve from which data are extracted
# either a single valve or multiple, create a list of numbers [1, 2, 18, ...]

# specification/ initalization of the y-axis data
x_collum_title = 'TIME_NORMALIZED[h]'
y_collum_title = 'F[mg/m2 h]'
data_dict = {} # initallzing a dict to store x and y data

### Actual Script ### 
# Loading the csv-file as a df:
combined_df = pd.read_csv(input_folder / input_file_name) # notice the / to combine the names
#print(combined_df)

# extracting data
for id in valve_ids: # looping  over the valve id list
    valve_df = combined_df[combined_df['VALVE_POS[-]'].round(5) == id].reset_index(drop=True) # selects the VALVE-POS collum from the combined_df folder,
    # rounds the number, as Python is weird with integers,
    # Checks if the VALVE-POS values matches the current id,
    # Based on this check, creates a new reduced df with restet index values
    data_dict[id] = {"x": valve_df[x_collum_title],"y": valve_df[y_collum_title]} # storing specified data in the dict,
    # outer dict has the valve id's as keys, and the x&y dicts as values,
    # inner has the x-data as keys and the y-data as values

## Plotting Data ##
for valve_key, data in data_dict.items():
    plt.plot(data["x"], data["y"],'.-', label=f"Valve {valve_key}")

plt.xlabel('Time [h]')
plt.ylabel('Flux [mg / m2 h]')
plt.legend()
plt.show()

### Coding references ### 