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
    copy_df = raw_df.copy() # creating a copy to avid changing raw df
    filtered_df = copy_df.dropna(axis = 0, how = 'any') # dropping any rows contaning nan
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
    3) creates new time-stamps within the common timerange with the specified resulution

    Input:
        BC_df: dataframe containing background-corrected datapoints of actual treatments

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

def prepare_TAN_dict(slurry_application_dict: dict, TAN_concentration_dict: dict, data_df: pd.DataFrame) -> dict:
    '''
    Determines valve-level TAN-amount [mg/m2]. Assumes slurry density is similar to water.

    input:
        slurry_application_dict: valves(int) as keys, slurry volumes [mL] as items
        TAN_concentration_dict: treatments(str) as keys, concentrations [g/L] as items
        data_df: dataframe containing all treatments and valves used

    output: dictionary with valves as keys and TAN-amounts [mg/m2] as values
    '''
    # Function specific constants:
    A = 28.27 * 10**(-4)  # [cm2] to [m2] total soil surface

    copy_df = data_df.copy()
    tan_dict = {}
    valves = copy_df['VALVE_ID'].unique()

    for valve in valves:
        valve_data = copy_df[copy_df['VALVE_ID'] == valve]
        treatment = valve_data['TREATMENT'].iloc[0]  # Grab treatment tag from first row

        slurry_app = slurry_application_dict[valve]  # [mL]
        slurry_app = slurry_app * 10**(-3)  # [mL] to [L]
        slurry_app = slurry_app / A  # [L/m2]

        TAN_C = TAN_concentration_dict[treatment]  # [g/L]
        TAN_C = TAN_C * 10**3  # [g/L] to [mg/L]

        TAN_m2 = slurry_app * TAN_C  # [L/m2] * [mg/L] = [mg/m2]
        tan_dict[valve] = TAN_m2

    return tan_dict

def TAN_normalization(interp_df: pd.DataFrame, TAN_dict: dict) -> pd.DataFrame:
    '''
    Normalizes flux-values [mg/h m2] and accumulated emissions [mg/m2] against slurry applied TAN [mg/m2] per valve.
    Assumes background data has been removed.

    input:
        interp_df: dataframe containing flux-values and a 'VALVE_ID' column
        TAN_dict: dictionary containing valve IDs (int) as keys, and applied TAN (float) as values

    output:
        interp_df with relative flux rates, %TAN [1/h] and relative accumulated emissions added
    '''
    copy_df = interp_df.copy()
    copy_df['%REL_F'] = 0.0  # Initialize new columns with 0's
    copy_df['%REL_ACUM_EMIS'] = 0.0

    for valve in copy_df['VALVE_ID'].unique():
        TAN_value = TAN_dict[valve]  # Extract TAN value for the current valve from the dict

        # Calculate the normalized flux for the current valve
        mask = copy_df['VALVE_ID'] == valve
        copy_df.loc[mask, '%REL_F'] = (copy_df.loc[mask, 'F_INTERP'] / TAN_value) * 100  # [mg/h m2] / [mg/m2] = [1/h]
        copy_df.loc[mask, '%REL_ACUM_EMIS'] = (copy_df.loc[mask, 'ACUM_EMIS'] / TAN_value) * 100  # [mg/m2] / [mg/m2] = [-]

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
        print(f'final accumated relative emissions for treatment {treatment} is {round(final_emis, 2)} ± {round(final_emis_stdev, 2)} %, coeficient of variation is {round((final_emis_stdev / final_emis) * 100, 2)}%')

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
input_path = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output\2-flux-conversion\2026-05-06-lab-CattleRetrail-flux-v32.csv")

##### Output folder and files #####
output_folder = Path(r"C:\Users\mikae\Desktop\Github - speciale\Larsen-2025-Masterthesis-DFCs\output\3-intergration")

##### Figures #####
output_folder_figures = Path(r"C:\Users\mikae\OneDrive - Aarhus universitet\10 semester - Speciale\Report Graphs")
output_name_figure = Path("graph-2026-06-05Lab-cattle-PackedSoil-24hflux.png")
output_path_figures = output_folder_figures / output_name_figure

##### Constants #####
#ttreatment_method_dict = {1: 'FAA', 2: 'STD', 3: 'FH2SO4', 4: 'PH2SO4', 5: 'PRAW', 11: 'BACKGROUND',
#6: 'PAA', 7: 'FRAW', 8: 'FH2SO4', 9: 'STD', 10: 'FAA', 12: 'BACKGROUND',
#17: 'PRAW', 18: 'FRAW', 19: 'PAA', 20: 'PH2SO4', 21: 'PRAW', 27: 'BACKGROUND',
#22: 'PAA', 23: 'PH2SO4', 24: 'FH2SO4', 25: 'FAA', 26: 'FRAW', 28: 'BACKGROUND'}

Aplication_time_dict = {1: 0.0, 2: 0.25, 3: 0.5, 4: 0.75, 5: 1.0, 11: 1.75,
6: 1.75, 7: 2.0, 8: 2.25, 9: 2.75, 10: 3.0, 12: 3.50,
17: 3.5, 18: 3.75, 19: 4.0, 20: 4.25, 21: 4.5, 27: 5.25,
22: 5.25, 23: 5.5, 24: 5.75, 25: 6, 26: 6.25, 28: 7.00} # [delta h], backgrounds corrected such that they are simply set to 0

slurry_aplication_dict = {1: 2.031, 2: 2.006, 3: 2.050, 4: 2.076, 5: 2.033,
6: 2.025, 7: 2.018, 8: 2.072, 9: 2.037, 10: 2.072,
17: 2.013, 18: 2.031, 19: 2.021, 20: 2.038, 21: 2.107,
22: 2.065, 23: 2.031, 24: 2.013, 25: 2.076, 26: 2.102} # amount of slurry applied to each sample in [g] or [mL] (assuming simillar density as water)

treatment_TAN_conentration = {
'FH2SO4' : 2.05, 'PH2SO4' : 2.05,
'FAA': 2.05, 'PAA': 2.05,
'FRAW': 1.89, 'PRAW' : 1.89,
'STD': 3.57} 
# concentration [g/L] of NH4-N (TAN) in the sample  


treatments = ['FAA', 'PAA','FH2SO4', 'PH2SO4', 'FRAW', 'PRAW', 'STD'] # Name of all treatments, only used for visuals
treatment_valve_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 17, 18, 19, 20, 21, 22, 23, 24, 26] # Bkgs exclulded, only used for visualsTD

##### Script excecution #####
raw_df = load_csv_file_as_df(input_path) # load flux-data
#print('inital data \n', raw_df.head(50))
#print(raw_df.tail(50))

# dropping collums not needed for down-stream
raw_df_small = raw_df.drop(columns=['C[PPB]','C_STDEV[PPB]','Q[L/min]']).copy()
#print('collums dropped \n', raw_df_small)

raw_df_new_time = time_normalization_application(raw_df_small, Aplication_time_dict)
#print('time normalized  agianst application time \n', raw_df_new_time.head(30))

filtered_df = remove_nan_rows(raw_df_new_time)
#print('rows with missing data removed \n', filtered_df)

times = determine_smallest_timerange_valve(filtered_df, pts_per_h = 2)
#print(len(times))

treatment_df = background_correction(filtered_df, power=3) 
#print('background corrected data \n', treatment_df.head(50))

interp_df = interpolation_linear(treatment_df, times)
#print('interpolated data', interp_df)

integrated_df = integration(interp_df)

#print('intergrated_data \n', integrated_df)

TAN_dict = prepare_TAN_dict(slurry_aplication_dict, treatment_TAN_conentration, integrated_df)
#print(TAN_dict)
TAN_df = TAN_normalization(integrated_df, TAN_dict)
#print('data normalized agianst slurry TAN \n', TAN_df)

merged_df = merge_triplicates(TAN_df)
#print('triplicates averaged \n', merged_df)

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
renamed_df = TAN_df.rename(columns={'TIME_SINCE_APP[h]': 'time_since_slurry_aplication[h]', 
'F_INTERP' : 'flux [mg/m2 h]',
'TIME_NORM_GLOBAL[h]': 'time_since_start_of_experiment',
'TIME_SINCE_APP[h]': 'time_since_slurry_aplication[h]',
'%REL_F': '%relative_flux',
'ACUM_EMIS':'accumulated_emission [mg/m2]',
'%REL_ACUM_EMIS': '%_relative_accumulated_emissions'})
print(renamed_df)

#save_df_as_csv(renamed_df, output_folder, '2026-06-05-lab-cattleRetrail-integrated-replicate_lvl', overwrite = True)

##### Tests and stats #####
### Data for relative differences ####
for valve in TAN_df['VALVE_ID'].unique(): # extract final accumalted emission from each treatment:
    valve_df = TAN_df[TAN_df['VALVE_ID'] == valve]
    final_emis = valve_df['%REL_ACUM_EMIS'].iloc[-1]
    treatment = valve_df['TREATMENT'].iloc[0]
    print(f'final accumulated emission for valve {valve} is {round(final_emis, 3)} %, treatment is {treatment}')


##### Plot creation ##### 
Create_plots = False


# global figure size and DPI
FIGSIZE = (6, 4)
DPI = 300

# fonts-types and size and tick control, needs to be defined before all plots
plt.rcParams.update({
    'font.family': 'Times New Roman',
    'font.size': 16,
    'axes.labelsize': 16,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'ytick.direction': 'in',
    'xtick.direction': 'in',
    'axes.linewidth': 1})


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
    plt.title(f'Raw vs. Interpolated Data for Valve {interptest_valveid}')
    plt.legend()
    plt.show()

    ##### Visual test of merging function #####
    mtest_treatment = random.choice(treatments)
    #mtest_treatment = 'STD'

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
    treatment_names = {
    'FAA': 'AA', 'PAA': 'AA',
    'FRAW': 'None', 'PRAW': 'None',
    'FH2SO4': 'SA', 'PH2SO4': 'SA'
    }

    treatment_colors = {
    'FAA': 'blue', 'PAA' : 'blue',
    'FRAW': 'darkorange', 'PRAW' : 'darkorange', 
    'FH2SO4': 'darkgreen', 'PH2SO4': 'darkgreen'}

    # filter to only packed or 
    group_prefix = 'P' # F or P
    plot_df = merged_df[merged_df['TREATMENT'].str.startswith(group_prefix)]

    # determine unique treatments in merged df
    for treatment in plot_df['TREATMENT'].unique():
        treatment_df = plot_df[plot_df['TREATMENT'] == treatment]
        color = treatment_colors.get(treatment, 'gray')  # Default to gray if treatment not in mapping
        
        # extract relevant data
        t_treatment = treatment_df['TIME_SINCE_APP[h]']
        Rel_F = treatment_df['%REL_F_MEAN']
        Rel_F_stdev = treatment_df['%REL_F_STD']

        label = treatment_names.get(treatment, treatment)  # Fallback to original if not found
        plt.plot(t_treatment, Rel_F, '-', label=label, linewidth=2, color = color)
        plt.fill_between(t_treatment, Rel_F - Rel_F_stdev, Rel_F + Rel_F_stdev, color = color, alpha=0.3)

    if group_prefix == 'P': # ammonium carbonate std needs to be plotted together with these
        STD_df = TAN_df[TAN_df['TREATMENT'] == 'STD']
            
        for i, valve_id in enumerate(STD_df['VALVE_ID'].unique()):
            valve_df = STD_df[STD_df['VALVE_ID'] == valve_id]
            t_valve = valve_df['TIME_SINCE_APP[h]']
            Rel_F = valve_df['%REL_F']
                
            if i == 0:
                plt.plot(t_valve, Rel_F, linestyle = 'dashed', label= 'AC std', linewidth=1.5, color = 'black')
            else:
                plt.plot(t_valve, Rel_F, linestyle = 'dashed', linewidth=1.5, color = 'black')
      

    # graph visuals
    plt.xlabel('Time Since Application [h]')
    plt.xlim(0, 24)
    plt.ylabel('Relative flux (% of TAN) [h⁻¹]')
    plt.ylim(-0.05 , 4.5)
    plt.legend(frameon=False)
    #plt.savefig(output_path_figures, dpi=300, bbox_inches='tight')
    plt.show()

##### Code References #####
# https://www.geeksforgeeks.org/python/add-zero-columns-to-pandas-dataframe/ 
# https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.cumulative_trapezoid.html
# https://en.wikipedia.org/wiki/Trapezoidal_rule 
# https://www.geeksforgeeks.org/pandas/python-pandas-dataframe-groupby/
# https://www.geeksforgeeks.org/pandas/how-to-rename-columns-in-pandas-dataframe/ 



