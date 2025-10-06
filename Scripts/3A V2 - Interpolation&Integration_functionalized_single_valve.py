### Script Description ###
# same functionality as 3A V1, but functionalized
# Thereby, splitting code related for creating visuals and code for extracting integration-results

### Script version ###
# V2 - functionalized to more cleanly split code for visualization & integration
# handles everything using valve-Id's still usefull for spotting odd data


### Packages ####
import matplotlib.pyplot as plt
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
    return pd.read_csv(input_folder / input_file_name) # notice the / to attach the strings, non-std Python formatting


def extract_valve_data(df,valve_ids):
    ''' 
    Extraxt data from a df with data from multiple valves.
    Extract data related to a specific valve coresponding id's in a list of valve ids.
    currently setup to extract flux and normalized time.
    returns the extracted data as a dict
    '''
    valve_data = {}
    for id in valve_ids:
        valve_df = df[df['VALVE_POS[-]'].round(5) == id].reset_index(drop=True) # selects the VALVE-POS collum from df,
        # rounds the number extra precuation, as Python is weird with floats,
        # Checks if the VALVE-POS values matches the current id,
        # Based on this check, creates a new reduced df with reset index values, default is keeping the ones from the old folder, with data purely related to 1 valve

        x = valve_df["TIME_NORMALIZED[h]"].values # extracting time-collum normalized with the start of experiment set to 0
        y = valve_df["F[mg/m2 h]"].values # extracting flux meassurements
        valve_data[id] = {"x": x, "y": y} # stores data from the id in the dict

    return valve_data


def interpolate_valve(valve_data, interp_method = 'all'):
    '''
    Performs interpolations using known x (norm time) and y-values (flux) on data coresponding to each valve id stored in a dict
    Returns a dict of dicts, the valve id being the outher key, with the other values being another dict with results from each interpolation
    '''
    interp_results = {} # initalizing the return-dict

    for id,data in valve_data.items(): # looping over the valve data dict
        x,y = data['x'], data['y'] # extracting x and y data from the dict

        x_expanded = np.linspace(0, x[-1], num=int(x[-1] * 120) + 1) # expands the time-values to every half min

        interp_result = {"x_expanded": x_expanded} # extract the x-value into the dict

        if interp_method in ("all", "linear"):
            interp_result["y_linear"] = np.interp(x_expanded, x, y) # linear interpolation of "missing" minutes, using known y-points

        if interp_method in ("all", "cubic"):
            interp_result["y_cubic"] = CubicSpline(x, y)(x_expanded) # cubic spline interpolation of "missing" minutes, using known y-points

        interp_results[id] = interp_result # add current itetation to the return_dict

    return interp_results



def integrate_valve(valve_data, interp_results, TAN_m2):
    """
    valvedata: dict with valve id as key, and x (normalized time), and y (flux-measurements) as values. Used for id-looping.
    interp_results: dict with valve id as key, x_expanded (normalized ½ min-basis), and interpresults (y-data from each respective interpolation) method.
    TAN_m2: constant used to normalize flux-values

    Returns integrals - dict of dict with valve id as outer key, inner key is integral results from each interpolation.
    function uses nympy pre-built trapezoidal integration function, which are provided x-expanded and y-values from each respective interpolation
    """
    integrals = {} # initializing outer dict

    for id,data in valve_data.items(): # looping over results from each id

        results = interp_results[id] # y-data from each respective interpolation result

        x_expanded = results["x_expanded"] # grapping expanded x-values from the interpolation dict
        
        integral = {} # saving data for the current integral as a dict

        if "y_linear" in results:
            y_linear_norm = results["y_linear"] / TAN_m2
            integral["integral_lin"] = np.trapezoid(y_linear_norm, x_expanded)

        if "y_cubic" in results:
            y_cubic_norm = results["y_cubic"] / TAN_m2
            integral["integral_splin"] = np.trapezoid(y_cubic_norm, x_expanded)

        integrals[id] = integral

    return integrals

def plot_interp_results(valve_id, valve_data, interp_results):
    """
    Plot original and any interpolated fluxes.
    """
   # extracting original measurements
    x = valve_data[valve_id]["x"]
    y = valve_data[valve_id]["y"]

    # extracting interpolated data
    results = interp_results[valve_id]
    x_expanded = results["x_expanded"]

    if "y_linear" in results:
        plt.plot(x_expanded, results["y_linear"], 'x', color='black', markersize=1,
                 label=f'valve {valve_id} (linear interp)')
        
    if "y_cubic" in results:
        plt.plot(x_expanded, results["y_cubic"], 'x', color='gray', markersize=1,
                 label=f'valve {valve_id} (cubic spline interp)')

    
    plt.plot(x, y, 'o', color='red', markersize=5, label=f'valve {valve_id} (original)')
    plt.xlabel('time [h]')
    plt.ylabel('flux [mg / m2 h]')
    plt.legend()
    plt.show()

## Constants ## 
# Folders
input_folder = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Speciale kodning - store filer\testdata - dummy data for coding\2 Dummy_converted") # copy the filepath
input_file_name = 'dummy_test_1_converted.csv' # copy the name as a string, don't forget .csv
valve_ids = [5,9,16] # valve ID's to be investigated as a list


# Tan & slurry aplication
TAN = 1800 # [mg/L] Total ammonia nitrogen for the slurry used in this experiment 
slurry_aplication = 3.5 # [L/m2] 
TAN_m2 = TAN * slurry_aplication # [mg/m2], amount of TAN per m2

## Function-calls ## 
df = load_data(input_folder,input_file_name)
valve_data = extract_valve_data(df,valve_ids)
interp_results = interpolate_valve(valve_data, interp_method="all")  # only linear
integrals = integrate_valve(valve_data, interp_results, TAN_m2)
plot_interp_results(9, valve_data, interp_results)

## Print tests ##
#print(valve_data[5]['x'])
#print(integrals)
### Coding references ### 