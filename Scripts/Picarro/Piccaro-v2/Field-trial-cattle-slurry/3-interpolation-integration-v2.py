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


def time_normalization_valve(df:pd.DataFrame)-> pd.DataFrame:
    '''
   normalizes each sub df agianst first meassuremnt

   Input:
        sub_df: dictionay, valve IDs are keys, sub DFs for each valve ID are values

    Output
        sub_df: same dictionay, each sub_df with added row, Time_norm_valve

    '''
    first_time = df['TIME_NORM_GLOBAL[h]'].iloc[0] # extracting first timevalue from current sub_df

    df['TIME_NORM_VALVE[h]'] = df['TIME_NORM_GLOBAL[h]'] - first_time # locally normalizing agianst first valve-specific measurement

    return df.copy()

### Input folder and Files ###
input_path = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\Field-trails\Cattle-Slurry 2025-10-28\Piccaro-data\2-flux-data\cattle-slurry-field-flux.csv")

### Script excecution ###
input_df = load_csv_file_as_df(input_path) # load flux-data

# dropping collums not needed for down-stream
input_df = input_df.drop(columns=['C[PPB]','C_STDEV[PPB]', 'P_DROP[pa]','TAN_RATE[1/h]','TAN_RATE_STDEV[1/h]', 'T_GROUND_10cm[DEGC]', 'P_ATMOSPHERE[hpa]', 'TIME_NORM_LOCAL[h]', 'TAN[mg/m2]','TAN_STDEV[mg/m2]']).copy()
input_df.rename(columns={'F[mg/h m2]' : 'F_RAW[mg/h m2]', 'F_STDEV[mg/h m2]':'STDEV_NOISE[mg/ h m2]'}, inplace= True) 
time_normalization_valve(input_df)
print(input_df)
