### Script Description ###
# read the csw-files with converted data created by script 2
# loop through the collums
#
# based on the valve id's extract data for each id, save these data as a temporary object
# loop though valve id-data, perfom linear interpolation between datapoint k and k+1
# add these to the valve id-data such that these wont be used in the interpolation-calculation (add point approximately per s or per min)
# using original and interpolated data, cumulate the TAN mass loss using integration, save this value
# compare the found loss agianst total loss, save this factor
# 
# identify the methods used for each valve
# Find Median & standard deviation from equivalent methods - on relative loss, others???

### Script version ###

### Packages ####
# alphabetical order
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.interpolate import CubicSpline

### Script Initalization - defining constants ###
# Folders
# copy the filepath.Put r in front so python knows to handle it as a raw string
input_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Speciale kodning - store filer\testdata - dummy data for coding\2 Dummy_converted")
input_file_name = 'dummy_test_1_converted.csv'

# Valve id's, used for looping
valve_ids = [2]

# TAN
TAN = 1800 # [mg/L] Total ammonia nitrogen for the slurry used in this experiment 
slurry_aplication = 3.5 # [L/m2] 
TAN_m2 = TAN * slurry_aplication # [mg/m2], amount of TAN per m2

### Actual Script ### 
# Loading the csv-file as a df:
combined_df = pd.read_csv(input_folder / input_file_name) # notice the / to combine folder filename in a single string, different from std Python notation

# looping relevant data related to each valve
for id in valve_ids:
    valve_df = combined_df[combined_df['VALVE_POS[-]'].round(5) == id].reset_index(drop=True) # selects the VALVE-POS collum from combined_df,
    # rounds the number extra precuation, as Python is weird with floats,
    # Checks if the VALVE-POS values matches the current id,
    # Based on this check, creates a new reduced df with reset index values, default is keeping the ones from the old folder, with data purely related to 1 valve

    x = valve_df["TIME_NORMALIZED[h]"].values # extracting time as x-values from the df
    y = valve_df["F[mg/m2 h]"].values # extracting flux-values as y-values from the df

    # Creating additional x-values approximately every min
    x_expanded = np.arange(0, x[-1], 1/60) # h/60 = min

    # Linear interpolation
    y_linear = np.interp(x_expanded, x, y)

    # Cubic interpolation 
    cs = CubicSpline(x, y)
    y_cubic = cs(x_expanded)

    # plot #
    plt.plot(x_expanded, y_linear, marker='x', linestyle='None', color='black', markersize=1, label=f'valve {id} (linear interp)')
    plt.plot(x_expanded, y_cubic, marker='x', linestyle='None', color='gray', markersize=1, label=f'valve {id} (cubic spline interp)')
    plt.plot(x, y, marker='.', linestyle='None', color='red', markersize=5, label=f'valve {id} (original)')

    # trapezoidal integration #
    # normalize the flux against total mass per m2
    y_norm = (y / TAN_m2) # [mg/m2 h] / [mg / m2] = [1 / h]
    y_linear_norm = (y_linear / TAN_m2)
    y_cubic_norm = y_cubic / TAN_m2

    trapz_org = np.trapezoid(y_norm, x)
    trapz_lin = np.trapezoid(y_linear_norm, x_expanded) 
    trapz_splin = np.trapezoid(y_cubic_norm, x_expanded)

### Print tests ###
# some needs to be within a loop, but those who can are placed here
#print(valve_df)
#print(y_linear)
#print(type(y_linear))
print('original:', trapz_org, 'lin interp:', trapz_lin , 'splin interp:', trapz_splin)

### Visuals ###
plt.xlabel('t [h]', fontsize=12)
plt.ylabel('F [mg / m2 h]', fontsize=12)
plt.legend()
plt.show()

### Coding references ### 