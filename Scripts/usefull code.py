### Script description ###
# Usefull codes/function with explantion - potentially not used in final version of actual scrits, therefore saved here

### Packages ###
import pandas as pd
import numpy as np
from scipy.interpolate import CubicSpline

### Actual code-section ###
# table["COLLUMNAME"].iloc[0])) # graps a single value from a specified collum in a pandas dataframe

# print(table['COLLUMNAME'].head(10)) # prints the first 10 datapoints of a table or a specified collum

a= [3,2,1]
print(np.empty_like(a))

def interpolate_valve(valve_data, interp_method = 'linear'):
    '''
    Performs interpolations(linear & cubic spline), within the range which data is present for each valve.
    Using x-values (global normalized time) and y-values (flux) on data coresponding to each valve id stored in a dict to perform the interpolation.
    Also extracs additional data used as argumments in later for later functions such as method_id.
    
    Returns a dict with valve_id as key and interpolated data (x_expanded, y_interpolated, method_id) as values.
    
    Notice this function is simplified compared to v2 script, as this function should be able to handle all valves within reasonable time-frames.
    Therefore, ability to interpolate using either method at the same time was removed. 
    Also make the data-structures later functions needs to handle simpler.
    '''
    interp_results = {} # initalizing the return-dict

    for id,data in valve_data.items(): # looping over the valve data dict
        x = data['x'] # normalized time
        y = data['y'] # flux
        method_id = data['metod_id']

        x_expanded = np.linspace(x[0], x[-1], num=int((x[-1] - x[0]) * 120) + 1) # creates evenly spaced timestamps (½ min)

        if interp_method == 'linear':
            y_interp = np.interp(x_expanded, x, y)

        elif interp_method == 'cubic':
            y_interp = CubicSpline(x, y)(x_expanded)

        interp_results[id] = {'x_expanded' : x_expanded, 'y_interp': y_interp, 'method_id' : method_id} # adding to the dict
        # id as key, results from interpolation as values 

    return interp_results


def process_input_folder(input_folder , output_folder, overwrite = False):
    '''
    Function handles overall logic of loading and saving multiple data from a folder.
    extract_data_from_piccarro_file is used for each file in the folder    
    '''

    output_folder.mkdir(parents=True, exist_ok=True) 
    # creates the outputfolder if it doesnt already exist
    # exist_ok = True ensures script simply moves on if output_folder exist instead of raising a value_error

    txt_files = list(input_folder.glob("*.txt"))
    if len(txt_files) == 0:
        print(f"No .txt files found in {input_folder}")
        return
    
    for txt_file in txt_files:
        print(f'Processing {txt_file.name}') # .name provides simply the filename not the entire path
        extracted_df = extract_data_from_piccaro_file(txt_file)

        output_file = output_folder / f"{txt_file.stem}_extracted.csv"
    
        if output_file.exists() and not overwrite:
            print(f"Skipping existing file: {output_file.name}")
            continue

        extracted_df.to_csv(output_file, index=False)
        print(f"Saved: {output_file.name}")

### Changing another script, saving this here for now ### 
