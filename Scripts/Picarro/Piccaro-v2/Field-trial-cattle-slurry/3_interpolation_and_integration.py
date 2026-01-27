### Script Description ###
# import flux data
# remove empty datapoints
# remove collums with background data such as temperature
# Tag current "actual" datapoints
# Create DFs related to single DFCs
# For backgrounds, interpolate and find avg value with stddev
# For actual treatments, Interpolate DF_DFC data - tag interpolated values and subtract bkg avg, remember error accumulation
# Intergrate DF_DFC data, accumulated emissions
# normalize against TAN-values
# determine avg and stddev for each treatment, ie. combine triplicate triplicates - remove tails?
# For now use linear interpolation

### Packages ###
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

def merge_method_dicts(sub_df_dict, treatment):
    '''
    merging triplicates (plots sharing the same treatment with different valve IDs) from the sub_df_dict structure, by averaing the troplicates, also creating a collum for the related std-deviation

    Input:
        sub_df_dict: dictionary containing valve ID's as keys and sub_dfs as values, containing a treament collum
        treatment (str): list of strings treaments to me merged

    Output:
        df containing data from all valves related to the specified treatment
    '''
    combined_list = []
    valve_method_grouped = {} # dict with treatment_id as key and related triplicate valve ids as a value-list

    # Group valves by treatment
    for valve_id, treatment_str in treatment_dict.items(): # looping over treatment dict
        if treatment_str not in valve_method_grouped: # if the method_str doesn't already exist in treatment_grups dict
            valve_method_grouped[treatment_str] = [] # then ad it as a key, initalize an empty list for the values

        valve_method_grouped[treatment_str].append(valve_id) # add the related valve_ids to the value-list

def interpolation(df):
    '''
   interpolation of the flux-values related to a specific df, by expanding the valve-specific time axis

   input:
        df the dataframe to be interpolated

    output:
        df containing 3 collums: 
            interpolated and original flux values
            interpolated and original local time-values
            tag indicating wheter a specific value was meassured or interpolated

    '''


### Visualization functions ### 

### Input folder and Files ###
input_path = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\Field-trails\Cattle-Slurry 2025-10-28\Piccaro-data\2-flux-data\cattle-slurry-field-flux.csv")

### Output folder and files ###

### Constants ###

### Script excecution ###
input_df = load_csv_file_as_df(input_path) # load flux-data

df_collum_drop = input_df.drop(columns=['C[PPB]','C_STDEV[PPB]', 'P_DROP[pa]','TAN_RATE[1/h]','TAN_RATE_STDEV[1/h]', 'T_GROUND_10cm[DEGC]', 'P_ATMOSPHERE[hpa]', 'TIME_NORM_LOCAL[h]']).copy() # dropping collums unneeded data further calculations

df_NAN_drop = df_collum_drop.dropna(axis = 0, how = 'any').copy() # remove empty rows (due to valve error), notice the explicit creation of a copy, not a view
add_tag(df_NAN_drop,'measured','VALUE_TYPE') # add "meassured" tag before interpolating


sub_df_dict = create_sub_dfs_per_valve(df_NAN_drop)


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