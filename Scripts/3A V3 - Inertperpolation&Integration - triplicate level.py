### Script Description ###
# interplation & integration script 
# handeling everything on a triplicate-level

### Script version ###
# V3 - easier to create new script for data-handeling at triplicate level

### Packages ###
import pandas as pd
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.interpolate import CubicSpline

### Actual Script ###

## Functions ##
def load_data(input_folder,input_file_name):
    '''
    Load a csv-file as a df using it's folderpath and filename
    Requires the path and pandas package
    '''
    df = pd.read_csv(input_folder / input_file_name) # notice the / to attach the strings, non-std Python formatting
    return df  

def add_method(df, method_dict):
    '''
    df: df of all data.
    method: dict with ints (valve ids) as keys, and str as values (methods).
    
    Using .map() to add an additional collum with treatment ID, using the method_dict

    Returns: df with additional collum with treatment ids
    '''    
    df = df.copy()
    df["TREATMENT"] = df["VALVE_POS[-]"].round(5).map(method_dict) # using .map() to add a new collum with method ID, using the valve id
    return df


def extract_valve_data(df, valve_ids=None):
    ''' 
    Extract data from a df with data from multiple valves.
    If `valve_ids` is None, it will automatically detect all unique valve IDs.
    Returns the extracted data as a dict.
    '''
    if valve_ids is None:
        valve_ids = df['VALVE_POS[-]'].round(5).unique() # extracting all unique id's

    valve_data = {}
    for id in valve_ids:
        valve_df = df[df['VALVE_POS[-]'].round(5) == id].reset_index(drop=True)

        x = valve_df["TIME_NORMALIZED[h]"].values
        y = valve_df["F[mg/m2 h]"].values
        method_id = df['TREATMENT'].iloc[0]
        valve_data[int(id)] = {"x": x, "y": y , 'metod_id' : method_id}

    return valve_data
    
def interpolate_valve(valve_data, interp_method = 'linear'):
    '''
    Performs interpolations using known x (norm time) and y-values (flux) on data coresponding to each valve id stored in a dict
    Returns a dict of dicts, the valve id being the outher key, with the other values being another dict with results from each interpolation
    '''
    interp_results = {} # initalizing the return-dict

    for id,data in valve_data.items(): # looping over the valve data dict
        x = data['x']
        y = data['y']
        method_id = data['metod_id']

        x_expanded = np.linspace(0, x[-1], num=int(x[-1] * 120) + 1) # expands the time-values to every half min
        
        interp_result = {"x_expanded": x_expanded, 'method_id': method_id} # extract the x-value into the dict

        if interp_method in ("all", "linear"):
            interp_result["y_linear"] = np.interp(x_expanded, x, y) # linear interpolation of "missing" minutes, using known y-points

        if interp_method in ("all", "cubic"):
            interp_result["y_cubic"] = CubicSpline(x, y)(x_expanded) # cubic spline interpolation of "missing" minutes, using known y-points

        interp_results[id] = interp_result # add current itetation to the return_dict

    return interp_results

def combine_triplicates(interp_results):
    '''
    '''
   
## Constants ## 
# Treatment methods - as a dict 
# no treatment = Baseline = B
# untreated slurry = US
# disrupter + acid = DA
# disrupter = D
# Seperated + Acid = SA
# Seperated = S
treatment_methods = {
5: 'B', 9: 'B', 16: 'B' ,
1: 'US', 10: 'US', 18: 'US', 
2: 'DA' , 8: 'DA', 13: 'DA',
3: 'D', 10: 'D', 17: 'D',
4: 'SA', 7: 'SA', 14: 'SA',
4: '6', 11: 'S', 15: '16'
}

# Folders
input_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Speciale kodning - store filer\testdata - dummy data for coding\2 Dummy_converted") # copy the filepath
input_file_name = 'dummy_test_1_converted.csv' # copy the name as a string, don't forget .csv

## Function calls ##
df = load_data(input_folder, input_file_name)
metod_df = add_method(df,treatment_methods)
valve_data_dict = extract_valve_data(metod_df)
interpolation_dict = interpolate_valve(valve_data_dict)

## Print tests ## 
#print(df)
#print(metod_df.head(10))
#print(valve_data)
print(interpolation_dict)

## Coding references ##
# https://pandas.pydata.org/docs/reference/api/pandas.Series.map.html 