##### Script Description #####
# import flux data
# remove unneeded collums
# remove nan rows
# create new timeline "time of aplication" instead of global time - THIS IS THE KEY CHANGE FOR V2
# determine background range(range within all 3 triplicates) and smallest treatment range, using time of aplication range
# perform interpolation on bck-range or smalest treatment range (the one which is smallest)
# background-correct all proper plots, remove bck-data for upstream functions- save csv-file
# TAN-normalize all proper plots
# integrate all proper plots, normalize cumulated emissions
# merge triplicates and determine biological deviation

##### Packages #####
import numpy as np
import pandas as pd
from pathlib import Path

### functions ###
def load_csv_file_as_df(file_path:Path)-> pd.DataFrame:
    '''
    Loads the raw picarro-files
    Helper-function to avoid repating code

    Input: file_path (Path object) the file-path of the folder the file is contained within

    returns: df (pd.df) a dataframe with all data from the raw picarro file contained within
    '''
    return pd.read_csv(file_path)
    # Collums in the file are seperated with several empty spaces


def time_normalization_application(raw_df:pd.DataFrame, valve_start_dict:dict)-> pd.DataFrame:
    '''
   Creating new time-axis based of starting time of each experiment, instead staring time for entire experiment

   Input:
        raw_df: dataframe contaning raw datapoints from all valves, following collum are expected: TIME_NORM_GLOBAL[h] and VALVE_ID
        valve_start_dict: dictionary containing valve id's as keys and starting time of each plot as values 

    returns
        copy of raw_df with and added collum TIME_SINCE_APP[h] 
 
    '''
    df_copy = raw_df.copy() # creating a copy to avid changing raw df
    df_copy['TIME_SINCE_APP[h]'] = 0.0 # inialize new collum with 0's

    for valve_id, start_time in valve_start_dict.items():  # extract data from the dict
        mask = df_copy['VALVE_ID'] == valve_id # filtering the df to data which shares valve
        df_copy.loc[mask, 'TIME_SINCE_APP[h]'] = df_copy.loc[mask, 'TIME_NORM_GLOBAL[h]'] - start_time # shifting the time-axis

    return df_copy

def remove_nan_rows(raw_df:pd.DataFrame) -> pd.DataFrame:
    '''
    remove rows containing nan from a df - present due to valve error

    Input:
        raw_df: dataframe containing raw datapoints from all valves

    Returns:
        filtered df: df with nan-containing rows removed
    '''
    copy_df = raw_df.copy() # creating a copy to avid changing raw df
    filtered_df = copy_df.dropna(axis = 0, how = 'any') # dropping any rows contaning nan

    return filtered_df

def determine_smallest_timerange(filtered_df):
    return 'not done'

def interpolation(filtered_df, smallest_timerange):
    return 'not done'

def background_correction(interp_df):
    return 'not done'

def TAN_normalization(BC_interp_df):
    return 'not done'

def integration(BC_interp_df):
    return 'not done'

def merge_triplicates(integrated_df):
    return 'not done'

##### Input folder and Files #####
input_path = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\Field-trails\Cattle-Slurry 2025-10-28\Piccaro-data\2-flux-data\cattle-slurry-field-flux.csv")

##### Constants #####
Aplication_time_dict = {4.0 : 0, 5.0 : 0.13, 8.0 : 0.27, 9.0: 0.40, 11.0: 0.53, 12.0 : 0.67, 13.0: 0.80, 14.0: 0.93, 15.0: 1.07, 16.0: 1.20, 17.0: 1.33, 18.0: 1.47} # [h] 

##### Script excecution #####
raw_df = load_csv_file_as_df(input_path) # load flux-data

# dropping collums not needed for down-stream
raw_df_small = raw_df.drop(columns=['C[PPB]','C_STDEV[PPB]', 'P_DROP[pa]','TAN_RATE[1/h]','TAN_RATE_STDEV[1/h]', 'P_ATMOSPHERE[hpa]', 'TIME_NORM_LOCAL[h]', 'TAN[mg/m2]','TAN_STDEV[mg/m2]']).copy() ; #print(raw_df_small)
raw_df_new_time = time_normalization_application(raw_df_small, Aplication_time_dict) ; print(raw_df_new_time)
filtered_df = remove_nan_rows(raw_df_new_time) ; print(filtered_df)



