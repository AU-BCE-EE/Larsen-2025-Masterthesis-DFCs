### Script Description ###
# import flux data
# remove empty datapoints
# remove collums with background data such as temperature
# Tag current "actual" datapoints
# Create DFs related to single valve IDs
# normalize time-values, agianst first datapoint for all valves - NAN datapoints included
# Interpolate all valve fluxes
# Find common time
# Intergrate DF_DFC data, accumulated emissions
# normalize against TAN-values
# determine avg and stddev for each treatment, ie. combine triplicate triplicates - remove tails?
# For now use linear interpolation

### Packages ###
import numpy as np
import pandas as pd
from pathlib import Path

### Data treatment functions ###
def load_csv_file_as_df(file_path):
    '''
    Loads the raw picarro-files
    Helper-function to avoid repating code

    Input: file_path (Path object) the file-path of the folder the file is contained within

    returns: df (pd.df) a dataframe with all data from the raw picarro file contained within
    '''
    return pd.read_csv(file_path)
    # Collums in the file are seperated with several empty spaces

def add_tag(df, tag, colum_name):
    '''
    creates additional collom to "tag" the data

    Input:
        df: the dataframe to tag
        tag (str): the information to insert into every vallue of the new collum
        collum_name(str): name of the new collum-header

    returns:
        df with a tag-collum added
    '''
    df.loc[:, colum_name] = tag
    return df

def create_sub_dfs_per_valve(df, valve_ids=None):
    ''' 
   creating sub dfs, dfs with data from only a single valve, collectively stored in a dict for compactabilty

   Args:
        df containing the collum VALVE_ID
        valve_ids (ints or BOOL): the valve-data to be extracted, all valves of none are specifid

    Returns:
        output_dict {valve_id(int) : sub_df}   
    '''
    if valve_ids is None:
        valve_ids = df['VALVE_ID'].round(5).unique() # extracting all unique id's

    output_dict = {} # initalization of output dict

    for id in valve_ids:
        valve_df = df[df['VALVE_ID'].round(5) == id].reset_index(drop=True)
        output_dict[int(id)] = valve_df

    return output_dict

def time_normalization_valve_level(sub_df_dict):
    '''
   normalizes each sub df agianst first meassuremnt, inital NAN-rows included

   Input:
        sub_df: dictionay, valve IDs are keys, sub DFs for each valve ID are values

    Output
        sub_df: same dictionay, each sub_df with added row, Time_norm_valve

    '''
    for valve_id, sub_df in sub_df_dict.items(): # iterating over the dataframes
        first_time = sub_df['TIME_NORM_GLOBAL[h]'].iloc[0] # extracting first timevalue from current sub_df

        sub_df['TIME_NORM_VALVE[h]'] = sub_df['TIME_NORM_GLOBAL[h]'] - first_time # locally normalizing agianst first valve-specific measurement

        sub_df_dict[valve_id] = sub_df # updating the dictionary
    
    return sub_df_dict
    

def remove_nan_datapoints(sub_df_dict):
    '''
    Remove datapoints with nan-values (faulty valve)

    Input
        sub_df_dict: ditionary with valve_id as keys and dataframes as values

    Output
        sub_df_dict: same dictionary with nan-rows remmoved

    '''
    for valve_id, sub_df in sub_df_dict.items(): # iterating over the dataframes
        sub_df = sub_df.dropna(axis = 0, how = 'any').copy() # remove empty rows (due to valve error), notice the explicit creation of a copy, not a view
        sub_df_dict[valve_id] = sub_df # updating the dictionary
    
    return sub_df_dict


def interpolation_df_linear(df, tpts_per_h = 120 ):
    '''
   interpolation of the flux-values related to a specific df, by expanding the valve-specific time axis

   input:
        df: the dataframe to be interpolated
        tpoints_per_h: int, amount of time points created per hour, even spacing, point per 0.5 minute as default

    output:
        new df containing the following collums: 
            interpolated and original flux values
            interpolated and original time-values
            tag indicating wheter a specific value was meassured or interpolated
            orgignal and interpolated error-values

    '''
    # To do
    # also extract DATE_TIME for measured values 

    # extracting original flux and time-values from the df, converting each collum to a numpy array
    F_meassured = df['F[mg/h m2]'].to_numpy() 
    F_meassured_stdev = df['F_STDEV[mg/h m2]'].to_numpy()
    t_measured = df['TIME_NORM_VALVE[h]'].to_numpy()

    # preparing time-axis
    start_t = t_measured[0]
    end_t = t_measured[-1] # start and end time for the valve measurement

    n_t_pts = int((end_t - start_t) * tpts_per_h) + 1 # amounts of points per hour
    t_expanded = np.linspace(start_t, end_t, n_t_pts) # creating n_t_pts, n number of evenly spaced time points between start and endtime

    # actual linear interpolation
    F_expanded = np.interp(t_expanded, t_measured, F_meassured)  

    # tagging interpolated values and determining error of interpolated values
    measured_index_map = {t: i for i, t in enumerate(t_measured)} # creating dict of meassured vallues

    # Preparing arrays for uncertainty and tagging
    F_stdev_expanded = np.zeros_like(F_expanded)
    data_type = np.full(len(t_expanded), 'interpolated', dtype=object)

    # as time-values are floats, a tolerance value is contructed
    # 2 pts closer than the tollerance is indistinguisable with 0.5 min time resoluton, therefore considered the same point
    time_resolution_h = 1 / tpts_per_h # [h] 0.5 min
    tollerance = time_resolution_h / 2

    for i,t in enumerate(t_expanded): # iterating over the expanded time-scale
        idx = np.argmin(np.abs(t_measured - t)) # finds the closest measured value
        time_diff = abs(t_measured[idx] - t)

        if time_diff <= tollerance: # considered a measured point, extracting measured deviation
            F_stdev_expanded[i] = F_meassured_stdev[idx]
            data_type[i] = 'measured' 
            continue

        # iteraing over an interpolated point
        # Applying White2016 algoritm, eq. 15 to find deviation

        # extracting closest meassured datapoints
        if t < t_measured[idx]:
            left_idx = idx - 1
            right_idx = idx

        else: 
            left_idx =  1
            right_idx = left_idx + 1 

        t1, t2 = t_measured[left_idx], t_measured[right_idx]
        F1, F2 = F_meassured_stdev[left_idx] , F_meassured_stdev[right_idx]

        # weight factors
        w1 = (t2 - t) / (t2 - t1)
        w2 = (t - t1) / (t2 - t1)

        variance = (w1**2) * (F1**2) + (w2**2) * (F2**2)
        F_stdev_expanded[i] = np.sqrt(variance)

    # storeing expanded values within a dataframe structure
    interpolated_df = pd.DataFrame({'TIME_NORM_VALVE[h]': t_expanded,'F[mg/h m2]': F_expanded,'F_STDEV[mg/h m2]': F_stdev_expanded,'VALUE_TYPE': data_type})

    # defninning error for interpolated values
    return interpolated_df


def merge_method_dicts(sub_df_dict, treatment):
    '''
    merging triplicates (plots sharing the same treatment with different valve IDs) from the sub_df_dict structure, by averaging the triplicates, also creating a collum for the related std-deviation

    Input:
        sub_df_dict: dictionary containing valve ID's as keys and sub_dfs as values, containing a treament collum
        treatment (str): list of strings treaments to me merged

    Output:
        df containing data from all valves related to the specified treatment
    '''
 
    # To do:
    # extract sub_dfs with the same treatment 
    # interpolate these 
    # determine common time axis - times for which all 3 triplicates have datapoints
    # remove heads - inital datapoints outside common time axis
    # remove tails - final datapoints outside common time axis
    # for each datapont, find avg and propagate std-deviation most likely need to use tolerance method as interpolation function
    # return single averaged df, contaning same collums as 

### Visualization functions ### 

### Input folder and Files ###
input_path = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\Field-trails\Cattle-Slurry 2025-10-28\Piccaro-data\2-flux-data\cattle-slurry-field-flux.csv")

### Output folder and files ###

### Constants ###

### Script excecution ###
input_df = load_csv_file_as_df(input_path) # load flux-data

df_collum_drop = input_df.drop(columns=['C[PPB]','C_STDEV[PPB]', 'P_DROP[pa]','TAN_RATE[1/h]','TAN_RATE_STDEV[1/h]', 'T_GROUND_10cm[DEGC]', 'P_ATMOSPHERE[hpa]', 'TIME_NORM_LOCAL[h]']).copy() # dropping collums unneeded data further calculations

add_tag(df_collum_drop,'measured','VALUE_TYPE') # add "meassured" tag before interpolating

sub_df_dict = create_sub_dfs_per_valve(df_collum_drop)
sub_df_dict = time_normalization_valve_level(sub_df_dict)
sub_df_dict = remove_nan_datapoints(sub_df_dict)

print(sub_df_dict)

for valve_id , sub_df in sub_df_dict.items():
    interp_res = interpolation_df_linear(sub_df)
    measured_rows = interp_res[interp_res['VALUE_TYPE'] == 'measured']
    print(measured_rows)


### print test ###
#print(input_df)
#print(df.head(50))
#print(df.tail(10))


### Code references ###
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.drop.html
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.head.html
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.tail.html 
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.dropna.html 
# white2016 https://doi.org/10.1007/s10765-016-2174-6 