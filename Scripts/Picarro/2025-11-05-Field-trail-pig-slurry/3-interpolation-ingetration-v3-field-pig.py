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


##### To do #####
# create prints of final accumulated emissions in function
# create plot of all merged treatments

##### Packages #####
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import random
from scipy.integrate import cumulative_trapezoid
from pathlib import Path

### functions ###
def load_csv_file_as_df(file_path:Path)-> pd.DataFrame:
    '''
    Loads the raw picarro-files
    Helper-function to avoid repating code

    Input: file_path (Path object) the file-path of the folder the file is contained within

    output: df (pd.df) a dataframe with all data from the raw picarro file contained within
    '''
    return pd.read_csv(file_path)
    # Collums in the file are seperated with several empty spaces

def time_normalization_application(raw_df:pd.DataFrame, valve_start_dict:dict)-> pd.DataFrame:
    '''
   Creating new time-axis based of slurry aplication and plot measurement start, instead staring time for entire experiment

   Input:
        raw_df: dataframe contaning raw datapoints from all valves, following collum are expected: TIME_NORM_GLOBAL[h] and VALVE_ID
        valve_start_dict: dictionary containing valve id's as keys and starting time of each plot as values 

    output
        copy of raw_df with and added collum TIME_SINCE_APP[h] 
 
    '''
    df_copy = raw_df.copy() # creating a copy to avid changing raw df
    df_copy['TIME_SINCE_APP[h]'] = 0.0 # inialize new collum with 0's

    for valve_id, start_time in valve_start_dict.items():  # extract data from the dict
        mask = df_copy['VALVE_ID'] == valve_id # filtering the df to data which shares valve
        df_copy.loc[mask, 'TIME_SINCE_APP[h]'] = df_copy.loc[mask, 'TIME_NORM_GLOBAL[h]'] - start_time # shifting the time-axis

    return df_copy

def remove_nan_rows(raw_df:pd.DataFrame) -> pd.DataFrame:
    # might delete this function and simply use dropna directly
    '''
    remove rows containing nan from a df - present due to valve error

    Input:
        raw_df: dataframe containing raw datapoints from all valves

    output:
        filtered df: df with nan-containing rows removed
    '''
    copy_df = raw_df.copy()  # Create a copy to avoid changing the raw DataFrame
    initial_rows = len(copy_df)
    
    filtered_df = copy_df.dropna(axis=0, how='any')  # Drop any rows containing NaN
    
    removed_rows = initial_rows - len(filtered_df)
    print(f'{removed_rows} of nan rows removed' )

    return filtered_df

def background_correction(filtered_df:pd.DataFrame, power:int = 2) -> pd.DataFrame:
    '''
    Finds bacground-corrected flux (F_BC) via inverse distance weiging of the 3 closest background-measurements, global time-scale

    Input: 
        filtered_df: dataframe contaning data from all valves
        power: int chosen power for the time-weighted average, 2 is typically used. Higer power-values ensures closer points are given higher weigths

    output: 
        datframe with a new collum FC for all actual treatments - background data removed 
    '''
    # extract background data from filtered df - remove background data from 
    df_copy = filtered_df.copy()

    # isolate treatment and background data
    background_df = df_copy[df_copy['TREATMENT'] == 'BACKGROUND'].copy()
    treatment_df = df_copy[df_copy['TREATMENT'] != 'BACKGROUND'].copy()

    background_df = background_df.sort_values(by='TIME_NORM_GLOBAL[h]') # Ensure background data is sorted by time (safety-line, this should already be the case)

    F_BC = [] # prepare object to store corrected flux-values within

    for idx, row in treatment_df.iterrows(): # looping over the dataframe-rows (vertically)
        current_time = row['TIME_NORM_GLOBAL[h]'] # extracting time-values of the current row

        # find the 3 closest backgrounds
        background_df['time_diff'] = np.abs(background_df['TIME_NORM_GLOBAL[h]'] - current_time) # determine background data time-distance for current row
        closest_background = background_df.nsmallest(3, 'time_diff') #nsmallest returns a df with the 3 closest background-times

        # determine weights (inverse distance weigting)
        distances = closest_background['time_diff'].to_numpy(dtype=float)
        weights = 1 / (distances ** power) 
        weights = weights / np.sum(weights)  # Normalize weights

        # Calculate the weighted average
        flux_values = closest_background['F[mg/h m2]'].to_numpy(dtype=float)
        weighted_avg = np.sum(weights * flux_values)

        # correct the treatment flux and add it to the results-list
        corrected_flux_value = row['F[mg/h m2]'] - weighted_avg
        F_BC.append(corrected_flux_value)


    # add the result-list as a new row
    treatment_df['F_BC'] = F_BC

    return treatment_df

def determine_smallest_timerange_valve(filtered_df: pd.DataFrame, pts_per_h = 2) -> np.ndarray:
    '''
    Determines a common time-interval for all valves for the downstream interpolation. Time of aplication used.
    1) Identifies the valve with the latest start
    2) Identifies the earliest end for all valves
    3) extracts time-stamps from the valve with the latest start
    4) filter the timestamps to be within the earliest end

    Input:
        BC_df: dataframe containing background-corrected datapoints of actual treatments
        pts_per_h: int, number of points to be interpolated per hour

    output:
        time-values of smallest timerange as a numpy-array, on the "time of aplication" axis.
         
    '''
    valves = filtered_df['VALVE_ID'].unique() # identify all unique valves

    start_times: dict[str, float] = {}
    end_times: dict[str, float] = {}

    for valve_id in valves: # extract start and end times
        valve_data = filtered_df[filtered_df['VALVE_ID'] == valve_id]
        start_times[valve_id] = valve_data['TIME_SINCE_APP[h]'].min()
        end_times[valve_id] = valve_data['TIME_SINCE_APP[h]'].max()

    # identify latest start and earliest end (shared time domian), and determine which valve contians the latest start
    latest_start_valve = max(start_times, key=start_times.get)  # type: ignore the dict always contains floats,
    earliest_end = min(end_times.values())
    latest_start_time = start_times[latest_start_valve]

    interp_step_size = 1 / pts_per_h # points per hour
    interp_times = np.arange(latest_start_time, earliest_end, interp_step_size)

    print(f"Time window: {latest_start_time:.3f} to {earliest_end:.3f}")

    return interp_times

def interpolation_linear(treatment_df: pd.DataFrame, shortest_time_range_values: np.ndarray) -> pd.DataFrame:
    # potentially create more points to better capture peaks? One flux-peak for a single valve is sligtly off 
    '''
    performs linear interpolation, on to the shortest time-range values to avoid extrapolation
    
    input:
        treatment df: df expexted to contain collums with background corrected flux-values and time normalized since aplication for all valves
        shortest_time_range_values

    output:
        interpolated df: df with interpolated fluxes (F_INTERP) with corresponding treatment-type, valve-id, global time, and time since aplication collums.
        The interpolated data should share time-stamps allowing easy downstream merging
    '''
    copy_df = treatment_df.copy()
    interpolated_dfs = []

    # identify all unique valves
    valve_ids = treatment_df['VALVE_ID'].unique()

    # extract relevant data from each valve
    for valve_id in valve_ids:
        # extracting valve data
        valve_df = copy_df[copy_df['VALVE_ID'] == valve_id]
        valve_df = valve_df.sort_values(by='TIME_SINCE_APP[h]')

        # extracting collums
        F_BC = valve_df['F_BC'].to_numpy()
        t_raw_app = valve_df['TIME_SINCE_APP[h]'].to_numpy()
        treatment = valve_df['TREATMENT'].iloc[0]
        
        # actual interpolation
        F_interp = np.interp(shortest_time_range_values, t_raw_app, F_BC)

        # recreate DATETIME and global time for interpolated values   
        experiment_start = pd.to_datetime(valve_df['DATE_TIME'].iloc[0]) - pd.to_timedelta(valve_df['TIME_NORM_GLOBAL[h]'].iloc[0], unit='h')
        datetime = experiment_start + pd.to_timedelta(shortest_time_range_values, unit='h')
        t_global = shortest_time_range_values + valve_df['TIME_NORM_GLOBAL[h]'].iloc[0]
     
        # Create a df for the interpolated values
        interp_df = pd.DataFrame({'VALVE_ID': valve_id,'TREATMENT': treatment,'TIME_SINCE_APP[h]': shortest_time_range_values,'F_INTERP': F_interp, 'DATE_TIME': datetime, 'TIME_NORM_GLOBAL[h]':t_global})

        interpolated_dfs.append(interp_df)

    # Combine all interpolated DataFrames
    interpolated_df = pd.concat(interpolated_dfs, ignore_index=True)

    return interpolated_df


def integration(interp_df: pd.DataFrame)-> pd.DataFrame:
    '''
    Performs trapezoidal integration on flux-values related to a single valve, providing accumulated emissions [mg/m2] 

    input:
        interp_df dataframe containing flux-values and a time-axis, expected names are F_INTERP and TIME_SINCE_APP

    output:
        copy of interp_df, now contaning additional collum for accumulated emissions
    '''
    copy_df = interp_df.copy()
    copy_df['ACUM_EMIS'] = 0.0 # accumulated emissions[mg/m2], initalizing new collum with 0's, notice as a float not an int
    
    for valve_id in copy_df['VALVE_ID'].unique():
        mask = copy_df['VALVE_ID'] == valve_id
        valve_data = copy_df.loc[mask].sort_values(by='TIME_SINCE_APP[h]')

        t = valve_data['TIME_SINCE_APP[h]'].to_numpy() # [h]
        F = valve_data['F_INTERP'].to_numpy() # [mg/m2 h]

        acum_emis = cumulative_trapezoid(F, t, initial = 0.0) # [mg / h m2] * [h] = [mg/ h], notice inital is a float not an int

        # storing integral-values
        copy_df.loc[valve_data.index, 'ACUM_EMIS'] = acum_emis

    return copy_df

def TAN_normalization(interp_df: pd.DataFrame, TAN_dict: dict) -> pd.DataFrame:
    '''
    normalizes flux-values [mg/ h m2] and accumulated emissions [mg/m2] against slurry applied TAN [mg/m2].
    Assumes background data has been removed.

    input: 
        interp_df: dataframe containing flux-values
        TAN_M2: dictionary containing treatments(str) as keys, and applied TAN(floats) as values

    output:
        interp_df with relative flux rates, %TAN [1 / h] and relative accumulated emissions added
        
    '''
    copy_df = interp_df.copy()
    copy_df['%REL_F'] = 0.0 # initalizing new collum with 0's
    copy_df['%REL_ACUM_EMIS'] = 0.0
    
    for treatment in copy_df['TREATMENT'].unique():
        TAN_value = TAN_dict[treatment] # extract tanvalue for the current treatment

        # Calculate the normalized flux for the current treatment
        mask = copy_df['TREATMENT'] == treatment
        copy_df.loc[mask, '%REL_F'] = (copy_df.loc[mask,'F_INTERP'] / TAN_value) * 100  # [mg/h m2] / [mg/m2] = [1/h]
        copy_df.loc[mask, '%REL_ACUM_EMIS'] = (copy_df.loc[mask,'ACUM_EMIS'] / TAN_value) * 100  # [mg/m2] / [mg/m2] = [-]
        

    return copy_df

def merge_triplicates(integrated_df: pd.DataFrame) -> pd.DataFrame:
    '''
    Merge triplicate-data, finding average values and the related std-deviation. After interpolation triplicate datapoints are assumed to have been alligned.

    input: 
        integrated_df: dataframe contaning data(actual and relative flux, actual and relative accumulated emissions) from all valves with a treatment tag, and shared time-values 

    output:
        merged_df: dataframe with same averaged parameters as integrated df, therefore smaller in therms of rows by a factor of 3
    '''
    df_copy = integrated_df.copy()
    grouped = df_copy.groupby(['TREATMENT', 'TIME_SINCE_APP[h]'])

    # initalyze return dataframe
    merged_df = pd.DataFrame()

    # Averaging emission data and finding variance
    merged_df['F_INTERP_MEAN'] = grouped['F_INTERP'].mean()
    merged_df['F_INTERP_STD'] = grouped['F_INTERP'].std()

    merged_df['ACUM_EMIS_MEAN'] = grouped['ACUM_EMIS'].mean()
    merged_df['ACUM_EMIS_STD'] = grouped['ACUM_EMIS'].std()

    merged_df['%REL_F_MEAN'] = grouped['%REL_F'].mean()
    merged_df['%REL_F_STD'] = grouped['%REL_F'].std()
    
    merged_df['%REL_ACUM_EMIS_MEAN'] = grouped['%REL_ACUM_EMIS'].mean()
    merged_df['%REL_ACUM_EMIS_STD'] = grouped['%REL_ACUM_EMIS'].std()

    # meta-data
    merged_df['DATE_TIME'] = grouped['DATE_TIME'].first()
    merged_df['TIME_NORM_GLOBAL[h]'] = grouped['TIME_NORM_GLOBAL[h]'].first()

    # reset such that treatment and TIME_SINCE_APP beceomes actual collums
    merged_df.reset_index(inplace=True)

    # print of final accumulated emissions
    treatments = merged_df['TREATMENT'].unique()
    for treatment in treatments:
        treatment_df = merged_df[merged_df['TREATMENT'] == treatment]
        final_emis = treatment_df['%REL_ACUM_EMIS_MEAN'].iloc[-1]
        final_emis_stdev = treatment_df['%REL_ACUM_EMIS_STD'].iloc[-1]
        print(f'final accumated relative emissions for treatment {treatment} is {round(final_emis, 2)} ± {round(final_emis_stdev, 2)} %, , coeficient of variation is {round((final_emis_stdev / final_emis) * 100, 2)}%')

    return merged_df

def save_df_as_csv(df : pd.DataFrame, output_folder: Path , output_file_name : str, overwrite: bool = True):
    '''
    saves a df as a csv-file in a designated outputfolder

    Input:
        df: the dataframe to be saved
        outputfolder(path object): the file-path of the output folder
        output_file_name(str): wanted name of the created file
        overwrite(BOOl): designate whether the function should overwrite an existing file with the same name

    output:
        a csv-file saved in the designated folder with the designated name.
    '''
    output_file = output_folder / f"{output_file_name}.csv"

    if output_file.exists() and not overwrite:
        print(f"The file with the following name already exist: {output_file.name}")
        return

    df.to_csv(output_file, index=False)
    print(f" output_file saved as: {output_file}")

##### Input folder and Files #####
input_path = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output-picarro\2-flux-conversion\2026-03-12-field-pig-flux-v32.csv")

##### Output folder and files #####
output_folder = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output-picarro\3-intergration")

##### Constants #####
treatment_valve_ids = [1, 2, 3, 4, 6, 7, 8, 10, 11, 12, 13, 14, 15, 17, 18]

Aplication_time_dict = {1 : 0.0 , 2 : 0.0 , 3 : 0.0, 4 : 0.40 , 5: 0.53, 6: 0.40 , 7: 0.40 , 8: 2.20, 9: 2.05,
 10: 2.35, 11: 2.48, 12: 2.62, 13: 2.75, 14: 2.88, 15: 3.02, 16: 3.15, 17: 3.28, 18: 3.42, 19: 3.55} 
# delta h since experimental start 
# no data "lost" for this experiment, aplication times manually corrected to first datapoint - 7.5 min (0.125 h)
# notice, for the order was valves are switched (backgr-times changed to fit lunch hours)


TAN_dict = {'AA' : 6228, 'RAW': 6249, 'H2SO4': 6115, 'OSI': 6215, 'TH': 6212} # [mg/m2] spec kit
#TAN_M2_stdev_dict = {'AA' : 143.2, 'RAW': 165.7, 'H2SO4': 95.3} # [mg/m2] # not currently used
treatments = ['AA','RAW','H2SO4', 'OSI', 'TH']

##### Script excecution #####
raw_df = load_csv_file_as_df(input_path) # load flux-data
#print(raw_df.head(50))

# dropping collums not needed for down-stream
raw_df_small = raw_df.drop(columns=['C[PPB]','C_STDEV[PPB]', 'P_DROP[pa]', 'P_ATMOS[hpa]', 'T[degc]']).copy() ; #print(raw_df_small)
#print(raw_df_small.head(26))

raw_df_new_time = time_normalization_application(raw_df_small, Aplication_time_dict)
#print(raw_df_new_time.head(50))
#print(raw_df_new_time.tail(50))

filtered_df = remove_nan_rows(raw_df_new_time)
#print(filtered_df)

pts_per_h = 2
times = determine_smallest_timerange_valve(filtered_df, pts_per_h = pts_per_h)
#print(times)
#print(len(times))
treatment_df = background_correction(filtered_df, power=2) 
#print(treatment_df)

interp_df = interpolation_linear(treatment_df, times)
#print(interp_df.head(50))

integrated_df = integration(interp_df)
#print(integrated_df)

TAN_df = TAN_normalization(integrated_df, TAN_dict)
#print(TAN_df)

merged_df = merge_triplicates(TAN_df)
#print(merged_df)

### Rename collums before saving as csv-files
# Treatment level
#renamed_df = merged_df.rename(columns={
#'F_INTERP_MEAN' : 'flux [mg/m2 h]',
#'F_INTERP_STD': 'flux_std_dev[mg/m2 h]',
#'%REL_F_MEAN': 'relative_flux',
#'%REL_F_STD': 'relative_flux_std_dev',
#'%REL_ACUM_EMIS_MEAN': '%_relative_accumulated_emissions',
#'%REL_ACUM_EMIS_STD' : '%_relative_accumulated_emisssions_std_dev',
#'ACUM_EMIS_MEAN':'accumulated_emission [mg/m2]',
#'ACUM_EMIS_STD': 'accumulated_emission_std_dev[mg/m2]',
#'TIME_SINCE_APP[h]': 'time_since_slurry_aplication[h]',
#'TIME_NORM_GLOBAL[h]': 'time_since_start_of_experiment'}) 
#print(renamed_df)

# valve level
renamed_df = TAN_df.rename(columns={
'TIME_SINCE_APP[h]': 'time_since_slurry_aplication[h]', 
'F_INTERP' : 'flux [mg/m2 h]',
'TIME_NORM_GLOBAL[h]': 'time_since_start_of_experiment',
'TIME_SINCE_APP[h]': 'time_since_slurry_aplication[h]',
'%REL_F': '%relative_flux',
'ACUM_EMIS':'accumulated_emission [mg/m2]',
'%REL_ACUM_EMIS': '%_relative_accumulated_emissions'
})
#print(renamed_df)


### Save data as csv ###
#save_df_as_csv(renamed_df, output_folder, '2026-03-16-field-pig-integrated-valve-lvl-v323', overwrite = True)

##### TEST and stats #####
### Relative reductions ###
for valve in TAN_df['VALVE_ID'].unique(): # extract final accumalted emission from each treatment:
    valve_df = TAN_df[TAN_df['VALVE_ID'] == valve]
    final_emis = valve_df['%REL_ACUM_EMIS'].iloc[-1]
    treatment = valve_df['TREATMENT'].iloc[0]
    print(f'final accumulated emission for valve {valve} is {round(final_emis, 3)} %, treatment is {treatment}')

##### Plot creation ##### 
Create_plots = False

if Create_plots == True:
    ##### Check of interpolation vs raw data for random valve #####
    interptest_valveid = random.choice(treatment_valve_ids)

    # extract raw data
    raw_valve_df =  treatment_df[treatment_df['VALVE_ID'] == interptest_valveid]
    t_raw = raw_valve_df['TIME_SINCE_APP[h]'].to_numpy()
    F = raw_valve_df['F_BC'].to_numpy()

    # extract interpolation data
    interp_valve_df = interp_df[interp_df['VALVE_ID'] == interptest_valveid]
    t_interp = interp_valve_df['TIME_SINCE_APP[h]'].to_numpy()
    F_interp = interp_valve_df['F_INTERP'].to_numpy()

    # modyfying plt
    plt.plot(t_raw, F, 'o-', label='Raw Data', color='blue')
    plt.plot(t_interp, F_interp, 'x-', label='Interpolated Data', color='red')
    plt.xlabel('Time Since Application [h]')
    plt.ylabel('Flux [mg/h m2]')
    plt.title(f'Raw vs. Interpolated Data for Valve {interptest_valveid}, interpolated points per hour was {pts_per_h}')
    plt.legend()
    plt.show()

    ##### Visual test of merging function #####
    mtest_treatment = random.choice(treatments)
    #mtest_treatment = 'TH'

    # extract treatment-relevant data, merged and original
    original_treatment_df = treatment_df[treatment_df['TREATMENT'] == mtest_treatment]
    
    merged_treatment_df = merged_df[merged_df['TREATMENT'] == mtest_treatment]
    merged_treatment_df = merged_treatment_df.sort_values(by='TIME_SINCE_APP[h]')

    for valve_id in original_treatment_df['VALVE_ID'].unique():
        valve_data = original_treatment_df[original_treatment_df['VALVE_ID'] == valve_id]
        F_valve = valve_data['F_BC']
        t_valve = valve_data['TIME_SINCE_APP[h]']
        plt.plot(t_valve, F_valve, 'o-', label=f'Valve {valve_id}', alpha=0.5)

    # Plot merged mean line
    F_merged = merged_treatment_df['F_INTERP_MEAN']
    F_merged_err = merged_treatment_df['F_INTERP_STD']
    t_merged = merged_treatment_df['TIME_SINCE_APP[h]']
    plt.plot(t_merged, F_merged, 'x-', label='Merged (Mean)', color='black', linewidth=2, markersize=6)

    # error as shading effect
    plt.fill_between(t_merged,F_merged - F_merged_err, F_merged + F_merged_err, color='gray', alpha=0.3, label='± Std Dev')

    plt.xlabel('Time Since Application [h]')
    plt.xlim(0, 24)
    plt.ylabel('Flux [mg/ m2 h]')
    #plt.ylim(0, 30)
    plt.title(f'Comparison of flux for Treatment {mtest_treatment}')
    plt.legend()
    plt.show()

    ##### Plot of relative flux for all merged treatments #####
    # rename treatments for plotting
    treatment_names = {'AA': 'Acetic acid','RAW': 'Unacidified slurry (hand applied)','H2SO4': 'H₂SO₄', 'TH': 'Trailing Hose', 'OSI': 'Open Slot Injection'}
    
    # determine unique treatments in merged df
    for treatment in merged_df['TREATMENT'].unique():
        treatment_df = merged_df[merged_df['TREATMENT'] == treatment]
        # extract relevant data
        t_treatment = treatment_df['TIME_SINCE_APP[h]']
        Rel_F = treatment_df['%REL_F_MEAN']
        Rel_F_stdev = treatment_df['%REL_F_STD']

        label = treatment_names.get(treatment, treatment)  # Fallback to original if not found
        plt.plot(t_treatment, Rel_F, '-', label=label, linewidth=2, markersize=6)
        plt.fill_between(t_treatment, Rel_F - Rel_F_stdev, Rel_F + Rel_F_stdev, alpha=0.3)

    # graph visuals
    plt.xlabel('Time Since Application [h]', fontsize=14, fontname='Times New Roman')
    #plt.xlim(0, 165)
    plt.ylabel('Relative flux (% of TAN) [h⁻¹]', fontsize=14, fontname='Times New Roman')
    plt.legend(fontsize=14, prop={'family': 'Times New Roman'},frameon=False)
    plt.show()


##### Code References #####
# https://www.geeksforgeeks.org/python/add-zero-columns-to-pandas-dataframe/ 
# https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.cumulative_trapezoid.html
# https://en.wikipedia.org/wiki/Trapezoidal_rule 
# https://www.geeksforgeeks.org/pandas/python-pandas-dataframe-groupby/
# https://www.geeksforgeeks.org/pandas/how-to-rename-columns-in-pandas-dataframe/ 



