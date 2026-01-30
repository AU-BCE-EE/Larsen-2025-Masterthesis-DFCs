### Script Description ###
# import flux data
# remove empty datapoints
# remove collums with background data such as temperature
# Tag current "actual" datapoints
# Create DFs related to single valve IDs
# normalize time-values, agianst first datapoint for all valves - NAN datapoints included
# For backgrounds, interpolate and find avg value with stddev
# For actual treatments, Interpolate DF_DFC data - tag interpolated values and subtract bkg avg, remember error accumulation
# Intergrate DF_DFC data, accumulated emissions
# normalize against TAN-values
# determine avg and stddev for each treatment, ie. combine triplicate triplicates - remove tails?
# For now use linear interpolation

### Packages ###
import pandas as pd
from numpy import linspace
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


def round_flux(df):
    '''
    rounds flux-values before interpolation based of measurement-specific std-deviation
    
    input: 
        dataframe with the F[mg/h m2] and F_STDEV[mg/h m2] collum

    output:
        original dataframe containing a F_rounded[mg/h m2] collum

    '''
    for index, row in df.interows():
        F = df['F[mg/h m2]']
        F_stdev = df['F_STDEV[mg/ h m2]'] 

def linear_interpolation(df, tpts_per_h = 120 ):
    '''
   interpolation of the flux-values related to a specific df, by expanding the valve-specific time axis

   input:
        df: the dataframe to be interpolated
        tpoints_per_h: int, amount of time points created per hour, even spacing, point per 0.5 minute as default

    output:
        df containing 3 collums: 
            interpolated and original flux values
            interpolated and original time-values
            tag indicating wheter a specific value was meassured or interpolated

    '''
    # extracting original flux and time-values from the df
    # rounding decimals based on the valve-specific std-deviation before interpolation

    df.round({'F[mg/h m2]': 1})
    F = df['F[mg/h m2]']
    
    # prepating time-axis
    start_t = df['TIME_NORM_VALVE[h]'].iloc[0]
    end_t = df['TIME_NORM_VALVE[h]'].iloc[-1]

    n_t_pts = int((start_t - end_t) * tpts_per_h) + 1 

    interp_time_axis = linspace(start_t, end_t, n_t_pts) # creating n_t_pts, n number of evenly spaced time points between start and endtime




def merge_method_dicts(sub_df_dict, treatment):
    '''
    merging triplicates (plots sharing the same treatment with different valve IDs) from the sub_df_dict structure, by averaging the triplicates, also creating a collum for the related std-deviation

    Input:
        sub_df_dict: dictionary containing valve ID's as keys and sub_dfs as values, containing a treament collum
        treatment (str): list of strings treaments to me merged

    Output:
        df containing data from all valves related to the specified treatment
    '''
    combined_list = []
    valve_method_grouped = {} # dict with treatment_id as key and related triplicate valve ids as a value-list

    # Group valves by treatment
    #for valve_id, treatment_str in treatment_dict.items(): # looping over treatment dict
        #if treatment_str not in valve_method_grouped: # if the method_str doesn't already exist in treatment_grups dict
            #valve_method_grouped[treatment_str] = [] # then ad it as a key, initalize an empty list for the values

        #valve_method_grouped[treatment_str].append(valve_id) # add the related valve_ids to the value-list

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


### print test ###
#print(input_df)
#print(df.head(50))
#print(df.tail(10))
print(sub_df_dict)

### Code references ###
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.drop.html
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.head.html
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.tail.html 
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.dropna.html 