### Script description ###
# Read txt-files from a designated input-folder, containing raw data from the dynamic flux chambers (DFC's) as txt-files
# For each file, load it as a table, extract and save the following parameters at least:
# - Concentration [ppb], as a an average of the last 30 s before a valve-shift idealy also with the corresponding std-deviation - use a moving average function
# - Corresponding Valve postion [-]
# - Corresponding date [y-m-d] and time of day [h:min:s:ms]
# Save these parameters in a new clearer table
# Save the new table as a txt or Csw-file 

### Packages ### 
import pandas as pd
from pathlib import Path
from statistics import stdev

### Variables ####
# copy the filepath
# put r in front so python knows to handle it as a raw string
input_folder = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\Input data\testdata - dummy data for coding\Actual data - only 1 file") 

### Data extraction ###
for txt_file in input_folder.glob("*.txt"): # loops over txt-files in the inputfolder
    current_table = pd.read_csv(txt_file, sep=r'\s+') # loads the current file in the loop as a table(dataframe)
    current_table_copy = current_table # creating a copy to maintain the original file as is

    extracted_data = [] # initalized as an empty which will be continously appended and saved as a table at the end, 
    # more computaionally efficient according to stackoverflow

    #print(current_table_copy['MPVPosition'].head(10)) # prints the first 10 datapoints of a collum as a manual check
    for row_index, row in current_table_copy.iterrows:
        if row(row_index) != row(row_index(+1)): # when the current and the next valveposion are not equal, ie the position shifts 
            extracted_data.append()

    
print('\n' 'script is done' '\n')
### Code references ### 
# https://www.geeksforgeeks.org/python/how-to-read-text-files-with-pandas/
# https://www.geeksforgeeks.org/python/how-to-calculate-moving-averages-in-python/ 
# https://stackoverflow.com/questions/28218698/how-to-iterate-over-columns-of-a-pandas-dataframe
# https://stackoverflow.com/questions/13784192/creating-an-empty-pandas-dataframe-and-then-filling-it 



