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

### Functions ###
def load_data(input_folder,input_file_name):
    '''
    Load a csv-file as a pd.df using it's folderpath and filename
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
    Extracts specific data from a df with data from multiple valves.
    If valve_ids is None, it will automatically detect all unique valve IDs.
    Returns the extracted data as a dict.
    Valve Id is key, normalized time, flux-values and method Id are dict_values
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

def extrapolate_valve(interp_results, global_end = None):
    '''
    Ensuring data from each valve is fitted onto the global time-frame (start end end of the experiment, not simply the specific valve-measurement).
    Done by extrapolating the heads and tails of each valve.
    Ensures acessment of interpolation and extrapolation accuracy individually.

    Interp_results: valve_id as key, x_expanded, y_interp & method ID as values
    global_time: normalized time for the final and initial datapoint in the experiment, function will find these automatically if not provided.

    Returns: Extrap_results a dict with the same structure as interp_results, wih all valves now covering the entire experimental time-frame
    '''
    if global_end is None : # determining global time if not provided
        start = 0 # first time in the experiment set to 0
        ends = [valve_id['x_expanded'][-1] for valve_id in interp_results.values()] # extracting 
        global_end =  max(ends)
        n_points = int((global_end - start) * 120) + 1  # 0.5-min spacing
        global_x = np.linspace(0, global_end, n_points) # x is normalized time
        #print(global_end)
        #print(global_time[0])
        #print(global_time[-1])
        print(type(global_x))

    # extracting data for extrapolation:
    for valve_id, results in interp_results.items():
        x = results['x_expanded']
        y = results['y_interp']
        method_id = results.get(method_id, None) # graps the method id, sets None if it doesn't exist 

        # Linear extrapolation based on the first 2 points
        slope_start = (y[1] - y[0]) - (x[1] - y[0])
        slope_end = (y[-1] - y[-2]) - (x[-1] - x[-2])

    return 42


def combine_triplicates(interp_results, treatment_dict):
    '''
    Using interpolation results, a dict.
    id: valve Id for each measurement - acts as key.
    x_expanded: ½-minute time-stamps from the start of the experimment to the end.
    y_interp: interpolated flux-measurments for each time-stamp.
    
    Using treatment_dict
    keys: valve_id's as an int.
    values: method_ids as a str.

    For each treatment method, find mean-flux & std-dev for each method from 3 triplicate-fields each with unique valve id.

    Return a df containing with the following collums:
        x_expanded.
        y_mean: mean flux for each method.
        y_std
        method_id.
    '''
    combined_list = []
    treatment_groups = {} # dict with treatment_id as key and related triplicate valve ids as a value-list

    for valve_id, treatment_str in treatment_dict.items(): # looping over treatment dict
        if treatment_str not in treatment_groups: # if the method_str doesn't already exist in treatment_grups dict
            treatment_groups[treatment_str] = [] # then ad it as a key, initalize an empty list for the values

        treatment_groups[treatment_str].append(valve_id) # at the related valve_ids to the value-list

    for treatment_str, valve_ids in treatment_groups.items(): # looping over the grouped dictionay
        y = []
        x_expanded = None

        for valve_id in valve_ids:
            
            if valve_id not in interp_results:
                continue

            results = interp_results[valve_id]

   
### Constants ### 
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

### Function calls ###
df = load_data(input_folder, input_file_name)
metod_df = add_method(df,treatment_methods)
valve_data_dict = extract_valve_data(metod_df)
interpolation_dict = interpolate_valve(valve_data_dict)
extrapolate_valve(interpolation_dict)

### Print tests ### 
#print(df)
#print(metod_df.head(10))
#print(valve_data)
#print(interpolation_dict)

### Coding references ###
# https://pandas.pydata.org/docs/reference/api/pandas.Series.map.html 
# https://docs.scipy.org/doc/scipy/tutorial/interpolate/extrapolation_examples.html 