### Script description ###
# Reads csv-files of cleaned data created by the "1 initial data extraction" script
# Converts concentration-meassurements [PPb] into fluxces [???], needs to be able to manage non-constant temperature
# Nomalizes the time to the start of the experiment

### Current version ###
# v0.5

### Packages ### 
from pathlib import Path
import pandas as pd

### Constants ###
# Folders copy the filepath. Put r in front so python knows to handle it as a raw string
input_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Speciale kodning - store filer\testdata - dummy data for coding\1 Dummy_extracted")
output_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Speciale kodning - store filer\testdata - dummy data for coding\2 Dummy converted")

# Physical constants
P = 1 # [atm] ambient presure
R = 8.205736 * 10**(-5) # [m3 atm / K mol] ideal gas constant
MW_N = 11 * 10**3 # [mg/mol] molecular weight of nitrogen ???

### Non-constant varibles ###
# Temperature
T = 288.15 # [K], 15 degrees celsius currently assumed will be non-constant for actual experiments 

### Actual Code-section ###

# loading the files in the input-folder one-by-one
for current_file in Path(input_folder).glob("*_extracted.csv"):
    inital_table = pd.read_csv(current_file)
    inital_table_copy = inital_table # creating a copy, protecting original data
    #print('this is the print: ', current_file)
    #print(current_table)

    for row_index, row in inital_table_copy.iterrows():
    # Converting from ppb into mass/volume:
        concentration = row['Concentration[PPB]']
        # print(concentration)
        concentration = concentration * (P / (R*T)) * MW_N * 10**(-9) # [mg / m3]
        #print(concentration)
        concentration_stdev = row['Concentration_stdev[PPB]']
        concentration_stdev = concentration_stdev * (P / (R*T)) * MW_N * 10**(-9) # [mg / m3]
        print(concentration_stdev)




   

### Code-references ### 