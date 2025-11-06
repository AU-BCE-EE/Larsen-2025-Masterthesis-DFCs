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
        valve_data[int(id)] = {"x": x, "y": y , 'method_id' : method_id}

    return valve_data
    
def interpolate_and_extrapolate_valve(valve_data, global_end = None, interp_method = 'linear', extrap_method = 'linear'):
    '''
    Fitting data from each valve onto a global timeframe (start and end of experiment) via interpolation and extrapolation.
    valve_data: a dict contaning known time-values (x), known flux-values (y), and a method_id.
    If global end is defined as None, the function will find it automatically. Interp_method can be either 'linear' or 'cubic' (cubic spline).
   
    Extrapolation either linear, of set-up to fil outside of bounds with nan.

    Returns a dict with x_global (global time axis), y_global (global flux-meassurements), mehtod_id, x_original and y_original.
    The last 2 mostly for acessment of the estimations.
    '''
    if global_end is None : # determining global time if not provided
        start = 0 # first time in the experiment set to 0
        ends = ends = [v['x'][-1] for v in valve_data.values()] # extracting last x-value
        global_end =  max(ends)
        n_points = int((global_end - start) * 120) + 1  # 0.5-min spacing
        x_global = np.linspace(0, global_end, n_points) # x is normalized time - notice, inital point 
        #print(global_end)
        #print(global_time[0])
        #print(global_time[-1])
        #print(type(global_x))

    # initalizing return-structure
    extrap_results = {}

    # extracting data for extrapolation:
    for id,data in valve_data.items(): # looping over the valve data dict
        x = data['x'] # normalized time
        y = data['y'] # flux
        method_id = data['method_id'] 

        # Linear extrapolation - finding the slope
        slope_start = (y[1] - y[0]) / (x[1] - x[0])
        slope_end = (y[-1] - y[-2]) / (x[-1] - x[-2])

        # initalizing an arry for y-values
        y_global = np.full_like(x_global, np.nan, dtype=float) # creating an array filled with nan (not a number) of the same length as global x

        # defining regions, before, inside and after actual measurements
        before = x_global < x[0]
        after = x_global > x[-1]
        inside = (x_global >= x[0]) & (x_global <= x[-1])

         # interpolating inside known data-range
        if interp_method == 'linear':
            y_global[inside] = np.interp(x_global[inside], x, y)  

        elif interp_method == 'cubic':
            y_global[inside] = CubicSpline(x, y)(x_global[inside])
        

        # fill y_global with interpolated or extrapolated data
        if extrap_method == 'linear':
            y_global[before] = y[0] + slope_start * (x_global[before] - x[0])
            y_global[after] =  y[-1] + slope_end * (x_global[after] - x[-1])

        elif extrap_method == 'nan': # fill before and after with none values
            y_global[before] = np.nan
            y_global[after] = np.nan

        # storing results
        extrap_results[id] = {'x_global' : x_global , 'y_global' : y_global, 'method_id' : method_id , 'actual_x' : x , 'actual_y' : y}

     
    return extrap_results

def combine_triplicates(extrap_results, treatment_dict):
    '''
    finds mean and std-deviation from each method from triplicates each with a unique valve id.

    extrap_results: dictionary containing x_global (global time-scale, start and end of experiment), 
    y_global (actual and estimated mesurements across the time-scale), methood id a str unique for each method, actual_x and actual_y
    values related to actual measurements, for each respective valve id.
    treatment_dict: a dictionary contaning valve_ids and method str

    retuns: A df with mean values and related std for each method.
    '''
    combined_list = []
    valve_method_grouped = {} # dict with treatment_id as key and related triplicate valve ids as a value-list

    # Group valves by treatment
    for valve_id, treatment_str in treatment_dict.items(): # looping over treatment dict
        if treatment_str not in valve_method_grouped: # if the method_str doesn't already exist in treatment_grups dict
            valve_method_grouped[treatment_str] = [] # then ad it as a key, initalize an empty list for the values

        valve_method_grouped[treatment_str].append(valve_id) # add the related valve_ids to the value-list

   
    # Using valve Id's from the grouped id to extract respective result from the extrapolation relusts
    for treatment_str, valve_ids in valve_method_grouped.items():
        # initializing variables
        y_data_all = [] # storing y_data from each respective valve into the list
        x_global = None
        
        # extracting data related to each id
        for valve_id in valve_ids:
            if valve_id not in extrap_results: # safey check
                print(f" Valve {valve_id} not found in extrap_results! skipping.")
                continue

            extrap_data = extrap_results[valve_id] 

            if x_global is None: # on the first go, grapping x_expanded
                x_global = extrap_data['x_global']
        
            y_data_all.append(extrap_data['y_global'])

    # Finding Mean and Stdev-values for each method
        if len(y_data_all) > 0: # avoid error if there there for some reason are no valves
            y_matrix = np.vstack(y_data_all) # n valves x n datapoints - all the valves related to 1 method 
            y_mean = np.nanmean(y_matrix, axis=0)
            y_stdev = np.nanstd(y_matrix, axis=0)
            # axis 0 coresponds to collums (same t, different valves), while axis 1 corespond to rows (same valve, differnet t)
            # nan's are ignored

            # gather the data inot the return-structure:
            combined_list.append({'x_global' : x_global, 'y_mean' : y_mean, 'y_std' : y_stdev, 'method_id': treatment_str})
        else:
            print(f"No valid data found for treatment '{treatment_str}'")

    if len(combined_list) == 0:
        print("No data combined!")
        return pd.DataFrame() # returning an empty dataframe
    
    combined_df = pd.concat(
        [pd.DataFrame(
            {'time[h]': method_dict['x_global'],
            'flux_mean[mg/m2 h]': method_dict['y_mean'],
            'flux_std[mg/m2 h]': method_dict['y_std'],
            'treatment': method_dict['method_id']}
            ) for method_dict in combined_list], ignore_index=True)
    return combined_df
   

def baselinecorrection(df_mean, baseline_id = 'B'):
    '''
    Perform baselinecorrection for all methods via subtraction of baseline fluxes for each time-value.
    '''
    df = df_mean.copy()

    # Find baseline data
    baseline = df[df['treatment']] == baseline_id.set_index('time[h]') 
    other_methods = df[df['treatment']] != baseline_id.set_index('time[h]')
    # time set as the index_collum

    # creating a new df which the baseline is a seperate collum, alligned in time with actual data 
    merged_df = other_methods.merge(
        baseline[['flux_mean[mg/m2 h]'], 'flux_std[mg/m2 h]'],
        left_index = True,
        right_index = True,
        suffixes = ('','_baseline')
    ) 
    # stating which collums from the baseline_df to add
    # sorting via the respective indexces, the time
    # title on other collum left as is, baseline collum tagged 

    # subtracting the baseline-collum row-wise (for for each time-value), making the corrected a new collum
    merged_df['flux_mean_corrected[mg/m2 h]'] =  ( merged_df['flux_mean[mg/m2 h]'] - merged_df['flux_mean[mg/m2 h]_baseline'])

    # propogation of error from correction
    merged_df['flux_std_corrected'] = np.sqrt( merged_df['flux_std[mg/m2 h]']**2 + merged_df['flux_std_baseline[mg/m2 h]']**2)  

    # Creating output-df with relevant collums
    corrected_df = merged_df.reset_index()[['time[h]', 'treatment', 'flux_mean_corrected[mg/m2 h]', 'flux_std_corrected[mg/m2 h]']]
    # time stopped being index-collum
    return corrected_df

def integration(corrected_df, TAN_m2):
    '''
    Identifies all unique methods present in the df and integrates each one individually,
    providing individual integral-values [mg/m2] as a seperate collum, and a cumulated integralvalue in a seperate collum.
    Finally uses total-ammonia nitrogen value (TAN) [mg/m2] to create addtional integral-collums with normalized values. 
    '''
    for method in corrected_df['treatment'].unique():
        # creating a df for each method
        method_df = corrected_df[corrected_df['treatment'] == method].reset_index(drop=True)
        integrated_results = [] 

        # initializing objects to gather integral-data
        integrals = [0.0] # as the 1st point cannot be calculated
        cumulative = [0.0]

        # looping over the rows of each integral
        for row_index in range(1,len(method_df)): # loop started at 2nd point

            # extracting flux and time-values for the integrations
            t0, t1 = method_df.loc[row_index - 1, 'time[h]'], method_df.loc[row_index, 'time[h]']
            flux0, flux1 = method_df.loc[row_index - 1, 'flux_mean_corrected[mg/m2 h]'], method_df.loc[row_index, 'flux_mean_corrected[mg/m2 h]']

            if np.isnan(flux0) or np.isnan(flux1): # check if the flux is nan
                integral = np.nan # in which case the integral is also nan
            else:
                integral = 0.5 * (flux0 + flux1) * (t1 - t0 ) # trapezoidal integration
        
        integrals.append(integral) 
        cumulative.append(cumulative[-1] + (integral if not np.isnan(integral) else 0)) # adding current an previous integralsum together
        # if the integarl is nan it is simply set to 0 for the cumulated integral-value
        
        # creating result-collums
        method_df['integral_step[mg/m2]'] = integrals
        method_df['integral_cumulative[mg/m2]'] = cumulative
        method_df['integral_cumulative_norm[TAN]'] = method_df['integral_cumulative[mg/m2]'] / TAN_m2

        integrated_results.append(method_df)

    # combining results from all methods into a cobined df
    integrated_df = pd.concat(integrated_results, ignore_index=True)
    return integrated_df


        

    # add the calculated integral-data as addtional collums of corrected_df and return this together

    # add addtional collums where the integral-data is corrected by TAN

    # created a small df with simply shows final integral-values for each method, return this as well






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
method_df = add_method(df,treatment_methods)
valve_data_dict = extract_valve_data(method_df)


### Print tests ### 
#print(df)
#print(metod_df.head(10))
#print(valve_data)
#print(interpolation_dict)

### Coding references ###
# https://pandas.pydata.org/docs/reference/api/pandas.Series.map.html 
# https://docs.scipy.org/doc/scipy/tutorial/interpolate/extrapolation_examples.html 
# https://numpy.org/doc/2.2/reference/generated/numpy.vstack.html
# https://numpy.org/doc/2.3/reference/generated/numpy.mean.html 
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html 
# https://pandas.pydata.org/docs/reference/api/pandas.unique.html 
# https://numpy.org/doc/2.3/reference/generated/numpy.isnan.html
# https://en.wikipedia.org/wiki/Trapezoidal_rule 