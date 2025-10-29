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


### Changing another script, saving this here for now ### 
