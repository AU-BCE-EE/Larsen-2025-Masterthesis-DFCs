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


# To do 
# considering simplifying function structure, should use df's instead of dict with df's contained
# potentially extend background range such that areas with only 1 and 2 plots are used, only for plotting
# 

### Packages ###
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.integrate import cumulative_trapezoid

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


def create_sub_dfs_per_valve(df, valve_ids=None):
    ''' 
   creating sub dfs, dfs with data from only a single valve, collectively stored in a dict for compactabilty

   Input:
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
   normalizes each sub df agianst first meassuremnt

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


def find_treatment_time_range(sub_df_dict, treatment):
    '''
    Finds the smallest common time range across all treatments in treatment_list.

    Input:
        sub_df_dict: Dictionary with valve_id as keys and DataFrames as values.
        treatment_list: List of treatment strings.

    Output:
        (t_start, t_end): Tuple of floats representing the smallest common time range.
    '''
    starts = []
    ends = []

    for sub_df in sub_df_dict.values():
        if sub_df['TREATMENT'].iloc[0] == treatment:
            start = sub_df['TIME_NORM_GLOBAL[h]'].iloc[0]
            end = sub_df['TIME_NORM_GLOBAL[h]'].iloc[-1]
            #print(start, end)

            starts.append(start)
            ends.append(end)


    return max(starts), min(ends)
    
        
def interpolation_df_linear(df: pd.DataFrame, background_time_range: tuple[int], tpts_per_h = 120) -> pd.DataFrame:
    '''
   interpolation of the flux-values related to a specific df, by expanding the valve-specific time axis

   input:
        df: the dataframe to be interpolated
        tpoints_per_h: int, amount of time points created per hour, even spacing, point per 0.5 minute as default - essentially the chosen resolution
        background_time_range (tuble): specified start and end for the interpolation, found automatically for the specific valve if undefined

    output:
        new df containing the following collums: 
            interpolated and original flux values
            interpolated and original time-values
            tag indicating wheter a specific value was meassured or interpolated
            orgignal and interpolated error-values

    '''
    # To do
    # also extract metadata such as DATETIME and TREATMENT? - might be done better in merging function?

    # extracting original flux and time-values from the df, converting each collum to a numpy array
    F_measured = df['F[mg/h m2]'].to_numpy() 
    F_measured_stdev = df['F_STDEV[mg/h m2]'].to_numpy()
    t_measured = df['TIME_NORM_GLOBAL[h]'].to_numpy()

    treatment = df['TREATMENT'].iloc[0]

    # background time range
    background_start = background_time_range[0]
    background_end = background_time_range[1]

    # Case 1, measurements fall outside the background range and is filtered off
    # Case 2, measurments fall entirely inside background range, the time axis is reduced

    # creating largest possible time-axis based on background range
    n_t_pts = int((background_end - background_start) * tpts_per_h) + 1 # amount of points
    t_expanded = np.linspace(background_start, background_end, n_t_pts) # creating evenly spaced time points between start and endtime

    # filtering t_expanded to be within measuring range if this is one is smaller
    valid_min = t_measured[0]
    valid_max = t_measured[-1]
    t_expanded = t_expanded[(t_expanded >= valid_min) & (t_expanded <= valid_max)]

    # actual linear interpolation
    F_expanded = np.interp(t_expanded, t_measured, F_measured)  

    # Preparing array for uncertainty calculation
    F_stdev_expanded = np.zeros_like(F_expanded)

    # as time-values are floats, a tolerance value is constructed
    # 2 pts closer than the tollerance is indistinguisable within chosen resoluton, therefore considered the same point
    time_resolution_h = 1 / tpts_per_h # [h] 120 points per hour = 0.5 min
    tolerance = time_resolution_h / 2 # [h] 0.25 min

    for i, t in enumerate(t_expanded):
        # find closest measured point to the right
        right_idx = np.searchsorted(t_measured, t)
        left_idx = right_idx - 1

        # time-point so close(with repect to the tolerance) to an actual measurement that it is treated as such
        if (left_idx >= 0 and abs(t_measured[left_idx] - t) <= tolerance):
            F_stdev_expanded[i] = F_measured_stdev[left_idx] # std-deviation from the measured point is used
            continue
        
        # if 1 measured point cannot be found on either side (happens at LHS data boundary) deviation is undefined
        if left_idx < 0 or right_idx >= len(t_measured):
            F_stdev_expanded[i] = np.nan
            continue
        
        # both measured point was found without issues, varriance interpolation 
        t1, t2 = t_measured[left_idx], t_measured[right_idx]
        F1, F2 = F_measured_stdev[left_idx], F_measured_stdev[right_idx]

        # weight functions
        w1 = (t2 - t) / (t2 - t1)
        w2 = (t - t1) / (t2 - t1)

        variance = (w1**2) * (F1**2) + (w2**2) * (F2**2)
        F_stdev_expanded[i] = np.sqrt(variance)

    # Create DATETIME for interpolated values   
    experiment_start = pd.to_datetime(df['DATE_TIME'].iloc[0]) - pd.to_timedelta(df['TIME_NORM_GLOBAL[h]'].iloc[0], unit='h')
    datetime_expanded = experiment_start + pd.to_timedelta(t_expanded, unit='h')

        
    # storeing expanded values within a dataframe structure
    interpolated_df = pd.DataFrame({'TIME_NORM_GLOBAL[h]': t_expanded,'F[mg/h m2]': F_expanded,'F_STDEV[mg/h m2]': F_stdev_expanded,"DATE_TIME":datetime_expanded , 'TREATMENT': treatment})

    return interpolated_df


def merge_baseline_triplicates(sub_df_dict: dict, treatment: str) -> pd.DataFrame:
    '''
    merge triplicates (plots sharing the same treatment with different valve IDs) from the sub_df_dict structure, by averaging the triplicates, also creating a collum for the related std-deviation.
    Expects triplicates to be on the same time-axis, but not necesaily of the same length

    Input:
        sub_df_dict: dictionary containing valve ID's as keys and sub_dfs as values, containing a treament collum
        treatment (str): str treament to me merged

    Output:
        df containing interpolated, and averaged flux data with the related std-deviation f
    '''
    # To do:
    # extract dfs with the same treatment 
    # interpolate these
    # determine common time axis - times for which all 3 triplicates have datapoints - is this too conservative?
    # remove heads - inital datapoints outside common time axis
    # remove tails - final datapoints outside common time axis 
    # for each datapoint, find avg and propagate std-deviation most likely need to use tolerance method as interpolation function
    # return single averaged df, contaning same collums as 
   
    triplicates = []
    # 1. Extract and interpolate triplicates
    for valve_id, sub_df in sub_df_dict.items():
        if sub_df['TREATMENT'].iloc[0] == treatment:
            triplicates.append(sub_df.copy())

    concat = pd.concat(triplicates, ignore_index = True)
    grouped = concat.groupby('TIME_NORM_GLOBAL[h]')

    merged_df = grouped.agg(
        F_MEAN=('F[mg/h m2]', 'mean'),
        F_STDEV_TRIPLICATES=('F[mg/h m2]', lambda x: x.std(ddof=1)  if len(x) >= 3 else np.nan),
        N_REPLICATES=('F[mg/h m2]', 'count'),
        DATE_TIME=('DATE_TIME', 'first'),
        TREATMENT=('TREATMENT', 'first')
    )

    merged_df = merged_df.reset_index()

    return merged_df

def baseline_correction(sub_df_dict:dict, baseline_df:pd.DataFrame) -> dict:
    '''
    subtracts baseline flux from individual plot data - all data alligned to same time-grid, but has indvidal lengths

    Input:
        sub_df_dict: dictionary containing valve ID's as keys and sub_dfs as values, containing a treament collum
        baseline_df: dataframe containing averaged baseline flux

    output:
        sub_df_dict: same dictionary with corrected flux-data

    '''
    baseline_df['TIME_NORM_GLOBAL[h]'] = baseline_df['TIME_NORM_GLOBAL[h]'].round(3)
    baseline_small = baseline_df[['TIME_NORM_GLOBAL[h]', 'F_MEAN']].copy()

    for id, sub_df in sub_df_dict.items():
        sub_df['TIME_NORM_GLOBAL[h]'] = sub_df['TIME_NORM_GLOBAL[h]'].round(3)
        
        if sub_df['TREATMENT'].iloc[0] == 'BACKGROUND':
            continue

        merged = pd.merge(sub_df, baseline_small, on='TIME_NORM_GLOBAL[h]', how='left')
        merged['F_BC[mg/h m2]'] = merged['F[mg/h m2]'] - merged['F_MEAN'] # BC = baseline corrected
        merged = merged.drop(columns=['F_MEAN'])
        sub_df_dict[id] = merged

    return sub_df_dict


def TAN_normalization(sub_df_dict: dict, TAN_M2_dict : dict):
    '''
    normalizes interpolated baselinecorected flux-values [mg/ h m2] against TAN applied in slurry [mg/m2]

    input: 
        sub_df_dict: dictionary containing valve ID's as keys and sub_dfs as values, containing a treament collum
        TAN_M2: dictionary containing treatments(str) as keys, and applied TAN[mg/m2] as values
        TAN_M2_stdev_dict: dictionary, same structure as TAN_M2 with related std-deviation

    output:
        in the sub_df_dict, 
    '''
    for valve_id, sub_df in sub_df_dict.items():
        treatment = sub_df['TREATMENT'].iloc[0]

        if treatment == 'BACKGROUND':
            continue

        TAN_value = TAN_M2_dict[treatment]

        # Normalized flux [%/h]
        sub_df['F_TAN[%/h]'] = sub_df['F_BC[mg/h m2]'] / TAN_value * 100


        sub_df_dict[valve_id] = sub_df

    return sub_df_dict


def integration(sub_df_dict: dict, TAN_m2: dict):
    '''
   integrates individual plotdata
   input: dictionary containing valve ID's as keys and sub_dfs as values, containing a treament collum

   output: dictionary, for each non-background dataframe the following collums are added
        %tan [1/h], flux[mg/m2 h] normalized against TAN added from slurry [mg/m2]
        acumulated emission, integral result of emissions [mg/m2]
        %acumulated emission, integral result normalized against TAN added from slurry [mg/m2]
    '''
    for valve_id, sub_df in sub_df_dict.items():
        treatment = sub_df['TREATMENT'].iloc[0]

        if treatment == 'BACKGROUND':
            continue

        t = sub_df['TIME_NORM_GLOBAL[h]'].to_numpy()
        F = sub_df['F_BC[mg/h m2]'].to_numpy()

        # cumulative integral using trapezoidal rule
        cumulative_emission = cumulative_trapezoid(F, t, initial=0)  # mg/m2

        sub_df['EMISSION_cum[mg/m2]'] = cumulative_emission
        sub_df['EMISSION_cum[%TAN]'] = cumulative_emission / TAN_M2_dict[treatment] * 100

        sub_df_dict[valve_id] = sub_df

    return sub_df_dict
        

def merge_treatment_triplicates(sub_df_dict: dict, treatment: str) -> pd.DataFrame:
    '''
    merge triplicates (plots sharing the same treatment with different valve IDs) from the sub_df_dict structure, by averaging the triplicates, also creating a collum for the related std-deviation.
    Expects triplicates to be on the same time-axis, but not necesaily of the same length

    Input:
        sub_df_dict: dictionary containing valve ID's as keys and sub_dfs as values, containing a treament collum
        treatment (str): str treament to me merged

    Output:
        df containing interpolated, and averaged flux data with the related std-deviation f
    '''
    # To do:
    # extract dfs with the same treatment 
    # interpolate these
    # determine common time axis - times for which all 3 triplicates have datapoints - is this too conservative?
    # remove heads - inital datapoints outside common time axis
    # remove tails - final datapoints outside common time axis 
    # for each datapoint, find avg and propagate std-deviation most likely need to use tolerance method as interpolation function
    # return single averaged df, contaning same collums as 
   
   # ectract df's related to specific treatment 
    treatment_dfs = [df.copy() for df in sub_df_dict.values()
        if df['TREATMENT'].iloc[0] == treatment]
    
    # determine common time range
    starts = [df['TIME_NORM_GLOBAL[h]'].iloc[0] for df in treatment_dfs]
    ends   = [df['TIME_NORM_GLOBAL[h]'].iloc[-1] for df in treatment_dfs]

    t_start = max(starts)
    t_end   = min(ends)

    trimmed = []
    for df in treatment_dfs:
        mask = ((df['TIME_NORM_GLOBAL[h]'] >= t_start) & (df['TIME_NORM_GLOBAL[h]'] <= t_end))
        trimmed.append(df.loc[mask])

    # merge
    concat = pd.concat(trimmed, ignore_index=True)

    grouped = concat.groupby('TIME_NORM_GLOBAL[h]')

    merged_df = grouped.agg(
        F_BC_mean=('F_BC[mg/h m2]', 'mean'),
        F_BC_std=('F_BC[mg/h m2]', lambda x: x.std(ddof=1)),

        F_TAN_mean=('F_TAN[%/h]', 'mean'),
        F_TAN_std=('F_TAN[%/h]', lambda x: x.std(ddof=1)),

        EMISSION_cum_mean=('EMISSION_cum[mg/m2]', 'mean'),
        EMISSION_cum_std=('EMISSION_cum[mg/m2]', lambda x: x.std(ddof=1)),

        EMISSION_cum_TAN_mean=('EMISSION_cum[%TAN]', 'mean'),
        EMISSION_cum_TAN_std=('EMISSION_cum[%TAN]', lambda x: x.std(ddof=1)),

        N_REPLICATES=('F_BC[mg/h m2]', 'count'),

        DATE_TIME=('DATE_TIME', 'first'),
        TREATMENT=('TREATMENT', 'first'))

    merged_df = merged_df.reset_index()

    return merged_df

### Input folder and Files ###
input_path = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\Field-trails\Cattle-Slurry 2025-10-28\Piccaro-data\2-flux-data\cattle-slurry-field-flux.csv")

### Output folder and files ###

### Constants ###
TAN_M2_dict = {'AA' : 5371.0, 'RAW': 5218.4, 'H2SO4': 5466.2} # [mg/m2]
TaN_M2_stdev_dict = {'AA' : 143.2, 'RAW': 165.7, 'H2SO4': 95.3} # [mg/m2]

### Script excecution ###
input_df = load_csv_file_as_df(input_path) # load flux-data

df_collum_drop = input_df.drop(columns=['C[PPB]','C_STDEV[PPB]', 'P_DROP[pa]','TAN_RATE[1/h]','TAN_RATE_STDEV[1/h]', 'T_GROUND_10cm[DEGC]', 'P_ATMOSPHERE[hpa]', 'TIME_NORM_LOCAL[h]']).copy() # dropping collums unneeded data further calculations

sub_df_dict = create_sub_dfs_per_valve(df_collum_drop)
sub_df_dict = time_normalization_valve_level(sub_df_dict)
sub_df_dict = remove_nan_datapoints(sub_df_dict)
#print(sub_df_dict)


bg_range = find_treatment_time_range( sub_df_dict,'BACKGROUND')
#print(bg_range, 'BACKGROUND')

for id, sub_df in sub_df_dict.items():
    interp_df = interpolation_df_linear(sub_df, bg_range, tpts_per_h=7.5)
    sub_df_dict[id] = interp_df
#print(sub_df_dict)

baseline_df = merge_baseline_triplicates(sub_df_dict, 'BACKGROUND')
#print(merge_baseline_triplicates(sub_df_dict, 'BACKGROUND'))

sub_df_dict = baseline_correction(sub_df_dict, baseline_df)
sub_df_dict = TAN_normalization(sub_df_dict, TAN_M2_dict)
sub_df_dict = integration(sub_df_dict, TAN_M2_dict)
#print(sub_df_dict)

raw_df = merge_treatment_triplicates(sub_df_dict, 'RAW')
H2SO4_df = merge_treatment_triplicates(sub_df_dict, 'H2SO4')
AA_df = merge_treatment_triplicates(sub_df_dict, 'AA')
print(raw_df)
print(H2SO4_df)
print(AA_df)


### Code references ###
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.drop.html
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.head.html
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.tail.html 
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.dropna.html 
# white2016 https://doi.org/10.1007/s10765-016-2174-6 