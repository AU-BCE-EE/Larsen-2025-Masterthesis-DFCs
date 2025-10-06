### Script description ###
# Reads csv-files of reduced data-set created by the "1 initial data extraction" script
# Converts concentration-meassurements [PPb] into fluxces [mg / s m2 ], needs to be able to manage non-constant temperature
# Using the Total ammonia nitrogen (TAN) content of the slurry and the flux-meassurement to find the relative loss per hour
# Nomalizes the time to the start of the experiment

### Current version ###
# v0.5 - converted into [mg/m3]

### Packages ### 
import pandas as pd
from math import pi 
#print(pi)
from pathlib import Path

### Script initialization - Defining constants ###
# Folder-paths
# Copy the filepath. Put r in front so python knows to handle it as a raw string
input_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Speciale kodning - store filer\testdata - dummy data for coding\1 Dummy_extracted")
output_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Speciale kodning - store filer\testdata - dummy data for coding\2 Dummy_converted")

# Name of output file
output_name = "dummy_test_1" 

# Physical constants
R = 8.205736 * 10**(-5) # [m3 atm / K mol], ideal gas constant
MW_N = 14 * 10**3 # [mg/mol], molecular weight of nitrogen

# Fixed variables
D = 0.7 # [m] chamber diameter
A = (D / 2 )**2 * pi # [m2] area of the DFC
P = 1 # [atm] experiment performed outside at ambient pressure

# Non-constant varibles
T = 288.15 # Temperature [K], 15 degrees celsius currently assumed will be non-constant for actual experiments
Q = 1986 * (1/1000) * 60 # 1986[L/min] * (1/1000) [m3/L] * 60 [min/h] = ... [m3/h], air-flow in the DFC
TAN = 1800 # [mg/L] Total ammonia nitrogen for the slurry used in this experiment 
slurry_aplication = 3.5 # [L/m2] 
TAN_m2 = TAN * slurry_aplication # [mg/m2], amount of TAN per m2
#print(TAN_m2)

# Starting time
# starting time of the first meassurement in this experiment, remember '' to create a string
date = '2023-04-12' # [y-m-d] ex 2023-04-12 
time = '12:05:11.196' # [h-min-s.ms] ex 12:05:11.195
start_time = pd.to_datetime(date + ' ' +  time, format="%Y-%m-%d %H:%M:%S.%f")  # ading the time and date string together using equivalent formatting as the meassurents

### Actual Code-section ###
## Combining data from multiple files ##
# initalization of the file-loop
all_dfs = [] # all tables will be combined at this step

# loading the files in the input-folder one-by-one
for current_file in Path(input_folder).glob("*_extracted.csv"):
    combined_df = pd.read_csv(current_file) # "loading" csw-file as a dataframe
    all_dfs.append(combined_df) # saving the dataframes into a list

combined_df = pd.concat(all_dfs, ignore_index = True) # reduces the list of dfs into a single df, ignoring individual headers

## Data conversions ##
# Converting data, creating new rows for converted values:
# ppb into [mass/volume]
combined_df["C[mg/m3]"] = combined_df["C[PPB]"] * (P / (R*T)) * MW_N * 10**(-9) # [mg/m3]
combined_df["C_STDEV[mg/m3]"] = combined_df["C_STDEV[PPB]"] * (P / (R*T)) * MW_N * 10**(-9) # [mg/m3]

# flux calculations
combined_df["F[mg/m2 h]"] = (combined_df["C[mg/m3]"] * Q) / A # [mg/m2 h]
combined_df["F_STDEV[mg/m2 h]"] = (combined_df["C_STDEV[mg/m3]"] * Q) / A # [mg/m2 h]

# TAN-loss rates
combined_df["%TAN_LOSS[h^-1]"] = (combined_df["F[mg/m2 h]"] / TAN_m2) * 100 # [h^-1]
combined_df["%TAN_LOSS_STDEV[h^-1]"] = (combined_df["F_STDEV[mg/m2 h]"] / TAN_m2) * 100 # [h^-1]

# Combining time and date into a single collum
combined_df['DATE_TIME'] = combined_df['DATE[y-m-d]'] + ' ' + combined_df['TIME[h-min-s.ms]'] # combines the time and date id's in a single new collum

# remmoving individual time and date collums
combined_df = combined_df.drop(columns=['DATE[y-m-d]', 'TIME[h-min-s.ms]'])

# using a built-in panda-function to intepret the DATE_TIME as time-values, not simply strings
combined_df['DATE_TIME'] = pd.to_datetime(combined_df['DATE_TIME'], format="%Y-%m-%d %H:%M:%S.%f") 
combined_df['TIME_NORMALIZED[h]'] = (combined_df['DATE_TIME'] - start_time).dt.total_seconds() / 3600 # [h]

## Sorting the data ##
# firstly by valve ID, then by time
combined_df.sort_values(by=['VALVE_POS[-]','TIME_NORMALIZED[h]'], inplace=True) # sorts the df via the 2 specified collums, inplace tells the function to change the original (creates a copy as default)
#print(combined_df.head(10))

## save the combined df as a csw-file ## 
output_file = output_folder / f"{output_name}_converted.csv" # defines the path for the outputfile, connecting the outputfolder, txt-file name and adding _extracted.csv as a suffix
#combined_df.to_csv(output_file, index=False)

print('file completed without error-calls')

### Code-references ### 
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.sort_values.html
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.sort_values.html