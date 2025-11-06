### Script description ###
# V1:
# Reads txt-files from a designated input-folder, containing raw data from the dynamic flux chambers (DFC's) as txt-files
# For each file, load it as a table, extract and save the following parameters, currently:
# - Concentration [ppb], as a an average of the last 30 s before a valve-shift idealy also with the corresponding std-deviation
# - Corresponding Valve postion [-]
# - Corresponding date [y-m-d] and time of day [h:min:s:ms]
# Save these parameters in a new clearer table
# Save the new table as a csv-file in a designated outputfolder, one for each txt-file
# V2:
# before saving the data, sort it based on the valve Id, and thereafter the time

### Currrent version ###
# v1

### Packages ### 
from pathlib import Path
import pandas as pd

### Scrip initialization ####
# Folders:copy the filepath.Put r in front so python knows to handle it as a raw string
input_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Speciale kodning - store filer\testdata - dummy data for coding\Actual data - only 1 file")
output_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Speciale kodning - store filer\testdata - dummy data for coding\1 Dummy_extracted")

# overwrite
overwrite = True # False/True statement, old files with the same name will not be overwritten if set to False

### Actual Code-section ###
## Setup loopng over the files ##
# Looping over files in the designated inputfolder
for txt_file in input_folder.glob("*.txt"): # loops over txt-files in the inputfolder (txt-file specific as an extra precuation to avoid errors)
    current_df = pd.read_csv(txt_file, sep=r'\s+') # loads the current file in the loop as a table(pd-dataframe), indicating that the collum seperator is sevral empty spaces
    # print(current_table_copy['MPVPosition'].head(10)) # prints the first 10 datapoints of a collum as a manual check of the code
    
    # Loop initialization for rows in the current txt-file
    extracted_data = {'C[PPB]' : [], 'C_STDEV[PPB]' : [], 'VALVE_POS[-]': [], 'DATE[y-m-d]' : [], 
    'TIME[h-min-s.ms]' : []} 
    #print(extracted_data)
    # extracted data will be continusly added to this dictionary and converted into a table at the end, saving computer-power compared to tables

    previous_vale_postion = None # initlazation of shift check
    in_shift = False # initialization of shift-check

    ## Actual data-extraction ##
    for row_index, row in current_df.iterrows(): # loops over the table top to bottom (in the rows)
        # defining the collums of interest using thier respective header:
        vale_position = row['MPVPosition'] # Position of the vale, determining which DFC chamber is meassured. 

        if previous_vale_postion is not None: # avoids erros at inital point
            valve_diff = vale_position - previous_vale_postion # difference in valve postion ID
            
            if valve_diff >= 0.0001 and not in_shift: # the in-shift state ensures only one measurement made per shift, if the difference is larger than 0.0001 a shift is occuring
                in_shift = True # shift-state changed
                #print(row_index , previous_vale_postion)

                ## Gathering data from the last 30 s  before the shift ## 
                start_index = max(0, row_index - 30) # tackes the last 30 measurements, or 0, extra precuation if the shift occurs at the start of the table
                #print('shift index ', row_index, 'go back 30 ', start_index)

                data_window = current_df.loc[start_index : row_index - 1] # panda feauture df.loc[row , collum] creates a sub-table with the ability to slice (includes the last index unlike slicing in normal pyhton)

                if len(data_window) > 0: # extra check that the data-window has been corectly created to avoid error-calls
                    middle_row = data_window.iloc[len(data_window) // 2 ] # tackes the entire row in the middle of the window, notice the integer division always rounds down
                    time_val = middle_row['TIME']
                    date_val = middle_row['DATE']
                    valve_ID = middle_row['MPVPosition']
                    #print(time_val,' ',date_val)
                    #print(valve_ID)

                    NH3_concentration = data_window['NH3'].mean() #mean of the last 30 s - notice the syntax is panda-specific
                    NH3_stdev = data_window['NH3'].std()
                    #print(NH3_concentration, '' , NH3_stdev)

                    # Saving collected data into the dict
                    extracted_data['C[PPB]'].append(NH3_concentration)
                    extracted_data['C_STDEV[PPB]'].append(NH3_stdev)
                    extracted_data['VALVE_POS[-]'].append(valve_ID)  # current valve pos at shift
                    extracted_data['DATE[y-m-d]'].append(date_val)
                    extracted_data['TIME[h-min-s.ms]'].append(time_val)

            elif valve_diff < 0.0001: # resets the shift-check when the there is no longer a difference between current and previous valve value
                in_shift = False

        previous_vale_postion = vale_position # shift of the current valve-postion in the loop       
    
    ## Saving the extracted data as csv-files ##
    #print(extracted_data)
    new_table = pd.DataFrame(data=extracted_data) # conveting the dict into a table
    #print(new_table)
    output_file = output_folder / f"{txt_file.stem}_extracted.csv" # defines the path for the outputfile, connecting the outputfolder, txt-file name and adding _extracted.csv as a suffix

    if output_file.exists() and overwrite is False:
        continue  # moves on to the next txt_file

    new_table.to_csv(output_file, index=False) 

    print("\nAll files processed successfully\n")

### Code references ### 
# https://www.geeksforgeeks.org/python/how-to-read-text-files-with-pandas/
# https://www.geeksforgeeks.org/python/how-to-calculate-moving-averages-in-python/ 
# https://stackoverflow.com/questions/28218698/how-to-iterate-over-columns-of-a-pandas-dataframe
# https://stackoverflow.com/questions/13784192/creating-an-empty-pandas-dataframe-and-then-filling-it 
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html 





